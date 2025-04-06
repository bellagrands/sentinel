# test_congress_api.py
from scrapers.congress_api import get_recent_legislation, save_bills
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Make sure the data directory exists
os.makedirs("data/congress", exist_ok=True)

# Set up test keywords
test_keywords = [
    "voting rights",
    "executive power"
]

print("Starting Congress.gov API test...")
print(f"Searching for: {', '.join(test_keywords)}")

# Run the scraper - will use API key from environment
bills = get_recent_legislation(days_back=30, keywords=test_keywords)

# Save the results
save_bills(bills)

# Print summary
print(f"\nTest completed. Retrieved {len(bills)} bills")

# If bills were found, print some basic info about the first one
if bills:
    bill = bills[0]
    print("\nSample bill:")
    print(f"ID: {bill.get('bill_id', 'No ID')}")
    print(f"Title: {bill.get('title', 'No title')}")
    print(f"Sponsor: {bill.get('sponsor', 'No sponsor')}")
    print(f"Introduced: {bill.get('introduced_date', 'No date')}")
    print(f"URL: {bill.get('url', 'No URL')}")