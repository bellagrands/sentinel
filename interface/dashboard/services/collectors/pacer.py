"""
PACER data collector.

This module implements document collection from the PACER (Public Access to Court Electronic Records) system.
"""

import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .base import BaseCollector
from ..data_sources import DataSourceConfig

logger = logging.getLogger(__name__)

class PACERCollector(BaseCollector):
    """Collector for PACER court documents."""
    
    BASE_URL = "https://pcl.uscourts.gov/pcl-public-api/v1"
    
    def __init__(self, source_id: str, config: DataSourceConfig):
        """Initialize the collector."""
        super().__init__(source_id, config)
        
        # Set up API configuration
        self.username = config.custom_fields.get("username")
        self.password = config.custom_fields.get("password")
        self.rate_limit = config.rate_limit
        self.max_days_back = config.max_days_back
        self.courts = config.custom_fields.get("courts", [])
        self.session_token = None
        
    async def validate_config(self) -> List[str]:
        """Validate the collector configuration."""
        errors = []
        
        if not self.username:
            errors.append("PACER username is required")
            
        if not self.password:
            errors.append("PACER password is required")
            
        if not self.rate_limit or self.rate_limit < 1:
            errors.append("Rate limit must be at least 1 request per minute")
            
        if not self.max_days_back or self.max_days_back < 1:
            errors.append("Max days back must be at least 1")
            
        if not self.courts:
            errors.append("At least one court must be specified")
            
        return errors
        
    async def test_connection(self) -> bool:
        """Test the connection to PACER."""
        try:
            # Attempt to authenticate and get session token
            if await self._authenticate():
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error testing PACER connection: {e}")
            return False
            
    async def collect(self) -> bool:
        """Collect documents from PACER."""
        try:
            # Authenticate first
            if not await self._authenticate():
                logger.error("Failed to authenticate with PACER")
                return False
                
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.max_days_back)
            
            total_saved = 0
            
            async with aiohttp.ClientSession() as session:
                # Collect from each specified court
                for court in self.courts:
                    try:
                        # Search for cases
                        cases = await self._search_cases(session, court, start_date, end_date)
                        
                        # Process each case
                        for case in cases:
                            # Get case details
                            case_details = await self._get_case_details(session, court, case["caseId"])
                            if not case_details:
                                continue
                                
                            # Get docket entries
                            docket_entries = await self._get_docket_entries(session, court, case["caseId"])
                            
                            # Process new documents
                            for entry in docket_entries:
                                if await self._should_process_document(entry):
                                    document = await self._process_document(case_details, entry)
                                    
                                    if document and self._save_document(document):
                                        total_saved += 1
                                        
                                        # Generate alert if needed
                                        if self._should_generate_alert(document):
                                            alert = self._create_alert(document)
                                            self._save_alert(alert)
                                            
                    except Exception as e:
                        logger.error(f"Error collecting from court {court}: {e}")
                        continue
                        
            logger.info(f"Collected {total_saved} documents from PACER")
            return True
            
        except Exception as e:
            logger.error(f"Error collecting PACER documents: {e}")
            return False
            
        finally:
            # Always try to logout
            await self._logout()
                
    async def _authenticate(self) -> bool:
        """Authenticate with PACER and get session token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/authenticate"
                data = {
                    "username": self.username,
                    "password": self.password
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.session_token = result.get("token")
                        return bool(self.session_token)
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
            
    async def _logout(self):
        """Logout from PACER session."""
        if not self.session_token:
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/logout"
                headers = {"Authorization": f"Bearer {self.session_token}"}
                
                async with session.post(url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning("Failed to logout from PACER")
                        
        except Exception as e:
            logger.error(f"Logout error: {e}")
            
    async def _search_cases(self, session: aiohttp.ClientSession, court: str,
                          start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Search for cases in a court."""
        url = f"{self.BASE_URL}/courts/{court}/cases"
        headers = {"Authorization": f"Bearer {self.session_token}"}
        params = {
            "filed_start": start_date.strftime("%Y-%m-%d"),
            "filed_end": end_date.strftime("%Y-%m-%d"),
            "page_size": 100
        }
        
        cases = []
        page = 1
        
        while True:
            params["page"] = page
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    break
                    
                data = await response.json()
                cases.extend(data.get("cases", []))
                
                if len(data.get("cases", [])) < 100:
                    break
                    
                page += 1
                
        return cases
        
    async def _get_case_details(self, session: aiohttp.ClientSession, court: str,
                               case_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific case."""
        url = f"{self.BASE_URL}/courts/{court}/cases/{case_id}"
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            return None
            
    async def _get_docket_entries(self, session: aiohttp.ClientSession, court: str,
                                 case_id: str) -> List[Dict[str, Any]]:
        """Get docket entries for a case."""
        url = f"{self.BASE_URL}/courts/{court}/cases/{case_id}/entries"
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("entries", [])
            return []
            
    async def _should_process_document(self, entry: Dict[str, Any]) -> bool:
        """Check if a docket entry should be processed."""
        # Example criteria - customize based on needs
        if not entry.get("documentNumber"):
            return False
            
        # Skip entries without documents
        if not entry.get("documents"):
            return False
            
        # Check document types of interest
        doc_types = ["motion", "order", "opinion", "judgment"]
        return any(t in entry.get("description", "").lower() for t in doc_types)
        
    async def _process_document(self, case: Dict[str, Any],
                              entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a document from PACER."""
        try:
            doc_id = f"{case['caseId']}_{entry['documentNumber']}"
            
            document = {
                "document_id": f"pacer_{doc_id}",
                "title": entry.get("description", "Unknown Document"),
                "content": entry.get("text", ""),
                "source_type": "pacer",
                "date": entry.get("filedDate"),
                "metadata": {
                    "case_number": case.get("caseNumber"),
                    "case_title": case.get("caseTitle"),
                    "court": case.get("court"),
                    "nature_of_suit": case.get("natureOfSuit"),
                    "document_number": entry.get("documentNumber"),
                    "document_type": entry.get("documentType"),
                    "page_count": entry.get("pageCount"),
                    "parties": case.get("parties", []),
                    "cause": case.get("cause")
                }
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing PACER document: {e}")
            return None
            
    def _should_generate_alert(self, document: Dict[str, Any]) -> bool:
        """Check if an alert should be generated for this document."""
        # Example criteria - customize based on needs
        
        # Alert on specific document types
        alert_types = ["temporary restraining order", "injunction", "emergency motion"]
        if any(t in document["title"].lower() for t in alert_types):
            return True
            
        # Alert on specific natures of suit
        alert_natures = ["civil rights", "voting", "election", "constitutional"]
        nature = document["metadata"].get("nature_of_suit", "").lower()
        if any(n in nature for n in alert_natures):
            return True
            
        return False
        
    def _create_alert(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert for a document."""
        return {
            "title": f"New PACER Document: {document['title']}",
            "source_type": "pacer",
            "date": document["date"],
            "threat_score": 0.8,  # Example score
            "categories": {
                "legal_action": 0.9,
                "civil_rights": 0.7
            },
            "summary": f"New document filed in case {document['metadata']['case_number']}: {document['title']}",
            "document_id": document["document_id"],
            "url": f"https://pcl.uscourts.gov/cases/{document['metadata']['court']}/{document['metadata']['case_number']}"
        } 