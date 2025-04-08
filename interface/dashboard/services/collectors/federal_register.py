"""
Federal Register data collector.

This module implements document collection from the Federal Register API.
"""

import logging
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, List

from .base import BaseCollector
from ..data_sources import DataSourceConfig

logger = logging.getLogger(__name__)

class FederalRegisterCollector(BaseCollector):
    """Collector for Federal Register documents."""
    
    def __init__(self):
        super().__init__('federal_register')
        self.base_url = "https://www.federalregister.gov/api/v1"
        
    def collect(self) -> bool:
        """Collect documents from Federal Register API."""
        try:
            # Get configuration
            days_back = self.source_config.config.get('days_back', 7)
            keywords = self.source_config.config.get('keywords', [])
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Build search parameters
            params = {
                'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
                'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d'),
                'per_page': 100,
                'order': 'newest'
            }
            
            # Add keyword filters if specified
            if keywords:
                params['conditions[term]'] = ' OR '.join(keywords)
            
            # Make API request
            response = requests.get(f"{self.base_url}/documents", params=params)
            response.raise_for_status()
            
            # Process results
            results = response.json()
            documents = results.get('results', [])
            
            # Save documents
            saved_count = 0
            for doc in documents:
                processed_doc = self._process_document(doc)
                if self._save_document(processed_doc):
                    saved_count += 1
            
            # Mark collection as complete
            self.complete_collection(saved_count)
            logger.info(f"Collected {saved_count} documents from Federal Register")
            
            return True
            
        except Exception as e:
            error_msg = f"Error collecting from Federal Register: {str(e)}"
            logger.error(error_msg)
            self.fail_collection(error_msg)
            return False
    
    def _process_document(self, raw_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a raw Federal Register document.
        
        Args:
            raw_doc: Raw document from the API
            
        Returns:
            Dict[str, Any]: Processed document
        """
        return {
            'document_id': f"fr_{raw_doc['document_number']}",
            'title': raw_doc['title'],
            'content': raw_doc.get('abstract', '') + '\n\n' + raw_doc.get('body_html', ''),
            'url': raw_doc['html_url'],
            'metadata': {
                'document_number': raw_doc['document_number'],
                'publication_date': raw_doc['publication_date'],
                'document_type': raw_doc['type'],
                'agencies': [a['name'] for a in raw_doc.get('agencies', [])],
                'topics': raw_doc.get('topics', []),
                'citation': raw_doc.get('citation', ''),
                'page_length': raw_doc.get('page_length'),
                'signing_date': raw_doc.get('signing_date'),
                'presidential_document_type': raw_doc.get('presidential_document_type'),
                'executive_order_number': raw_doc.get('executive_order_number')
            }
        }

    async def validate_config(self) -> List[str]:
        """Validate the collector configuration."""
        errors = []
        
        if not self.source_config.config.get('days_back') or self.source_config.config['days_back'] < 1:
            errors.append("Max days back must be at least 1")
            
        if not self.source_config.config.get('keywords'):
            errors.append("At least one keyword must be specified")
            
        return errors
        
    async def test_connection(self) -> bool:
        """Test the connection to the Federal Register API."""
        try:
            # Try to fetch a single document to test connection
            response = requests.get(f"{self.base_url}/documents", params={"per_page": 1})
            response.raise_for_status()
            return True
                    
        except Exception as e:
            logger.error(f"Error testing Federal Register connection: {e}")
            return False
            
    async def collect(self) -> bool:
        """Collect documents from the Federal Register."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.source_config.config['days_back'])
            
            # Build search parameters
            params = {
                'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
                'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d'),
                'per_page': 100,
                'order': 'newest'
            }
            
            # Add keyword filters if specified
            if self.source_config.config.get('keywords'):
                params['conditions[term]'] = ' OR '.join(self.source_config.config['keywords'])
            
            # Make API request
            response = requests.get(f"{self.base_url}/documents", params=params)
            response.raise_for_status()
            
            # Process results
            results = response.json()
            documents = results.get('results', [])
            
            # Save documents
            saved_count = 0
            for doc in documents:
                processed_doc = self._process_document(doc)
                if self._save_document(processed_doc):
                    saved_count += 1
            
            # Mark collection as complete
            self.complete_collection(saved_count)
            logger.info(f"Collected {saved_count} documents from Federal Register")
            
            return True
            
        except Exception as e:
            error_msg = f"Error collecting from Federal Register: {str(e)}"
            logger.error(error_msg)
            self.fail_collection(error_msg)
            return False 