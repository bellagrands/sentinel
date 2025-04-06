"""
Congress.gov data collector.

This module implements document collection from the Congress.gov API.
"""

import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .base import BaseCollector
from ..data_sources import DataSourceConfig

logger = logging.getLogger(__name__)

class CongressCollector(BaseCollector):
    """Collector for Congress.gov documents."""
    
    BASE_URL = "https://api.congress.gov/v3"
    
    def __init__(self, source_id: str, config: DataSourceConfig):
        """Initialize the collector."""
        super().__init__(source_id, config)
        
        # Set up API configuration
        self.api_key = config.custom_fields.get("api_key")
        self.rate_limit = config.rate_limit
        self.max_days_back = config.max_days_back
        
    async def validate_config(self) -> List[str]:
        """Validate the collector configuration."""
        errors = []
        
        if not self.api_key:
            errors.append("API key is required")
            
        if not self.rate_limit or self.rate_limit < 1:
            errors.append("Rate limit must be at least 1 request per minute")
            
        if not self.max_days_back or self.max_days_back < 1:
            errors.append("Max days back must be at least 1")
            
        if not self.config.document_types:
            errors.append("At least one document type must be specified")
            
        return errors
        
    async def test_connection(self) -> bool:
        """Test the connection to the Congress.gov API."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to fetch a single bill to test connection
                url = f"{self.BASE_URL}/bill"
                params = {
                    "api_key": self.api_key,
                    "limit": 1,
                    "format": "json"
                }
                
                async with session.get(url, params=params) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error testing Congress.gov connection: {e}")
            return False
            
    async def collect(self) -> bool:
        """Collect documents from Congress.gov."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.max_days_back)
            
            async with aiohttp.ClientSession() as session:
                total_saved = 0
                
                # Collect each document type
                for doc_type in self.config.document_types:
                    # Get endpoint for document type
                    endpoint = self._get_endpoint(doc_type)
                    if not endpoint:
                        continue
                        
                    # Fetch documents page by page
                    offset = 0
                    while True:
                        # Build request parameters
                        params = {
                            "api_key": self.api_key,
                            "format": "json",
                            "limit": 20,
                            "offset": offset,
                            "fromDateTime": start_date.strftime("%Y-%m-%d"),
                            "toDateTime": end_date.strftime("%Y-%m-%d")
                        }
                        
                        # Make request
                        url = f"{self.BASE_URL}/{endpoint}"
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                logger.error(f"Error fetching Congress.gov {doc_type}: {response.status}")
                                continue
                                
                            data = await response.json()
                            
                            # Process documents
                            for doc in data.get("bills", []):  # Field name varies by type
                                # Convert to our document format
                                document = await self._process_document(doc, doc_type)
                                
                                # Save document
                                if document and self._save_document(document):
                                    total_saved += 1
                                    
                                    # Generate alert if needed
                                    if self._should_generate_alert(document):
                                        alert = self._create_alert(document)
                                        self._save_alert(alert)
                            
                            # Check if we have more pages
                            if len(data.get("bills", [])) < 20:  # Field name varies by type
                                break
                                
                            offset += 20
                
                logger.info(f"Collected {total_saved} documents from Congress.gov")
                return True
                
        except Exception as e:
            logger.error(f"Error collecting Congress.gov documents: {e}")
            return False
            
    def _get_endpoint(self, doc_type: str) -> Optional[str]:
        """Get API endpoint for document type."""
        endpoints = {
            "BILL": "bill",
            "RESOLUTION": "resolution",
            "AMENDMENT": "amendment",
            "HEARING": "hearing",
            "REPORT": "report"
        }
        return endpoints.get(doc_type.upper())
        
    async def _process_document(self, doc: Dict[str, Any], doc_type: str) -> Optional[Dict[str, Any]]:
        """Process a document from the API response."""
        try:
            # Get document details
            doc_id = doc.get("number") or doc.get("id")
            if not doc_id:
                return None
                
            # Basic document structure
            document = {
                "document_id": f"congress_{doc_type.lower()}_{doc_id}",
                "title": doc.get("title", ""),
                "content": doc.get("summary", ""),
                "source_type": "congress",
                "date": doc.get("latestAction", {}).get("actionDate"),
                "metadata": {
                    "congress": doc.get("congress"),
                    "type": doc_type,
                    "number": doc_id,
                    "url": doc.get("url"),
                    "latest_action": doc.get("latestAction"),
                    "sponsors": doc.get("sponsors", []),
                    "committees": doc.get("committees", []),
                    "subjects": doc.get("subjects", [])
                }
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing Congress.gov document: {e}")
            return None
            
    def _should_generate_alert(self, document: Dict[str, Any]) -> bool:
        """Check if an alert should be generated for this document."""
        # Example criteria - customize based on needs
        if document["metadata"]["type"] == "BILL":
            # Alert on bills with certain subjects
            subjects = document["metadata"].get("subjects", [])
            alert_subjects = ["civil rights", "voting", "elections"]
            return any(subj in " ".join(subjects).lower() for subj in alert_subjects)
            
        return False
        
    def _create_alert(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert for a document."""
        return {
            "title": f"New {document['metadata']['type']}: {document['title']}",
            "source_type": "congress",
            "date": document["date"],
            "threat_score": 0.7,  # Example score
            "categories": {
                "legislation": 0.9,
                "policy_change": 0.7
            },
            "summary": document["content"][:500] + "..." if len(document["content"]) > 500 else document["content"],
            "document_id": document["document_id"],
            "url": document["metadata"]["url"]
        } 