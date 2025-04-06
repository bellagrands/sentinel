# scrapers/congress_api.py
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CongressAPI:
    """
    A client for the Congress.gov API.
    """
    
    BASE_URL = "https://api.congress.gov/v3"
    
    def __init__(self, api_key=None):
        """Initialize the Congress.gov API client with an API key."""
        # Use provided key or get from environment
        self.api_key = api_key or os.getenv("CONGRESS_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set CONGRESS_API_KEY environment variable or pass key directly.")
        
    def get_recent_bills(self, congress=119, limit=20, offset=0, bill_type=None):
        """
        Get recent bills from the Congress.gov API.
        
        Args:
            congress: The congress number (e.g., 118 for the 118th Congress)
            limit: Number of results to return (max 250)
            offset: Starting record offset
            bill_type: Type of bill (e.g., "hr" for House bills)
            
        Returns:
            Dictionary containing bill data
        """
        endpoint = f"{self.BASE_URL}/bill"
        
        # Build the query parameters
        params = {
            "api_key": self.api_key,
            "format": "json",
            "limit": min(limit, 250),  # API max is 250
            "offset": offset
        }
        
        # Add congress if specified
        if congress:
            endpoint = f"{endpoint}/{congress}"
            
            # Add bill type if specified
            if bill_type:
                endpoint = f"{endpoint}/{bill_type}"
        
        try:
            # Make the API request
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching bills from Congress.gov API: {e}")
            return {"bills": []}
    
    def get_bill_details(self, congress, bill_type, bill_number):
        """
        Get detailed information about a specific bill.
        
        Args:
            congress: The congress number (e.g., 118)
            bill_type: Type of bill (e.g., "hr", "s")
            bill_number: Bill number
            
        Returns:
            Dictionary containing bill details
        """
        endpoint = f"{self.BASE_URL}/bill/{congress}/{bill_type}/{bill_number}"
        
        params = {
            "api_key": self.api_key,
            "format": "json"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching bill details from Congress.gov API: {e}")
            return {}
    
    def search_bills(self, query, congress=None, limit=20):
        """
        Search for bills by keyword.
        
        Args:
            query: Search query
            congress: Optional congress number to filter by
            limit: Number of results to return
            
        Returns:
            List of matching bills
        """
        endpoint = f"{self.BASE_URL}/bill"
        
        # Build the query parameters
        params = {
            "api_key": self.api_key,
            "format": "json",
            "limit": min(limit, 250),  # API max is 250
            "q": query
        }
        
        # Add congress if specified
        if congress:
            endpoint = f"{endpoint}/{congress}"
        
        try:
            # Make the API request
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching bills in Congress.gov API: {e}")
            return {"bills": []}

def get_recent_legislation(api_key=None, days_back=30, keywords=None):
    """
    Get recent legislation from Congress.gov API, optionally filtered by keywords.
    
    Args:
        api_key: Congress.gov API key (optional if set in environment)
        days_back: Number of days to look back (not directly supported, used for filtering)
        keywords: List of keywords to search for
        
    Returns:
        List of bill dictionaries with details
    """
    # Use provided key or get from environment
    api_key = api_key or os.getenv("CONGRESS_API_KEY")
    if not api_key:
        raise ValueError("API key is required. Set CONGRESS_API_KEY environment variable or pass key directly.")
    
    api = CongressAPI(api_key)
    
    # We'll use the current Congress (118th as of 2024-2025)
    congress = 119
    
    results = []
    
    # If keywords provided, search for each one
    if keywords:
        for keyword in keywords:
            print(f"Searching for legislation with term: {keyword}")
            
            # Search bills with this keyword
            response = api.search_bills(keyword, congress=congress, limit=50)
            
            bills_data = response.get("bills", [])
            
            print(f"Found {len(bills_data)} bills for term: {keyword}")
            
            # Process each bill
            for bill_data in bills_data:
                # Extract bill information
                bill_number = bill_data.get("number", "")
                bill_type = bill_data.get("type", "").lower()
                congress_num = bill_data.get("congress", "")
                
                # Get bill details
                if bill_number and bill_type and congress_num:
                    # Get detailed bill information
                    bill_details = api.get_bill_details(congress_num, bill_type, bill_number)
                    
                    # Extract cosponsors if they exist
                    cosponsors = []
                    if bill_details and 'bill' in bill_details and 'cosponsors' in bill_details['bill']:
                        for cosponsor in bill_details['bill']['cosponsors']:
                            cosponsors.append({
                                'name': cosponsor.get('name', ''),
                                'state': cosponsor.get('state', ''),
                                'party': cosponsor.get('party', ''),
                                'sponsorshipDate': cosponsor.get('sponsorshipDate', '')
                            })
                    
                    bill = {
                        "bill_id": f"{bill_type.upper()}{bill_number}",
                        "title": bill_data.get("title", ""),
                        "url": f"https://www.congress.gov/bill/{congress_num}th-congress/{bill_type}/{bill_number}",
                        "introduced_date": bill_data.get("introducedDate", ""),
                        "sponsor": bill_data.get("sponsors", [{}])[0].get("name", "") if bill_data.get("sponsors") else "",
                        "sponsor_party": bill_data.get("sponsors", [{}])[0].get("party", "") if bill_data.get("sponsors") else "",
                        "sponsor_state": bill_data.get("sponsors", [{}])[0].get("state", "") if bill_data.get("sponsors") else "",
                        "cosponsors": cosponsors,
                        "cosponsors_count": len(cosponsors),
                        "latest_action": bill_data.get("latestAction", {}).get("text", ""),
                        "latest_action_date": bill_data.get("latestAction", {}).get("actionDate", ""),
                        "search_term": keyword
                    }
                    
                    # Only append bills within our date range
                    if bill.get("introduced_date"):
                        try:
                            introduced_date = datetime.strptime(bill["introduced_date"], "%Y-%m-%d")
                            cutoff_date = datetime.now() - timedelta(days=days_back)
                            
                            if introduced_date >= cutoff_date:
                                results.append(bill)
                        except:
                            # If date parsing fails, include the bill anyway
                            results.append(bill)
                    else:
                        results.append(bill)
    else:
        # If no keywords, just get recent bills
        print("Fetching recent legislation")
        
        # Get bills for each bill type
        bill_types = ["hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"]
        
        for bill_type in bill_types:
            response = api.get_recent_bills(congress=congress, limit=50, bill_type=bill_type)
            
            bills_data = response.get("bills", [])
            
            print(f"Found {len(bills_data)} recent {bill_type.upper()} bills")
            
            # Process each bill
            for bill_data in bills_data:
                bill_number = bill_data.get('number', '')
                
                # Get detailed bill information to include cosponsors
                bill_details = api.get_bill_details(congress, bill_type, bill_number)
                
                # Extract cosponsors if they exist
                cosponsors = []
                if bill_details and 'bill' in bill_details and 'cosponsors' in bill_details['bill']:
                    for cosponsor in bill_details['bill']['cosponsors']:
                        cosponsors.append({
                            'name': cosponsor.get('name', ''),
                            'state': cosponsor.get('state', ''),
                            'party': cosponsor.get('party', ''),
                            'sponsorshipDate': cosponsor.get('sponsorshipDate', '')
                        })
                
                # Create bill object
                bill = {
                    "bill_id": f"{bill_type.upper()}{bill_data.get('number', '')}",
                    "title": bill_data.get("title", ""),
                    "url": f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}/{bill_data.get('number', '')}",
                    "introduced_date": bill_data.get("introducedDate", ""),
                    "sponsor": bill_data.get("sponsors", [{}])[0].get("name", "") if bill_data.get("sponsors") else "",
                    "sponsor_party": bill_data.get("sponsors", [{}])[0].get("party", "") if bill_data.get("sponsors") else "",
                    "sponsor_state": bill_data.get("sponsors", [{}])[0].get("state", "") if bill_data.get("sponsors") else "",
                    "cosponsors": cosponsors,
                    "cosponsors_count": len(cosponsors),
                    "latest_action": bill_data.get("latestAction", {}).get("text", ""),
                    "latest_action_date": bill_data.get("latestAction", {}).get("actionDate", "")
                }
                
                # Only append bills within our date range
                if bill.get("introduced_date"):
                    try:
                        introduced_date = datetime.strptime(bill["introduced_date"], "%Y-%m-%d")
                        cutoff_date = datetime.now() - timedelta(days=days_back)
                        
                        if introduced_date >= cutoff_date:
                            results.append(bill)
                    except:
                        # If date parsing fails, include the bill anyway
                        results.append(bill)
                else:
                    results.append(bill)
    
    # Remove duplicates based on bill_id
    unique_bills = {}
    for bill in results:
        if bill["bill_id"] not in unique_bills:
            unique_bills[bill["bill_id"]] = bill
    
    print(f"Found {len(unique_bills)} total unique bills")
    return list(unique_bills.values())

def save_bills(bills, output_dir="data/congress", format="json"):
    """
    Save bills to files.
    
    Args:
        bills: List of bill dictionaries
        output_dir: Directory to save files in
        format: Output format (json or csv)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    if format.lower() == "json":
        for bill in bills:
            bill_id = bill.get("bill_id")
            if not bill_id:
                continue
                
            # Clean up bill_id for filename
            safe_id = bill_id.replace(" ", "_").replace("/", "_")
            filename = f"{output_dir}/{safe_id}.json"
            
            with open(filename, "w") as f:
                json.dump(bill, f, indent=2)
                
            print(f"Saved bill {bill_id} to {filename}")
    
    # Also save a combined file with all bills
    all_bills_file = f"{output_dir}/all_bills_{datetime.now().strftime('%Y%m%d')}.json"
    with open(all_bills_file, "w") as f:
        json.dump(bills, f, indent=2)
    
    print(f"Saved all {len(bills)} bills to {all_bills_file}")

# Example usage
if __name__ == "__main__":
    # Create data directory
    os.makedirs("data/congress", exist_ok=True)
    
    # Test keywords
    test_keywords = [
        "voting rights",
        "civil rights"
    ]
    
    # Get and save bills - will use API key from environment
    bills = get_recent_legislation(days_back=30, keywords=test_keywords)
    save_bills(bills)
    
    print(f"Retrieved {len(bills)} total bills")