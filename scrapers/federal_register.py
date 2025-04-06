# scrapers/federal_register.py - Simple version
import requests
import json
import os
from datetime import datetime, timedelta

def get_recent_documents(days_back=7, keywords=None):
    """Simple Federal Register document fetcher."""
    base_url = "https://www.federalregister.gov/api/v1/documents"
    
    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    print(f"Searching Federal Register from {start_date} to {end_date}")
    
    results = []
    
    # If keywords provided, search for each one
    search_terms = keywords if keywords else [""]
    
    for term in search_terms:
        if term:
            print(f"Searching for term: {term}")
        
        params = {
            "per_page": 20,
            "order": "newest",
            "conditions[publication_date][gte]": start_date,
            "conditions[publication_date][lte]": end_date
        }
        
        if term:
            params["conditions[term]"] = term
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("count", 0) > 0:
                results.extend(data.get("results", []))
                print(f"Found {len(data.get('results', []))} documents for term: {term}")
            
        except Exception as e:
            print(f"Error searching Federal Register: {e}")
    
    # Remove duplicates
    unique_docs = {}
    for doc in results:
        doc_number = doc.get("document_number")
        if doc_number and doc_number not in unique_docs:
            unique_docs[doc_number] = doc
    
    return list(unique_docs.values())

def save_documents(documents, output_dir="data/federal_register"):
    """Save documents to JSON files."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    for doc in documents:
        doc_number = doc.get("document_number")
        if not doc_number:
            continue
        
        filename = f"{output_dir}/{doc_number}.json"
        
        with open(filename, "w") as f:
            json.dump(doc, f, indent=2)
        
        print(f"Saved document {doc_number} to {filename}")

# Test the functionality
if __name__ == "__main__":
    # Create data directory
    os.makedirs("data/federal_register", exist_ok=True)
    
    # Test keywords
    test_keywords = [
        "voting rights",
        "civil rights",
        "election"
    ]
    
    # Get and save documents
    documents = get_recent_documents(days_back=7, keywords=test_keywords)
    save_documents(documents)
    
    print(f"Retrieved {len(documents)} total documents")