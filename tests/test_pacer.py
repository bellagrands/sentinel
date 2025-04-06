"""
Test script for PACER integration.

This script tests the PACER integration functionality.
Note: Tests that interact with the actual PACER service are skipped
unless credentials are provided.
"""

import unittest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.pacer_scraper import PacerClient, get_pacer_documents, save_pacer_results
from scrapers.pacer_scraper import FEDERAL_DISTRICT_COURTS, DOCUMENT_TYPES

class TestPacerIntegration(unittest.TestCase):
    """Test cases for PACER integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_output_dir = "tests/test_output/pacer"
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def test_court_lists(self):
        """Test that court lists are properly defined."""
        self.assertTrue(len(FEDERAL_DISTRICT_COURTS) > 0)
        self.assertIn('dcd', FEDERAL_DISTRICT_COURTS)
        self.assertIn('nysd', FEDERAL_DISTRICT_COURTS)
    
    def test_document_types(self):
        """Test document type classification."""
        self.assertTrue(len(DOCUMENT_TYPES) > 0)
        self.assertIn('complaint', DOCUMENT_TYPES)
        self.assertIn('order', DOCUMENT_TYPES)
    
    @patch('scrapers.pacer_scraper.PacerClient')
    def test_get_pacer_documents(self, mock_client):
        """Test get_pacer_documents function with mocked client."""
        # Set up mock client
        instance = mock_client.return_value
        instance.juriscraper_available = True
        instance.login.return_value = True
        
        # Mock search_dockets to return test data
        mock_data = [
            {
                "case_number": "1:23-cv-12345",
                "case_name": "Test Case v. Demo",
                "court": "dcd",
                "court_full_name": "District of Columbia",
                "date_filed": "04/01/2023",
                "document_number": "1",
                "description": "Complaint for declaratory and injunctive relief",
                "search_term": "voting rights",
                "source_type": "pacer",
                "document_id": "pacer_dcd_1_23-cv-12345_1",
                "document_type": "complaint"
            }
        ]
        instance.search_dockets.return_value = mock_data
        
        # Call function
        results = get_pacer_documents(days_back=7, courts=["dcd"])
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["case_name"], "Test Case v. Demo")
        self.assertEqual(results[0]["document_type"], "complaint")
        
        # Verify login/logout called
        instance.login.assert_called_once()
        instance.logout.assert_called_once()
    
    def test_save_pacer_results(self):
        """Test saving PACER results to files."""
        # Create test data
        test_data = [
            {
                "case_number": "1:23-cv-12345",
                "case_name": "Test Case v. Demo",
                "court": "dcd",
                "date_filed": "04/01/2023",
                "document_number": "1",
                "description": "Complaint for declaratory relief",
                "source_type": "pacer",
                "document_id": "pacer_dcd_1_23-cv-12345_1",
                "document_type": "complaint"
            }
        ]
        
        # Save results
        save_pacer_results(test_data, output_dir=self.test_output_dir)
        
        # Verify files were created
        files = os.listdir(self.test_output_dir)
        self.assertTrue(any(f.startswith("index_") for f in files))
        self.assertTrue(any(f.startswith("pacer_dcd") for f in files))
        
        # Verify content of saved file
        doc_file = next(f for f in files if f.startswith("pacer_dcd"))
        with open(os.path.join(self.test_output_dir, doc_file), 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["case_name"], "Test Case v. Demo")
        self.assertEqual(saved_data["document_type"], "complaint")
    
    def test_pacer_client_initialization(self):
        """Test PacerClient initialization."""
        with patch.dict('os.environ', {'PACER_USERNAME': 'test_user', 'PACER_PASSWORD': 'test_pass'}):
            client = PacerClient()
            self.assertEqual(client.username, 'test_user')
            self.assertEqual(client.password, 'test_pass')
    
    def test_determine_document_type(self):
        """Test document type determination."""
        client = PacerClient()
        
        self.assertEqual(client._determine_document_type("Complaint for injunctive relief"), "complaint")
        self.assertEqual(client._determine_document_type("Motion to dismiss"), "motion")
        self.assertEqual(client._determine_document_type("Order granting summary judgment"), "order")
        self.assertEqual(client._determine_document_type("Appellant's Brief"), "brief")
        self.assertEqual(client._determine_document_type("Notice of Appearance"), "notice")
        self.assertEqual(client._determine_document_type("Random text without keywords"), None)

    @unittest.skipUnless(os.environ.get('PACER_USERNAME') and os.environ.get('PACER_PASSWORD'),
                       "PACER credentials not available for live test")
    def test_live_pacer_connection(self):
        """Test actual PACER connection if credentials are available."""
        client = PacerClient()
        logged_in = client.login()
        self.assertTrue(logged_in)
        if logged_in:
            client.logout()

if __name__ == '__main__':
    unittest.main() 