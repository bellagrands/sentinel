#!/usr/bin/env python
"""
Sentinel Democracy Watchdog System - Main Entry Point

This script serves as the main entry point for the Sentinel system.
It provides an interface to run the collector, processor, and web interface components.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api import router as api_router
from utils.logging_config import setup_logger
from scripts.collect_documents import main as collect_main
from scripts.process_documents import main as process_main
from config import STORAGE_ROOT, DOCUMENT_STORAGE

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logger = setup_logger(__name__)

def setup_fastapi() -> FastAPI:
    """Set up FastAPI application with CORS and routes."""
    app = FastAPI(
        title="Sentinel API",
        description="API for the Sentinel Democracy Watchdog System",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes with prefix
    app.include_router(api_router, prefix="/api")
    
    return app

def run_collector() -> None:
    """Run the document collector."""
    try:
        logger.info("Starting document collector...")
        collect_main()
    except Exception as e:
        logger.error(f"Error in collector: {e}")

def run_processor() -> None:
    """Run the document processor."""
    try:
        logger.info("Starting document processor...")
        process_main()
    except Exception as e:
        logger.error(f"Error in processor: {e}")

def run_web_interface(api_only: bool = False) -> None:
    """
    Run the web interface (FastAPI for API and optionally Flask for dashboard).
    
    Args:
        api_only: If True, only run the FastAPI server
    """
    # Create necessary directories
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs(os.path.join(STORAGE_ROOT, 'alerts'), exist_ok=True)
    
    if api_only:
        # Run only FastAPI server
        app = setup_fastapi()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Import dashboard only when needed
        from dashboard import create_app as create_flask_app
        import threading
        
        def run_api():
            app = setup_fastapi()
            uvicorn.run(app, host="0.0.0.0", port=8000)
            
        def run_dashboard():
            app = create_flask_app()
            app.run(host="0.0.0.0", port=5000)
            
        # Start API server in a separate thread
        api_thread = threading.Thread(target=run_api)
        api_thread.start()
        
        # Run Flask app in main thread
        run_dashboard()

def run_collector_processor() -> None:
    """Run both collector and processor in a continuous loop."""
    while True:
        try:
            # Run collector
            run_collector()
            
            # Wait before running processor
            time.sleep(5)
            
            # Run processor
            run_processor()
            
            # Wait for next cycle
            logger.info("Waiting for next cycle...")
            time.sleep(60)  # Wait 1 minute before next cycle
            
        except Exception as e:
            logger.error(f"Error in main process: {e}")
            time.sleep(60)  # Wait before retrying

def main() -> None:
    """Main function to parse arguments and run components."""
    parser = argparse.ArgumentParser(description="Sentinel Democracy Watchdog System")
    parser.add_argument(
        "--mode",
        choices=["all", "collect", "process", "web", "api", "watch"],
        default="all",
        help="Mode to run (all, collect, process, web, api, or watch)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "collect":
            run_collector()
        elif args.mode == "process":
            run_processor()
        elif args.mode == "web":
            run_web_interface(api_only=False)
        elif args.mode == "api":
            run_web_interface(api_only=True)
        elif args.mode == "watch":
            from watchdog.main import main as watchdog_main
            watchdog_main()
        else:  # all
            # Run collector and processor in a separate thread
            import threading
            cp_thread = threading.Thread(target=run_collector_processor)
            cp_thread.start()
            
            # Run web interface in main thread
            run_web_interface(api_only=False)
            
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise

if __name__ == "__main__":
    main() 