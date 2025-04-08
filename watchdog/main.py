#!/usr/bin/env python
"""
Sentinel Democracy Watchdog System - Watchdog Service

This script implements the watchdog service that monitors the health and performance
of the Sentinel system components and generates alerts when issues are detected.
"""

import os
import sys
import time
import json
import logging
import yaml
from datetime import datetime
from typing import Dict, Any, List
from config import STORAGE_ROOT

def setup_logger(name):
    """
    Set up a logger with console output only.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger

# Set up logging
logger = setup_logger(__name__)

class WatchdogService:
    """Service for monitoring system health and generating alerts."""
    
    def __init__(self):
        """Initialize the watchdog service."""
        self.config = self.load_config()
        self.alerts_dir = os.path.join(STORAGE_ROOT, 'alerts')
        os.makedirs(self.alerts_dir, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yml."""
        try:
            with open('/app/config.yml', 'r') as f:  # Use absolute path in Docker
                config = yaml.safe_load(f)
                logger.info("Successfully loaded configuration")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def generate_alert(self, alert_type: str, severity: str, message: str, details: Dict[str, Any] = None) -> None:
        """
        Generate and save an alert.
        
        Args:
            alert_type: Type of alert (e.g. 'system_health', 'performance')
            severity: Alert severity ('info', 'warning', 'error', 'critical')
            message: Alert message
            details: Additional alert details
        """
        alert = {
            'id': f"{int(time.time())}_{alert_type}",
            'type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'acknowledged': False
        }
        
        try:
            filename = os.path.join(self.alerts_dir, f"{alert['id']}.json")
            with open(filename, 'w') as f:
                json.dump(alert, f, indent=2)
            logger.info(f"Generated {severity} alert: {message}")
        except Exception as e:
            logger.error(f"Error saving alert: {e}")

    def check_system_health(self):
        """Check the health of various system components."""
        # Check if required directories exist
        required_dirs = [
            os.path.join(STORAGE_ROOT, 'data'),
            os.path.join(STORAGE_ROOT, 'logs'),
            os.path.join(STORAGE_ROOT, 'alerts')
        ]
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                self.generate_alert(
                    "missing_directory",
                    "error",
                    f"Required directory '{dir_name}' is missing"
                )

        # Check for recent activity in logs
        try:
            log_files = [f for f in os.listdir(os.path.join(STORAGE_ROOT, 'logs')) if f.endswith('.log')]
            for log_file in log_files:
                path = os.path.join(STORAGE_ROOT, 'logs', log_file)
                if time.time() - os.path.getmtime(path) > 3600:  # No updates in last hour
                    self.generate_alert(
                        "stale_logs",
                        "warning",
                        f"No recent updates to log file: {log_file}"
                    )
        except Exception as e:
            logger.error(f"Error checking log files: {e}")

def ensure_directories():
    """Ensure required directories exist."""
    required_dirs = [
        os.path.join(STORAGE_ROOT, 'data'),
        os.path.join(STORAGE_ROOT, 'logs'),
        os.path.join(STORAGE_ROOT, 'alerts')
    ]
    
    for directory in required_dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")

def main():
    """Main function to run the watchdog service."""
    logger.info("Starting Sentinel Watchdog Service")

    # Ensure directories exist
    ensure_directories()

    # Initialize watchdog
    watchdog = WatchdogService()

    while True:
        try:
            watchdog.check_system_health()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in watchdog service: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main() 