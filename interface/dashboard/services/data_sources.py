"""
Data source management services for the Sentinel dashboard.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from pydantic import BaseModel
from config import STORAGE_ROOT

logger = logging.getLogger(__name__)

class DataSourceConfig(BaseModel):
    """Model for data source configuration."""
    update_frequency: int
    max_days_back: int
    document_types: List[str]
    rate_limit: int
    custom_fields: Optional[Dict[str, Any]] = None

class DataSourceActivity(BaseModel):
    """Model for data source activity log entry."""
    level: str
    timestamp: str
    message: str

class DataSource(BaseModel):
    """Model for data source details."""
    name: str
    status: str
    status_class: str
    auth_type: str
    auth_class: str
    last_update: str
    documents: int
    update_frequency: str
    health_score: int
    total_documents: Optional[int] = None
    new_documents: Optional[int] = None
    collection_rate: Optional[int] = None
    success_rate: Optional[float] = None
    api_usage: Optional[int] = None
    config: Optional[DataSourceConfig] = None
    recent_activity: Optional[List[DataSourceActivity]] = None

class DataSourceService:
    """Service for managing data sources."""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(STORAGE_ROOT, "sources")
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
        
    def _get_source_file(self, source_id: str) -> str:
        """Get the path to a source's data file."""
        return os.path.join(self.data_dir, f"{source_id}.json")
        
    def get_all_sources(self) -> Dict[str, DataSource]:
        """Get all configured data sources."""
        sources = {}
        try:
            # First try to load from data files
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    source_id = filename[:-5]  # Remove .json
                    source = self.get_source(source_id)
                    if source:
                        sources[source_id] = source
                        
            # If no sources found, return default sources
            if not sources:
                sources = self._get_default_sources()
                
        except FileNotFoundError:
            # Return default sources if data directory doesn't exist
            sources = self._get_default_sources()
            
        except Exception as e:
            logger.error(f"Error loading data sources: {e}")
            sources = self._get_default_sources()
            
        return sources
    
    def get_source(self, source_id: str) -> Optional[DataSource]:
        """Get details for a specific data source."""
        try:
            # Try to load from data file
            source_file = self._get_source_file(source_id)
            if os.path.exists(source_file):
                with open(source_file, 'r') as f:
                    data = json.load(f)
                    return DataSource(**data)
            
            # If no file exists, check default sources
            default_sources = self._get_default_sources()
            if source_id in default_sources:
                return default_sources[source_id]
                
            return None
            
        except Exception as e:
            logger.error(f"Error loading data source {source_id}: {e}")
            return None
    
    def update_source(self, source_id: str, source: DataSource) -> bool:
        """Update a data source's configuration."""
        try:
            source_file = self._get_source_file(source_id)
            with open(source_file, 'w') as f:
                json.dump(source.dict(), f, indent=2)
            return True
            
        except Exception as e:
            logger.error(f"Error updating data source {source_id}: {e}")
            return False
    
    def delete_source(self, source_id: str) -> bool:
        """Delete a data source configuration."""
        try:
            source_file = self._get_source_file(source_id)
            if os.path.exists(source_file):
                os.remove(source_file)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting data source {source_id}: {e}")
            return False
    
    def add_activity(self, source_id: str, level: str, message: str) -> bool:
        """Add an activity log entry for a data source."""
        try:
            source = self.get_source(source_id)
            if not source:
                return False
                
            # Create new activity entry
            activity = DataSourceActivity(
                level=level,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                message=message
            )
            
            # Add to recent activity list
            if not source.recent_activity:
                source.recent_activity = []
            source.recent_activity.append(activity)
            
            # Keep only last 100 entries
            source.recent_activity = source.recent_activity[-100:]
            
            # Save updated source
            return self.update_source(source_id, source)
            
        except Exception as e:
            logger.error(f"Error adding activity for data source {source_id}: {e}")
            return False
    
    def _get_default_sources(self) -> Dict[str, DataSource]:
        """Get default data source configurations."""
        return {
            'federal_register': DataSource(
                name='Federal Register',
                status='Active',
                status_class='success',
                auth_type='API Key',
                auth_class='info',
                last_update='10 minutes ago',
                documents=15243,
                update_frequency='1 hour',
                health_score=98
            ),
            'congress': DataSource(
                name='Congress.gov',
                status='Active',
                status_class='success', 
                auth_type='Public',
                auth_class='secondary',
                last_update='25 minutes ago',
                documents=8765,
                update_frequency='2 hours',
                health_score=95
            ),
            'pacer': DataSource(
                name='PACER',
                status='Active',
                status_class='success',
                auth_type='Login',
                auth_class='warning',
                last_update='1 hour ago', 
                documents=25431,
                update_frequency='6 hours',
                health_score=92
            ),
            'state_legislature': DataSource(
                name='State Legislatures',
                status='Beta',
                status_class='warning',
                auth_type='Mixed',
                auth_class='info',
                last_update='45 minutes ago',
                documents=12543,
                update_frequency='12 hours',
                health_score=85
            )
        } 