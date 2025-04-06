# Replacement for congress_api.py
# This would use unitedstates/congress instead of our custom API implementation

import os
import sys
import json
from datetime import datetime, timedelta

# Add unitedstates/congress path - would need to be cloned as a submodule
sys.path.append('./lib/congress')

from congress.bills import bill_info
from congress.utils import utils

def get_recent_legislation(days_back=30, keywords=None):
    """Get recent legislation using unitedstates/congress tools."""
    results = []
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Current Congress number
    congress = 119  # For 2025-2026
    
    # Get bill data using congress tools
    bill_types = ["hr", "s", "hjres", "sjres", "hconres", "sconres"]
    
    for bill_type in bill_types:
        # This would need to be adapted based on congress project structure
        bills = bill_info.bills_for_congress(congress, bill_type)
        
        for bill in bills:
            # Check if bill is within our date range
            if 'introduced_at' in bill and bill['introduced_at']:
                bill_date = datetime.fromisoformat(bill['introduced_at'])
                if bill_date < start_date:
                    continue
            
            # Check if bill matches keywords
            if keywords and not any(keyword.lower() in bill.get('title', '').lower() for keyword in keywords):
                continue
                
            # Format bill for our system
            results.append({
                "bill_id": f"{bill_type}{bill.get('number', '')}",
                "title": bill.get('title', ''),
                "url": f"https://www.congress.gov/bill/{congress}/{bill_type}/{bill.get('number', '')}",
                "introduced_date": bill.get('introduced_at', ''),
                "sponsor": bill.get('sponsor', {}).get('name', '') if bill.get('sponsor') else '',
                "summary": bill.get('summary', '')
            })
    
    return results