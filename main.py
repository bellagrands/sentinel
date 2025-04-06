#!/usr/bin/env python
"""
Sentinel Democracy Watchdog System - Main Entry Point

This script serves as the main entry point for the Sentinel system.
It provides an interface to run the collector, processor, and dashboard components.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
import json
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'sentinel_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SentinelApp:
    """Main application class for Sentinel."""
    
    def __init__(self):
        """Initialize the Sentinel application."""
        self.alerts_dir = os.path.join('data', 'alerts')
        self.documents_dir = os.path.join('data', 'documents')
        os.makedirs(self.alerts_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
        
    def get_alerts(self, acknowledged=None, limit=10):
        """Get list of alerts, optionally filtered by acknowledged status."""
        alerts = []
        alert_files = glob.glob(os.path.join(self.alerts_dir, '*.json'))
        
        for file_path in alert_files:
            try:
                with open(file_path, 'r') as f:
                    alert = json.load(f)
                    if acknowledged is None or alert.get('acknowledged', False) == acknowledged:
                        alerts.append(alert)
            except Exception as e:
                logger.error(f"Error reading alert file {file_path}: {e}")
                
        # Sort by timestamp descending and limit results
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return alerts[:limit]

def run_collector():
    """Run the document collector."""
    logger.info("Starting document collector...")
    from scripts.collect_documents import main as collect_main
    collect_main()

def run_processor():
    """Run the document processor."""
    logger.info("Starting document processor...")
    from scripts.process_documents import main as process_main
    process_main()

def run_dashboard():
    """Run the web dashboard."""
    logger.info("Starting web dashboard...")
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sentinel Democracy Watchdog System")
    
    # Add command-line arguments
    parser.add_argument("--collect", action="store_true", help="Run document collector")
    parser.add_argument("--process", action="store_true", help="Run document processor")
    parser.add_argument("--dashboard", action="store_true", help="Run web dashboard")
    parser.add_argument("--all", action="store_true", help="Run all components")
    
    args = parser.parse_args()
    
    # If no args specified, show help
    if not any([args.collect, args.process, args.dashboard, args.all]):
        parser.print_help()
        return
    
    # Run components based on arguments
    if args.all or args.collect:
        run_collector()
    
    if args.all or args.process:
        run_processor()
    
    if args.all or args.dashboard:
        run_dashboard()

if __name__ == "__main__":
    try:
    main()
    except KeyboardInterrupt:
        logger.info("Shutting down Sentinel...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)