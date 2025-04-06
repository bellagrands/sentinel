from scrapers.federal_register import get_recent_documents, save_documents
import os

# Make sure data directory exists
os.makedirs("data/federal_register", exist_ok=True)

# Set up a minimal test with just a few keywords
test_keywords = [
    "voting rights",
    "executive power"
]

print("Starting Federal Register test scraper...")
print(f"Searching for: {', '.join(test_keywords)}")

# Run the scraper with a small lookback period
documents = get_recent_documents(days_back=3, keywords=test_keywords)

# Save the results
save_documents(documents)

# Print summary
print(f"\nTest completed. Retrieved {len(documents)} documents")

# If documents were found, print some basic info about the first one
if documents:
    doc = documents[0]
    print("\nSample document:")
    print(f"Title: {doc.get('title', 'No title')}")
    print(f"Publication Date: {doc.get('publication_date', 'No date')}")
    print(f"Type: {doc.get('type', 'No type')}")
    print(f"URL: {doc.get('html_url', 'No URL')}")