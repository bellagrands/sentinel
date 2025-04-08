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
from database.db import db
from database.models import Document, CollectionStatus, SourceConfig

logger = logging.getLogger(__name__)

class BaseCollector(abc.ABC):
    """Base class for data source collectors."""
    
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.storage_dir = f"storage/documents/{source_id}"
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Get source configuration
        self.source_config = SourceConfig.query.filter_by(source_id=source_id).first()
        if not self.source_config:
            raise ValueError(f"No configuration found for source {source_id}")
            
        # Create collection status
        self.collection_status = CollectionStatus(
            source_id=source_id,
            status='running',
            collection_metadata={'start_time': datetime.utcnow().isoformat()}
        )
        db.session.add(self.collection_status)
        db.session.commit()
    
    @abc.abstractmethod
    def collect(self) -> bool:
        """Collect documents from the source.
        
        Returns:
            bool: True if collection was successful
        """
        pass
    
    def _save_document(self, document: Dict[str, Any]) -> Optional[Document]:
        """Save a document to storage and database.
        
        Args:
            document: Document data to save
            
        Returns:
            Document: Created document model if successful, None otherwise
        """
        try:
            # Generate document ID if not present
            if "document_id" not in document:
                document["document_id"] = f"{self.source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            # Save raw file
            raw_path = os.path.join(self.storage_dir, f"{document['document_id']}.json")
            with open(raw_path, "w") as f:
                json.dump(document, f, indent=2)
                
            # Create document model
            doc_model = Document(
                document_id=document["document_id"],
                title=document.get("title", "Untitled"),
                content=document.get("content", ""),
                source_type=self.source_id,
                url=document.get("url"),
                doc_metadata=document.get("metadata", {})
            )
            
            db.session.add(doc_model)
            db.session.commit()
            
            return doc_model
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return None
    
    def complete_collection(self, documents_collected: int):
        """Mark collection as completed."""
        try:
            self.collection_status.complete(documents_collected)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error completing collection: {e}")
    
    def fail_collection(self, error_message: str):
        """Mark collection as failed."""
        try:
            self.collection_status.fail(error_message)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error marking collection as failed: {e}")
        
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