# New file: scrapers/state_legislature.py
import requests
import os
import logging
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
from utils.logging_config import setup_logger

# Set up logging
logger = setup_logger(__name__)

def get_state_legislation(states=None, days_back=30, keywords=None):
    """
    Get recent state legislation using Open States API.
    
    Args:
        states: List of state codes to search (default: major states)
        days_back: Number of days to look back
        keywords: List of keywords to search for
        
    Returns:
        List of bill dictionaries with details
    """
    # API key from environment
    api_key = os.environ.get("OPENSTATES_API_KEY")
    
    if not api_key:
        logger.warning("Open States API key not found in environment variables")
        return []
        
    # Default to important states if none specified
    if not states:
        states = [
            "ca",  # California
            "ny",  # New York
            "tx",  # Texas
            "fl",  # Florida
            "il",  # Illinois
            "pa",  # Pennsylvania
            "oh",  # Ohio
            "ga",  # Georgia
            "nc",  # North Carolina
            "mi"   # Michigan
        ]
    
    # Default keywords if none specified
    if not keywords:
        keywords = [
            "voting rights",
            "election",
            "civil rights",
            "ballot",
            "executive power",
            "immigration",
            "emergency declaration"
        ]
    
    results = []
    
    # Calculate date cutoff
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Search parameters
    headers = {
        "X-API-Key": api_key
    }
    
    logger.info(f"Searching legislation in {len(states)} states for the past {days_back} days")
    
    for state in states:
        try:
            state_results = 0
            logger.info(f"Processing state: {state}")
            
            # Search for each keyword
            for term in keywords:
                logger.info(f"Searching for term '{term}' in {state}")
                
                params = {
                    "jurisdiction": state,
                    "created_since": cutoff_date,
                    "page": 1,
                    "per_page": 20
                }
                
                if term:
                    params["q"] = term
                
                # Make API request with pagination
                more_pages = True
                while more_pages:
                    try:
                        # Make API request
                        response = requests.get(
                            "https://v3.openstates.org/bills",
                            headers=headers,
                            params=params
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            bills = data.get("results", [])
                            
                            # Process bills
                            for bill in bills:
                                # Extract sponsors and categorize them
                                sponsors = []
                                primary_sponsor = None
                                
                                for sponsor in bill.get("sponsors", []):
                                    sponsor_data = {
                                        "name": sponsor.get("name", ""),
                                        "type": sponsor.get("classification", ""),
                                        "id": sponsor.get("id", "")
                                    }
                                    
                                    # Save primary sponsor separately
                                    if sponsor.get("classification") == "primary":
                                        primary_sponsor = sponsor_data
                                    
                                    sponsors.append(sponsor_data)
                                
                                # Build standardized bill object
                                bill_data = {
                                    "bill_id": bill.get("identifier", ""),
                                    "title": bill.get("title", ""),
                                    "state": state,
                                    "introduced_date": bill.get("created_at", ""),
                                    "last_action_date": bill.get("updated_at", ""),
                                    "url": f"https://openstates.org/{state}/bills/{bill.get('session', '')}/{bill.get('identifier', '')}",
                                    "summary": bill.get("abstract", "") or bill.get("title", ""),
                                    "search_term": term,
                                    "source_type": "state_legislature",
                                    "primary_sponsor": primary_sponsor,
                                    "sponsors": sponsors,
                                    "subjects": bill.get("subject", []),
                                    "status": bill.get("latest_action_description", "")
                                }
                                
                                # Add to results if not already present
                                if not any(r.get("bill_id") == bill_data["bill_id"] and r.get("state") == state for r in results):
                                    results.append(bill_data)
                                    state_results += 1
                            
                            # Check for more pages
                            pagination = data.get("pagination", {})
                            if pagination.get("page", 1) < pagination.get("max_page", 1):
                                params["page"] = pagination.get("page", 1) + 1
                            else:
                                more_pages = False
                                
                        else:
                            logger.error(f"Error fetching data for {state}, term '{term}': {response.status_code}")
                            more_pages = False
                            
                    except Exception as e:
                        logger.error(f"Error processing page for {state}, term '{term}': {e}")
                        more_pages = False
            
            logger.info(f"Collected {state_results} bills for {state}")
                    
        except Exception as e:
            logger.error(f"Error processing state {state}: {e}")
    
    logger.info(f"State legislation search complete. Found {len(results)} bills")
    return results

def get_state_documents(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get documents from state legislatures.
    
    Args:
        config (Dict[str, Any]): Configuration for state legislature scraping
        
    Returns:
        List[Dict[str, Any]]: List of documents
    """
    try:
        # This is a placeholder - implement actual state legislature scraping
        logger.info("Getting documents from state legislatures")
        
        # Example document structure
        docs = [{
            'id': 'EXAMPLE_STATE_001',
            'source': 'state_legislature',
            'title': 'Example State Bill',
            'text': 'This is an example state legislature document...',
            'url': 'https://legislature.example.com/bill/001',
            'metadata': {
                'state': 'Example State',
                'bill_number': 'HB123',
                'filing_date': datetime.now().isoformat()
            }
        }]
        
        return docs
        
    except Exception as e:
        logger.error(f"Error getting state legislature documents: {e}")
        return []

def save_state_results(docs: List[Dict[str, Any]]) -> None:
    """
    Save state legislature documents to the data directory.
    
    Args:
        docs (List[Dict[str, Any]]): List of documents to save
    """
    try:
        # Create documents directory if it doesn't exist
        os.makedirs('data/documents', exist_ok=True)
        
        # Save each document
        for doc in docs:
            filename = f"state_{doc['id']}.json"
            filepath = os.path.join('data', 'documents', filename)
            
            with open(filepath, 'w') as f:
                json.dump(doc, f, indent=2)
            
            logger.info(f"Saved state legislature document: {filename}")
            
    except Exception as e:
        logger.error(f"Error saving state legislature results: {e}")

# If the module is run directly, perform a test
if __name__ == "__main__":
    print("Testing state legislature scraper...")
    bills = get_state_legislation(states=["ca"], days_back=7, keywords=["voting"])
    print(f"Found {len(bills)} bills")
    for bill in bills[:3]:  # Print first 3 bills
        print(f"- {bill['bill_id']}: {bill['title']}")
        if bill.get('primary_sponsor'):
            print(f"  Sponsor: {bill['primary_sponsor']['name']}")