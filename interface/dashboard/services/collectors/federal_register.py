"""
Federal Register data collector.

This module implements document collection from the Federal Register API.
"""

import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .base import BaseCollector
from ..data_sources import DataSourceConfig

logger = logging.getLogger(__name__)

class FederalRegisterCollector(BaseCollector):
    """Collector for Federal Register documents."""
    
    BASE_URL = "https://www.federalregister.gov/api/v1"
    
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
        """Test the connection to the Federal Register API."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to fetch a single document to test connection
                url = f"{self.BASE_URL}/documents"
                params = {
                    "api_key": self.api_key,
                    "per_page": 1,
                    "fields[]": ["document_number"]
                }
                
                async with session.get(url, params=params) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error testing Federal Register connection: {e}")
            return False
            
    async def collect(self) -> bool:
        """Collect documents from the Federal Register."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.max_days_back)
            
            async with aiohttp.ClientSession() as session:
                # Fetch documents page by page
                page = 1
                total_saved = 0
                
                while True:
                    # Build request parameters
                    params = {
                        "api_key": self.api_key,
                        "per_page": 20,
                        "page": page,
                        "fields[]": [
                            "title",
                            "document_number",
                            "publication_date",
                            "document_type",
                            "abstract",
                            "html_url",
                            "pdf_url",
                            "agencies",
                            "topics"
                        ],
                        "conditions[publication_date][gte]": start_date.strftime("%Y-%m-%d"),
                        "conditions[publication_date][lte]": end_date.strftime("%Y-%m-%d"),
                        "conditions[type][]": self.config.document_types
                    }
                    
                    # Make request
                    url = f"{self.BASE_URL}/documents"
                    async with session.get(url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"Error fetching Federal Register documents: {response.status}")
                            return False
                            
                        data = await response.json()
                        
                        # Process documents
                        for doc in data.get("results", []):
                            # Convert to our document format
                            document = {
                                "document_id": f"fr_{doc['document_number']}",
                                "title": doc["title"],
                                "content": doc.get("abstract", ""),
                                "source_type": "federal_register",
                                "date": doc["publication_date"],
                                "metadata": {
                                    "document_number": doc["document_number"],
                                    "document_type": doc["document_type"],
                                    "html_url": doc["html_url"],
                                    "pdf_url": doc.get("pdf_url"),
                                    "agencies": doc.get("agencies", []),
                                    "topics": doc.get("topics", [])
                                }
                            }
                            
                            # Save document
                            if self._save_document(document):
                                total_saved += 1
                                
                                # Generate alert if needed (example: new executive order)
                                if doc["document_type"] == "Executive Order":
                                    alert = {
                                        "title": f"New Executive Order: {doc['title']}",
                                        "source_type": "federal_register",
                                        "date": doc["publication_date"],
                                        "threat_score": 0.8,  # Example score
                                        "categories": {
                                            "executive_action": 0.9,
                                            "policy_change": 0.7
                                        },
                                        "summary": doc.get("abstract", "No summary available"),
                                        "document_id": document["document_id"],
                                        "url": doc["html_url"]
                                    }
                                    self._save_alert(alert)
                        
                        # Check if we have more pages
                        if len(data.get("results", [])) < 20:
                            break
                            
                        page += 1
                
                logger.info(f"Collected {total_saved} documents from Federal Register")
                return True
                
        except Exception as e:
            logger.error(f"Error collecting Federal Register documents: {e}")
            return False 