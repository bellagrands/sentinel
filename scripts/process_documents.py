#!/usr/bin/env python
"""
Document Processing Script for Sentinel

This script processes collected documents using the NLP pipeline,
generates alerts for high-threat documents, and saves analysis results.

It can be run as a standalone script or as a service in the Docker container.
"""

import json
import logging
import os
import sys
import time
import gc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import traceback
import yaml
from utils.logging_config import setup_logger

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logger = setup_logger(__name__)

# Configure logging with fallback to console if file logging fails
try:
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Try to create a test file to check write permissions
    test_file_path = os.path.join('logs', 'permission_test.txt')
    try:
        with open(test_file_path, 'w') as f:
            f.write('test')
        os.remove(test_file_path)
        
        # If we can write to the directory, add the file handler
        log_file = os.path.join('logs', f"processor_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    except (IOError, PermissionError) as e:
        logger.warning(f"Unable to write to logs directory: {e}. Logging to console only.")
except Exception as e:
    logger.warning(f"Error setting up file logging: {e}. Logging to console only.")

# Import processor modules
from processor.nlp_pipeline import SentinelNLP
from processor.memory_optimization import batch_process, log_memory_usage, limit_text_length

# Default configuration
DEFAULT_CONFIG = {
    "processing": {
        "batch_size": 10,
        "max_document_length": 100000,
        "initial_scoring_threshold": 0.3,
        "alert_threshold": 0.6,
        "use_transformers": True
    },
    "directories": {
        "input": [
            "data/pacer",
            "data/congress",
            "data/federal_register"
        ],
        "output": "data/analyzed",
        "alerts": "data/alerts",
        "errors": "data/errors"
    },
    "schedule": {
        "interval_seconds": 3600,  # Default to hourly
        "max_retries": 3,
        "retry_delay": 300  # 5 minutes
    }
}

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yml."""
    try:
        with open('config.yml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def find_documents(input_dirs: List[str]) -> List[Dict[str, Any]]:
    """
    Find documents in input directories that need processing.
    
    Args:
        input_dirs: List of directories to check
        
    Returns:
        List of document dictionaries
    """
    documents = []
    processed_ids = set(get_processed_document_ids())
    
    for directory in input_dirs:
        if not os.path.exists(directory):
            logger.warning(f"Input directory {directory} does not exist")
            continue
            
        try:
            # Get all JSON files in the directory
            files = [f for f in os.listdir(directory) if f.endswith('.json') and not f.startswith('index_')]
            
            for filename in files:
                filepath = os.path.join(directory, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        doc = json.load(f)
                        
                        # Extract document ID or generate one
                        doc_id = doc.get('document_id', filename.replace('.json', ''))
                        
                        # Skip if already processed
                        if doc_id in processed_ids:
                            continue
                            
                        # Add document for processing
                        documents.append(doc)
                        
                except Exception as e:
                    logger.error(f"Error loading document {filepath}: {e}")
        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    logger.info(f"Found {len(documents)} documents to process")
    return documents

def get_processed_document_ids() -> List[str]:
    """
    Get list of already processed document IDs.
    
    Returns:
        List of document IDs
    """
    processed_ids = []
    
    # Check output directory
    output_dir = DEFAULT_CONFIG["directories"]["output"]
    if os.path.exists(output_dir):
        try:
            # Get all JSON files in the directory
            files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
            
            for filename in files:
                try:
                    # Extract ID from filename
                    doc_id = filename.replace('.json', '')
                    processed_ids.append(doc_id)
                    
                    # Also try to read document ID from file
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'r') as f:
                        doc = json.load(f)
                        if 'document_id' in doc:
                            processed_ids.append(doc['document_id'])
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error scanning output directory: {e}")
    
    # Also check alerts directory
    alerts_dir = DEFAULT_CONFIG["directories"]["alerts"]
    if os.path.exists(alerts_dir):
        try:
            # Get all JSON files in the directory
            files = [f for f in os.listdir(alerts_dir) if f.endswith('.json')]
            
            for filename in files:
                try:
                    filepath = os.path.join(alerts_dir, filename)
                    with open(filepath, 'r') as f:
                        alert = json.load(f)
                        if 'document_id' in alert:
                            processed_ids.append(alert['document_id'])
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error scanning alerts directory: {e}")
    
    # Remove duplicates
    return list(set(processed_ids))

def prepare_document(doc: Dict[str, Any], max_length: int = 100000) -> Dict[str, Any]:
    """
    Prepare document for processing, including text extraction and limiting.
    
    Args:
        doc: Document to prepare
        max_length: Maximum content length
        
    Returns:
        Prepared document
    """
    prepared_doc = doc.copy()
    
    # Ensure document has a title
    if 'title' not in prepared_doc or not prepared_doc['title']:
        prepared_doc['title'] = prepared_doc.get('case_name', 'Untitled Document')
    
    # Extract content
    if 'content' not in prepared_doc or not prepared_doc['content']:
        # Try to find content in other fields
        content_fields = ['text', 'body', 'description']
        for field in content_fields:
            if field in prepared_doc and prepared_doc[field]:
                prepared_doc['content'] = prepared_doc[field]
                break
    
    # Limit content length
    if 'content' in prepared_doc and prepared_doc['content']:
        prepared_doc['content'] = limit_text_length(prepared_doc['content'], max_length)
    
    # Ensure document has source_type
    if 'source_type' not in prepared_doc or not prepared_doc['source_type']:
        # Try to determine source type from other fields or set default
        if 'case_number' in prepared_doc:
            prepared_doc['source_type'] = 'pacer'
        elif 'bill_number' in prepared_doc:
            prepared_doc['source_type'] = 'congress'
        elif 'agency' in prepared_doc:
            prepared_doc['source_type'] = 'federal_register'
        else:
            prepared_doc['source_type'] = 'unknown'
    
    # Ensure document has a date
    if 'date' not in prepared_doc or not prepared_doc['date']:
        date_fields = ['date_filed', 'filing_date', 'publication_date']
        for field in date_fields:
            if field in prepared_doc and prepared_doc[field]:
                prepared_doc['date'] = prepared_doc[field]
                break
        
        # Default to current date if not found
        if 'date' not in prepared_doc or not prepared_doc['date']:
            prepared_doc['date'] = datetime.now().isoformat()
    
    return prepared_doc

def process_batch(batch: List[Dict[str, Any]], processor: SentinelNLP, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process a batch of documents.
    
    Args:
        batch: List of documents to process
        processor: NLP processor instance
        config: Processing configuration
        
    Returns:
        List of processed documents with analysis
    """
    max_length = config.get("processing", {}).get("max_document_length", 100000)
    results = []
    
    for doc in batch:
        try:
            # Prepare document
            prepared_doc = prepare_document(doc, max_length)
            
            # Skip documents without content
            if 'content' not in prepared_doc or not prepared_doc['content']:
                logger.warning(f"Skipping document {prepared_doc.get('document_id', 'unknown')} - no content")
                continue
            
            # Process document
            processed = processor.analyze_document(prepared_doc)
            results.append(processed)
            
        except Exception as e:
            logger.error(f"Error processing document {doc.get('document_id', 'unknown')}: {e}")
            logger.error(traceback.format_exc())
            
            # Save error info
            try:
                errors_dir = config.get("directories", {}).get("errors", "data/errors")
                os.makedirs(errors_dir, exist_ok=True)
                
                error_doc = {
                    "document_id": doc.get("document_id", "unknown"),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now().isoformat(),
                    "document": doc
                }
                
                error_file = os.path.join(errors_dir, f"error_{int(time.time())}_{doc.get('document_id', 'unknown')}.json")
                with open(error_file, 'w') as f:
                    json.dump(error_doc, f, indent=2)
            except Exception as save_error:
                logger.error(f"Error saving error info: {save_error}")
    
    return results

def save_results(results: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[int, int]:
    """
    Save processing results and generate alerts.
    
    Args:
        results: List of processed documents
        config: Configuration dictionary
        
    Returns:
        Tuple of (saved_count, alert_count)
    """
    output_dir = config.get("directories", {}).get("output", "data/analyzed")
    alerts_dir = config.get("directories", {}).get("alerts", "data/alerts")
    alert_threshold = config.get("processing", {}).get("alert_threshold", 0.6)
    
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(alerts_dir, exist_ok=True)
    
    saved_count = 0
    alert_count = 0
    
    for doc in results:
        try:
            # Get document ID
            doc_id = doc.get("document_id", f"doc_{int(time.time())}")
            
            # Save analyzed document
            output_file = os.path.join(output_dir, f"{doc_id}.json")
            with open(output_file, 'w') as f:
                json.dump(doc, f, indent=2)
            
            saved_count += 1
            
            # Check if alert should be generated
            threat_score = doc.get("threat_score", 0)
            
            if threat_score >= alert_threshold:
                # Generate alert
                alert = {
                    "alert_id": f"alert_{int(time.time())}_{doc_id}",
                    "document_id": doc_id,
                    "title": doc.get("title", "Untitled Document"),
                    "source_type": doc.get("source_type", "unknown"),
                    "date": doc.get("date", datetime.now().isoformat()),
                    "threat_score": threat_score,
                    "threat_categories": doc.get("threat_categories", {}),
                    "summary": doc.get("summary", "No summary available"),
                    "acknowledged": False,
                    "created_at": datetime.now().isoformat(),
                    "url": doc.get("url", None)
                }
                
                # Save alert
                alert_file = os.path.join(alerts_dir, f"{alert['alert_id']}.json")
                with open(alert_file, 'w') as f:
                    json.dump(alert, f, indent=2)
                
                alert_count += 1
                logger.info(f"Generated alert for document {doc_id} with threat score {threat_score:.2f}")
        
        except Exception as e:
            logger.error(f"Error saving results for document: {e}")
    
    return saved_count, alert_count

def run_processing(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run document processing.
    
    Args:
        config: Processing configuration
        
    Returns:
        Dictionary with processing results
    """
    # Log memory before starting
    log_memory_usage("Memory before processing")
    
    # Initialize NLP processor
    processor = SentinelNLP()
    
    # Find documents to process
    input_dirs = config.get("directories", {}).get("input", ["data/pacer"])
    documents = find_documents(input_dirs)
    
    if not documents:
        logger.info("No documents to process")
        return {"processed": 0, "alerts": 0}
    
    # Process documents in batches
    batch_size = config.get("processing", {}).get("batch_size", 10)
    
    # Define batch processing function
    def process_batch_with_config(batch):
        return process_batch(batch, processor, config)
    
    # Process in batches
    logger.info(f"Processing {len(documents)} documents in batches of {batch_size}")
    processed_docs = batch_process(documents, process_batch_with_config, batch_size=batch_size)
    
    # Save results
    saved_count, alert_count = save_results(processed_docs, config)
    
    # Log memory after processing
    log_memory_usage("Memory after processing")
    
    # Force garbage collection
    gc.collect()
    
    logger.info(f"Processed {len(processed_docs)} documents, saved {saved_count}, generated {alert_count} alerts")
    
    return {
        "processed": saved_count,
        "alerts": alert_count
    }

def should_run_now(config: Dict[str, Any]) -> bool:
    """
    Determine if processing should run based on schedule.
    
    Args:
        config: Schedule configuration
        
    Returns:
        Boolean indicating whether to run
    """
    # For container operation, always return True
    # The container's restart policy and CMD will handle scheduling
    if os.environ.get("RUNNING_IN_CONTAINER"):
        return True
    
    # Get last run time
    last_run_file = os.path.join("data", "processor_last_run.txt")
    try:
        if os.path.exists(last_run_file):
            with open(last_run_file, 'r') as f:
                last_run_str = f.read().strip()
                last_run = datetime.fromisoformat(last_run_str)
                
                # Check if enough time has passed since last run
                interval = config.get("schedule", {}).get("interval_seconds", 3600)
                next_run = last_run + timedelta(seconds=interval)
                
                if datetime.now() < next_run:
                    logger.info(f"Not time to run yet. Next run at {next_run}")
                    return False
    except Exception as e:
        logger.error(f"Error checking last run time: {e}")
    
    return True

def update_last_run_time():
    """Update the last run timestamp file."""
    last_run_file = os.path.join("data", "processor_last_run.txt")
    try:
        os.makedirs(os.path.dirname(last_run_file), exist_ok=True)
        with open(last_run_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error updating last run time: {e}")

def main():
    """Main entry point for the processor script."""
    logger.info("Starting document processor")
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration with batch size {config['processing']['batch_size']}")
    
    # Check if we should run based on schedule
    if not should_run_now(config):
        logger.info("Skipping run based on schedule")
        return
    
    # Run processing
    start_time = time.time()
    
    try:
        results = run_processing(config)
        
        # Log results
        logger.info(f"Processing complete. Processed {results['processed']} documents, generated {results['alerts']} alerts")
        
        # Update last run time
        update_last_run_time()
        
    except Exception as e:
        logger.error(f"Error in processing: {e}")
        logger.error(traceback.format_exc())
    
    # Log execution time
    execution_time = time.time() - start_time
    logger.info(f"Document processing completed in {execution_time:.2f} seconds")

if __name__ == "__main__":
    # Run processing once
    main()
    
    # If running in container, keep alive with scheduled execution
    if os.environ.get("RUNNING_IN_CONTAINER"):
        config = load_config()
        interval = config.get("schedule", {}).get("interval_seconds", 3600)
        
        logger.info(f"Running in container mode. Will process every {interval} seconds")
        
        while True:
            time.sleep(interval)
            main() 