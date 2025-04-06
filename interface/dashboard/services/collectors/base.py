"""
Base collector class for data sources.

This module defines the base collector interface that all data source collectors must implement.
"""

import abc
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..data_sources import DataSource, DataSourceConfig, DataSourceActivity

logger = logging.getLogger(__name__)

class BaseCollector(abc.ABC):
    """Base class for data source collectors."""
    
    def __init__(self, source_id: str, config: DataSourceConfig):
        """Initialize the collector.
        
        Args:
            source_id: Unique identifier for the data source
            config: Configuration for the data source
        """
        self.source_id = source_id
        self.config = config
        self.data_dir = self._get_data_dir()
        
        # Ensure data directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs("/alerts", exist_ok=True)
        
    def _get_data_dir(self) -> str:
        """Get the data directory for this collector."""
        return os.path.join("data", self.source_id)
        
    def _save_document(self, document: Dict[str, Any]) -> bool:
        """Save a document to storage.
        
        Args:
            document: Document data to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Add metadata
            document["collected_at"] = datetime.now().isoformat()
            document["source_id"] = self.source_id
            
            # Generate document ID if not present
            if "document_id" not in document:
                document["document_id"] = f"{self.source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            # Save document
            filepath = os.path.join(self.data_dir, f"{document['document_id']}.json")
            with open(filepath, "w") as f:
                json.dump(document, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False
            
    def _save_alert(self, alert: Dict[str, Any]) -> bool:
        """Save an alert to storage.
        
        Args:
            alert: Alert data to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Add metadata
            alert["created_at"] = datetime.now().isoformat()
            alert["source_id"] = self.source_id
            
            # Generate alert ID if not present
            if "alert_id" not in alert:
                alert["alert_id"] = f"alert_{self.source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            # Save alert
            filepath = os.path.join("/alerts", f"{alert['alert_id']}.json")
            with open(filepath, "w") as f:
                json.dump(alert, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            return False
            
    @abc.abstractmethod
    async def collect(self) -> bool:
        """Collect documents from the data source.
        
        Returns:
            bool: True if collection was successful
        """
        pass
        
    @abc.abstractmethod
    async def validate_config(self) -> List[str]:
        """Validate the collector configuration.
        
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        pass
        
    @abc.abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the data source.
        
        Returns:
            bool: True if connection is successful
        """
        pass 