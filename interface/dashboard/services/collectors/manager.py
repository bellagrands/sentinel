"""
Collector manager service.

This module provides a service for managing and running data source collectors.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Type

from .base import BaseCollector
from .federal_register import FederalRegisterCollector
from .congress import CongressCollector
from .pacer import PACERCollector
from ..data_sources import DataSourceService, DataSource, DataSourceActivity

logger = logging.getLogger(__name__)

class CollectorManager:
    """Service for managing data source collectors."""
    
    # Map source types to collector classes
    COLLECTORS: Dict[str, Type[BaseCollector]] = {
        "federal_register": FederalRegisterCollector,
        "congress": CongressCollector,
        "pacer": PACERCollector,
        # Add other collectors as they are implemented
    }
    
    def __init__(self):
        """Initialize the collector manager."""
        self.data_source_service = DataSourceService()
        self.running_collectors: Dict[str, asyncio.Task] = {}
        
    async def start_collector(self, source_id: str) -> bool:
        """Start a collector for a data source.
        
        Args:
            source_id: ID of the data source to collect from
            
        Returns:
            bool: True if collector was started successfully
        """
        try:
            # Get data source
            source = self.data_source_service.get_source(source_id)
            if not source:
                logger.error(f"Data source {source_id} not found")
                return False
                
            # Check if collector is already running
            if source_id in self.running_collectors:
                logger.warning(f"Collector for {source_id} is already running")
                return False
                
            # Get collector class
            collector_class = self.COLLECTORS.get(source_id)
            if not collector_class:
                logger.error(f"No collector implemented for {source_id}")
                return False
                
            # Create collector instance
            collector = collector_class(source_id, source.config)
            
            # Validate configuration
            errors = await collector.validate_config()
            if errors:
                logger.error(f"Invalid configuration for {source_id}: {errors}")
                await self._update_source_status(source_id, "Error", f"Invalid configuration: {', '.join(errors)}")
                return False
                
            # Test connection
            if not await collector.test_connection():
                logger.error(f"Connection test failed for {source_id}")
                await self._update_source_status(source_id, "Error", "Connection test failed")
                return False
                
            # Start collection task
            task = asyncio.create_task(self._run_collector(collector))
            self.running_collectors[source_id] = task
            
            # Update source status
            await self._update_source_status(source_id, "Active", "Collection started")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting collector for {source_id}: {e}")
            await self._update_source_status(source_id, "Error", f"Failed to start: {str(e)}")
            return False
            
    async def stop_collector(self, source_id: str) -> bool:
        """Stop a running collector.
        
        Args:
            source_id: ID of the data source to stop collecting from
            
        Returns:
            bool: True if collector was stopped successfully
        """
        try:
            if source_id not in self.running_collectors:
                logger.warning(f"No running collector found for {source_id}")
                return False
                
            # Cancel the collection task
            task = self.running_collectors[source_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
                
            del self.running_collectors[source_id]
            
            # Update source status
            await self._update_source_status(source_id, "Inactive", "Collection stopped")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping collector for {source_id}: {e}")
            return False
            
    async def _run_collector(self, collector: BaseCollector):
        """Run a collector continuously.
        
        Args:
            collector: Collector instance to run
        """
        source_id = collector.source_id
        
        try:
            while True:
                # Run collection
                success = await collector.collect()
                
                if success:
                    await self._update_source_status(
                        source_id,
                        "Active",
                        f"Collection completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    await self._update_source_status(
                        source_id,
                        "Error",
                        f"Collection failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                
                # Wait for next collection interval
                await asyncio.sleep(collector.config.update_frequency * 3600)  # Convert hours to seconds
                
        except asyncio.CancelledError:
            logger.info(f"Collector for {source_id} was cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Error in collector for {source_id}: {e}")
            await self._update_source_status(source_id, "Error", f"Collector error: {str(e)}")
            
    async def _update_source_status(self, source_id: str, status: str, message: str):
        """Update a data source's status and add an activity log entry.
        
        Args:
            source_id: ID of the data source to update
            status: New status
            message: Activity message
        """
        try:
            # Get current source
            source = self.data_source_service.get_source(source_id)
            if not source:
                return
                
            # Update status
            source.status = status
            source.status_class = {
                "Active": "success",
                "Inactive": "secondary",
                "Error": "danger"
            }.get(status, "warning")
            
            # Add activity
            level = "error" if status == "Error" else "info"
            self.data_source_service.add_activity(source_id, level, message)
            
            # Save changes
            self.data_source_service.update_source(source_id, source)
            
        except Exception as e:
            logger.error(f"Error updating source status for {source_id}: {e}")
            
    def get_collector_status(self, source_id: str) -> str:
        """Get the status of a collector.
        
        Args:
            source_id: ID of the data source
            
        Returns:
            str: Status of the collector (Running/Stopped)
        """
        return "Running" if source_id in self.running_collectors else "Stopped" 