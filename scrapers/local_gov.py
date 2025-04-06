# New file: scrapers/local_gov.py
from civic_scraper.legislative import LegistarScraper
import os

def get_local_legislation(jurisdictions=None):
    """Collect local government legislation using civic-scraper."""
    results = []
    
    # Default jurisdictions to monitor
    if not jurisdictions:
        jurisdictions = [
            {"name": "chicago", "url": "https://chicago.legistar.com"},
            {"name": "nyc", "url": "https://legistar.council.nyc.gov"}
        ]
    
    for jurisdiction in jurisdictions:
        try:
            scraper = LegistarScraper(jurisdiction=jurisdiction["name"], 
                                     host=jurisdiction["url"])
            documents = scraper.get_documents(start_date="2024-03-01")
            
            # Process and standardize results
            for doc in documents:
                results.append({
                    "title": doc.get("title", ""),
                    "source": f"local_gov_{jurisdiction['name']}",
                    "date": doc.get("date", ""),
                    "url": doc.get("url", ""),
                    "type": doc.get("type", "")
                })
                
        except Exception as e:
            print(f"Error scraping {jurisdiction['name']}: {e}")
    
    return results