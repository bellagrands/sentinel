#!/usr/bin/env python
"""
Document Collection Script for Sentinel

This script automatically collects new documents from configured data sources
and saves them to the data directory for later processing.

It can be run as a standalone script or as a service in the Docker container.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from utils.logging_config import setup_logger

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logger = setup_logger(__name__)

# Add file handler only if directory is writable
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
        log_file = os.path.join('logs', f"collector_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    except (IOError, PermissionError) as e:
        logger.warning(f"Unable to write to logs directory: {e}. Logging to console only.")
except Exception as e:
    logger.warning(f"Error setting up file logging: {e}. Logging to console only.")

# Import data collection modules
try:
    from scrapers.pacer_scraper import get_pacer_documents, save_pacer_results
except ImportError as e:
    logger.warning(f"Could not import PACER scraper: {e}")

# Default configuration
DEFAULT_CONFIG = {
    "sources": {
        "pacer": {
            "enabled": True,
            "days_back": 7,
            "courts": ["dcd", "ca9", "nysd"],
            "keywords": ["voting rights", "election law", "executive power", "civil liberties"],
            "download_documents": False
        },
        "congress": {
            "enabled": False,
            "days_back": 14,
            "legislation_types": ["BILL", "RESOLUTION"],
            "keywords": ["voting", "election", "executive", "court", "freedom", "liberty"]
        },
        "federal_register": {
            "enabled": False,
            "days_back": 14,
            "document_types": ["NOTICE", "RULE", "PROPOSED_RULE"],
            "keywords": ["voting", "election", "executive", "court", "freedom", "liberty"]
        }
    },
    "schedule": {
        "interval_seconds": 86400,  # Default to daily
        "start_hour": 2,  # 2 AM in container's timezone
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

def collect_from_pacer(config: Dict[str, Any]) -> int:
    """
    Collect documents from PACER.
    
    Args:
        config: PACER configuration
        
    Returns:
        Number of documents collected
    """
    try:
        logger.info("Starting PACER document collection")
        
        days_back = config.get("days_back", 7)
        courts = config.get("courts", ["dcd"])
        keywords = config.get("keywords", ["voting rights"])
        download_docs = config.get("download_documents", False)
        
        # Collect documents
        documents = get_pacer_documents(
            days_back=days_back,
            keywords=keywords,
            courts=courts,
            download_docs=download_docs
        )
        
        # Save results
        output_dir = os.path.join("data", "pacer")
        os.makedirs(output_dir, exist_ok=True)
        
        if documents:
            save_pacer_results(documents, output_dir=output_dir)
            logger.info(f"Collected {len(documents)} documents from PACER")
            return len(documents)
        else:
            logger.warning("No documents collected from PACER")
            return 0
            
    except Exception as e:
        logger.error(f"Error collecting from PACER: {e}")
        return 0

def collect_from_congress(config: Dict[str, Any]) -> int:
    """
    Collect documents from Congress.gov.
    
    Args:
        config: Congress configuration
        
    Returns:
        Number of documents collected
    """
    # This would implement the Congress.gov API scraper
    # Placeholder for now
    logger.info("Congress.gov collection not yet implemented")
    return 0

def collect_from_federal_register(config: Dict[str, Any]) -> int:
    """
    Collect documents from Federal Register.
    
    Args:
        config: Federal Register configuration
        
    Returns:
        Number of documents collected
    """
    # This would implement the Federal Register API scraper
    # Placeholder for now
    logger.info("Federal Register collection not yet implemented")
    return 0

def run_collection(config: Dict[str, Any]) -> Dict[str, int]:
    """
    Run document collection from all enabled sources.
    
    Args:
        config: Collection configuration
        
    Returns:
        Dictionary with collection results
    """
    results = {
        "pacer": 0,
        "congress": 0,
        "federal_register": 0,
        "total": 0
    }
    
    sources = config.get("sources", {})
    
    # Collect from PACER
    if sources.get("pacer", {}).get("enabled", False):
        results["pacer"] = collect_from_pacer(sources["pacer"])
    
    # Collect from Congress.gov
    if sources.get("congress", {}).get("enabled", False):
        results["congress"] = collect_from_congress(sources["congress"])
    
    # Collect from Federal Register
    if sources.get("federal_register", {}).get("enabled", False):
        results["federal_register"] = collect_from_federal_register(sources["federal_register"])
    
    # Calculate total
    results["total"] = sum(results.values()) - results["total"]
    
    return results

def should_run_now(config: Dict[str, Any]) -> bool:
    """
    Determine if collection should run based on schedule.
    
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
    last_run_file = os.path.join("data", "last_collection.txt")
    try:
        if os.path.exists(last_run_file):
            with open(last_run_file, 'r') as f:
                last_run_str = f.read().strip()
                last_run = datetime.fromisoformat(last_run_str)
                
                # Check if enough time has passed since last run
                interval = config.get("schedule", {}).get("interval_seconds", 86400)
                next_run = last_run + timedelta(seconds=interval)
                
                if datetime.now() < next_run:
                    logger.info(f"Not time to run yet. Next run at {next_run}")
                    return False
    except Exception as e:
        logger.error(f"Error checking last run time: {e}")
    
    return True

def update_last_run_time():
    """Update the last run timestamp file."""
    last_run_file = os.path.join("data", "last_collection.txt")
    try:
        os.makedirs(os.path.dirname(last_run_file), exist_ok=True)
        with open(last_run_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error updating last run time: {e}")

def main():
    """Main entry point for the collector script."""
    logger.info("Starting document collector")
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    logger.info(f"Loaded configuration with {len(config.get('sources', []))} sources")
    
    # Check if we should run based on schedule
    if not should_run_now(config):
        logger.info("Skipping run based on schedule")
        return
    
    # Run collection
    start_time = time.time()
    
    try:
        results = run_collection(config)
        
        # Log results
        logger.info(f"Collection complete. Collected {results['total']} documents:")
        for source, count in results.items():
            if source != "total":
                logger.info(f"  - {source}: {count} documents")
        
        # Update last run time
        update_last_run_time()
        
    except Exception as e:
        logger.error(f"Error in collection process: {e}")
    
    # Log execution time
    execution_time = time.time() - start_time
    logger.info(f"Document collection completed in {execution_time:.2f} seconds")

if __name__ == "__main__":
    # Run collection once
    main()
    
    # If running in container, keep alive with scheduled execution
    if os.environ.get("RUNNING_IN_CONTAINER"):
        config = load_config()
        interval = config.get("schedule", {}).get("interval_seconds", 86400)
        
        logger.info(f"Running in container mode. Will collect every {interval} seconds")
        
        while True:
            time.sleep(interval)
            main() 