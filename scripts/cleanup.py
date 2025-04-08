import os
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_and_cleanup():
    """Backup old data and clean up directories."""
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'data_backup_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    
    # List of old directories to clean up
    old_dirs = [
        'data/congress',
        'data/federal_register',
        'data/state_legislature',
        'data/pacer',
        'data/documents',
        'data/sources',
        'data/analyzed',
        'data/alerts',
        'data/local_government'
    ]
    
    # Old files to clean up
    old_files = [
        'data/sentinel.db',
        'data/last_collection.txt',
        'data/processor_last_run.txt',
        'data/collector_last_run.txt'
    ]
    
    try:
        # Backup and remove directories
        for dir_path in old_dirs:
            if os.path.exists(dir_path):
                # Create corresponding backup directory
                backup_path = os.path.join(backup_dir, os.path.basename(dir_path))
                if os.path.exists(dir_path):
                    logger.info(f"Backing up {dir_path} to {backup_path}")
                    shutil.copytree(dir_path, backup_path)
                    logger.info(f"Removing {dir_path}")
                    shutil.rmtree(dir_path)
        
        # Backup and remove files
        for file_path in old_files:
            if os.path.exists(file_path):
                # Copy to backup directory
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                logger.info(f"Backing up {file_path} to {backup_path}")
                shutil.copy2(file_path, backup_path)
                logger.info(f"Removing {file_path}")
                os.remove(file_path)
        
        # Remove data directory if empty
        if os.path.exists('data') and not os.listdir('data'):
            logger.info("Removing empty data directory")
            os.rmdir('data')
            
        logger.info("Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

if __name__ == '__main__':
    backup_and_cleanup() 