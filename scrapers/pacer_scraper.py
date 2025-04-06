# New file: scrapers/pacer_scraper.py
import os
import logging
import json
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/pacer_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants for PACER courts
FEDERAL_DISTRICT_COURTS = {
    # Major district courts
    'nysd': 'Southern District of New York',
    'cacd': 'Central District of California',
    'dcd': 'District of Columbia',
    'txnd': 'Northern District of Texas',
    'ilnd': 'Northern District of Illinois',
    # Additional district courts
    'flsd': 'Southern District of Florida',
    'mied': 'Eastern District of Michigan',
    'gamd': 'Middle District of Georgia',
    'ncmd': 'Middle District of North Carolina',
    'paed': 'Eastern District of Pennsylvania',
}

FEDERAL_APPELLATE_COURTS = {
    'ca1': 'First Circuit',
    'ca2': 'Second Circuit',
    'ca5': 'Fifth Circuit',
    'ca9': 'Ninth Circuit',
    'ca11': 'Eleventh Circuit',
    'cadc': 'D.C. Circuit',
}

# Document type mapping
DOCUMENT_TYPES = {
    'complaint': ['complaint', 'petition', 'initial filing'],
    'motion': ['motion', 'application', 'request'],
    'order': ['order', 'decision', 'ruling', 'opinion'],
    'brief': ['brief', 'memorandum', 'argument'],
    'judgment': ['judgment', 'verdict', 'determination'],
    'notice': ['notice', 'advisory', 'notification'],
    'transcript': ['transcript', 'hearing', 'proceedings'],
}

class PacerClient:
    """Client for interacting with PACER (Public Access to Court Electronic Records)."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the PACER client.
        
        Args:
            username: PACER username (from env var if None)
            password: PACER password (from env var if None)
        """
        self.username = username or os.environ.get("PACER_USERNAME")
        self.password = password or os.environ.get("PACER_PASSWORD")
        self.session = None
        self.is_logged_in = False
        
        # Check if juriscraper is installed
        try:
            from juriscraper.pacer import PacerSession, DocketReport, PacerDocketReport
            self.juriscraper_available = True
        except ImportError:
            logger.error("Juriscraper not installed. Install with: pip install juriscraper")
            self.juriscraper_available = False
    
    def login(self) -> bool:
        """
        Log in to PACER with credentials.
        
        Returns:
            Boolean indicating login success
        """
        if not self.juriscraper_available:
            return False
            
        if not self.username or not self.password:
            logger.error("PACER credentials not provided or found in environment variables")
            return False
        
        try:
            from juriscraper.pacer import PacerSession
            self.session = PacerSession(username=self.username, password=self.password)
            self.is_logged_in = self.session.login()
            
            if self.is_logged_in:
                logger.info("Successfully logged in to PACER")
            else:
                logger.error("Failed to log in to PACER. Check credentials.")
                
            return self.is_logged_in
            
        except Exception as e:
            logger.error(f"Error logging in to PACER: {e}")
            return False
    
    def logout(self) -> bool:
        """
        Log out from PACER session.
        
        Returns:
            Boolean indicating success
        """
        if self.session and self.is_logged_in:
            try:
                self.session.logout()
                self.is_logged_in = False
                logger.info("Successfully logged out from PACER")
                return True
            except Exception as e:
                logger.error(f"Error logging out from PACER: {e}")
        return False
    
    def search_dockets(
        self, 
        court: str, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime] = None,
        query_terms: List[str] = None,
        case_type: str = None,
        case_status: str = 'open',
        nature_of_suit: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search PACER dockets for a specific court.
        
        Args:
            court: Court abbreviation (e.g., 'nysd')
            start_date: Start date for search
            end_date: End date for search (default: today)
            query_terms: List of search terms
            case_type: Type of case (cv, cr, etc.)
            case_status: Status of case (open, closed, all)
            nature_of_suit: Nature of suit code
            
        Returns:
            List of docket dictionaries
        """
        if not self.is_logged_in:
            logger.warning("Not logged in to PACER. Attempting login...")
            if not self.login():
                return []
        
        try:
            from juriscraper.pacer import DocketReport
            
            # Format dates if needed
            if isinstance(start_date, datetime):
                start_date = start_date.strftime('%m/%d/%Y')
            
            if end_date is None:
                end_date = datetime.now().strftime('%m/%d/%Y')
            elif isinstance(end_date, datetime):
                end_date = end_date.strftime('%m/%d/%Y')
            
            # Initialize docket report
            report = DocketReport(court)
            report._session = self.session
            
            results = []
            
            # Process each search term
            terms = query_terms if query_terms else ["voting rights", "election", "civil rights"]
            
            for term in terms:
                try:
                    logger.info(f"Searching {court} for term: {term}")
                    
                    # Build query parameters
                    query_params = {
                        'filed_from': start_date,
                        'filed_to': end_date,
                        'case_status': case_status
                    }
                    
                    # Add optional parameters
                    if term:
                        query_params['case_name'] = term
                    if case_type:
                        query_params['case_type'] = case_type
                    if nature_of_suit:
                        query_params['nature_of_suit'] = nature_of_suit
                    
                    # Execute query
                    report.query(**query_params)
                    docket = report.data
                    
                    if not docket or 'docket_entries' not in docket:
                        logger.warning(f"No docket entries found for {term} in {court}")
                        continue
                    
                    logger.info(f"Found {len(docket['docket_entries'])} entries for {term} in {court}")
                    
                    # Process each entry
                    for entry in docket['docket_entries']:
                        doc = {
                            "case_number": docket.get('case_number', ''),
                            "case_name": docket.get('case_name', ''),
                            "court": court,
                            "court_full_name": FEDERAL_DISTRICT_COURTS.get(court, court),
                            "date_filed": entry.get('date_filed', ''),
                            "document_number": entry.get('document_number', ''),
                            "description": entry.get('description', ''),
                            "url": entry.get('url', ''),
                            "search_term": term,
                            "source_type": "pacer",
                            "document_id": f"pacer_{court}_{docket.get('case_number', '').replace(':', '_')}_{entry.get('document_number', '')}"
                        }
                        
                        # Add document type if available
                        doc["document_type"] = self._determine_document_type(entry.get('description', ''))
                        
                        # Add nature of suit
                        if 'nature_of_suit' in docket:
                            doc["nature_of_suit"] = docket['nature_of_suit']
                        
                        results.append(doc)
                        
                except Exception as e:
                    logger.error(f"Error searching {court} for {term}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error in search_dockets for {court}: {e}")
            return []
    
    def _determine_document_type(self, description: str) -> Optional[str]:
        """
        Determine document type based on description.
        
        Args:
            description: Document description text
            
        Returns:
            Document type or None if unknown
        """
        description = description.lower()
        
        for doc_type, keywords in DOCUMENT_TYPES.items():
            for keyword in keywords:
                if keyword.lower() in description:
                    return doc_type
        
        return None
    
    def download_document(self, court: str, pacer_doc_id: str, output_path: str) -> Optional[str]:
        """
        Download a document from PACER.
        
        Args:
            court: Court abbreviation
            pacer_doc_id: PACER document ID
            output_path: Directory to save document
            
        Returns:
            Path to downloaded file or None on failure
        """
        if not self.is_logged_in:
            logger.warning("Not logged in to PACER. Attempting login...")
            if not self.login():
                return None
        
        try:
            from juriscraper.pacer import PacerDocumentDownloader
            
            # Initialize document downloader
            downloader = PacerDocumentDownloader(court)
            downloader._session = self.session
            
            # Ensure output directory exists
            os.makedirs(output_path, exist_ok=True)
            
            # Generate filename
            filename = f"{court}_{pacer_doc_id}.pdf"
            filepath = os.path.join(output_path, filename)
            
            # Download document
            logger.info(f"Downloading document {pacer_doc_id} from {court}")
            downloaded = downloader.download_document(pacer_doc_id, filepath)
            
            if downloaded:
                logger.info(f"Successfully downloaded document to {filepath}")
                return filepath
            else:
                logger.warning(f"Failed to download document {pacer_doc_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading document {pacer_doc_id}: {e}")
            return None
    
    def extract_document_text(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from a PACER PDF document.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None on failure
        """
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                return text
                
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return None

def get_pacer_documents(days_back: int = 7, keywords: List[str] = None, courts: List[str] = None, download_docs: bool = False) -> List[Dict[str, Any]]:
    """
    Collect documents from PACER using Juriscraper.
    
    Args:
        days_back: Number of days to look back
        keywords: List of keywords to search for
        courts: List of courts to check (default: major federal courts)
        download_docs: Whether to download document PDFs
        
    Returns:
        List of document dictionaries
    """
    # Set default courts if none provided
    if not courts:
        courts = list(FEDERAL_DISTRICT_COURTS.keys())[:3]  # Use first 3 courts by default
    
    # Initialize PACER client
    client = PacerClient()
    
    if not client.juriscraper_available:
        logger.error("Juriscraper not available. Cannot proceed with PACER scraping.")
        return []
    
    if not client.login():
        logger.error("Failed to log in to PACER. Check credentials.")
        return []
    
    results = []
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Searching {len(courts)} courts for the past {days_back} days")
        
        # Process each court
        for court in courts:
            court_results = client.search_dockets(
                court=court,
                start_date=start_date,
                end_date=end_date,
                query_terms=keywords
            )
            
            results.extend(court_results)
            
            # Prevent rate limiting
            if len(courts) > 1:
                time.sleep(2)
        
        # Download documents if requested
        if download_docs and results:
            output_dir = "data/pacer_documents"
            
            for i, doc in enumerate(results):
                if 'url' in doc and doc['url']:
                    doc_id = doc.get('document_number')
                    
                    if doc_id:
                        # Download document
                        pdf_path = client.download_document(
                            court=doc['court'],
                            pacer_doc_id=doc_id,
                            output_path=output_dir
                        )
                        
                        if pdf_path:
                            # Extract text
                            doc['content'] = client.extract_document_text(pdf_path)
                            doc['local_path'] = pdf_path
                    
                # Prevent rate limiting
                if i % 5 == 0 and i > 0:
                    time.sleep(5)
        
        # Logout
        client.logout()
        
        logger.info(f"PACER search complete. Found {len(results)} documents")
        return results
        
    except Exception as e:
        logger.error(f"Critical error in PACER scraper: {e}")
        client.logout()
        return []

def save_pacer_results(results: List[Dict[str, Any]], output_dir: str = "data/pacer") -> None:
    """
    Save PACER search results to files.
    
    Args:
        results: List of document dictionaries
        output_dir: Directory to save results
    """
    if not results:
        logger.warning("No results to save")
        return
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save each document
        for doc in results:
            doc_id = doc.get('document_id', f"pacer_{int(time.time())}")
            filename = f"{doc_id}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(doc, f, indent=2)
        
        # Create index file
        index = {
            "timestamp": datetime.now().isoformat(),
            "count": len(results),
            "documents": [
                {
                    "document_id": doc.get('document_id', ''),
                    "case_name": doc.get('case_name', ''),
                    "court": doc.get('court', ''),
                    "date_filed": doc.get('date_filed', ''),
                    "document_type": doc.get('document_type', ''),
                    "has_content": 'content' in doc and bool(doc['content'])
                }
                for doc in results
            ]
        }
        
        index_path = os.path.join(output_dir, f"index_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
        
        logger.info(f"Saved {len(results)} documents to {output_dir}")
        
    except Exception as e:
        logger.error(f"Error saving PACER results: {e}")

# If the module is run directly, perform a test
if __name__ == "__main__":
    print("Testing PACER scraper...")
    
    # Create a test directory
    os.makedirs("data/pacer", exist_ok=True)
    
    # Test with limited courts and days for faster results
    docs = get_pacer_documents(days_back=3, courts=['dcd'], download_docs=False)
    
    print(f"Found {len(docs)} documents")
    
    # Display first few documents
    for i, doc in enumerate(docs[:3]):
        print(f"Document {i+1}:")
        print(f"  Case: {doc['case_name']}")
        print(f"  Court: {doc['court_full_name']}")
        print(f"  Document Type: {doc['document_type'] or 'Unknown'}")
        print(f"  Description: {doc['description'][:100]}...")
    
    # Save results
    save_pacer_results(docs)
    print(f"Results saved to data/pacer/")