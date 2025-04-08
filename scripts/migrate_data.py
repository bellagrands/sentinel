import os
import json
import yaml
import shutil
from datetime import datetime
import logging
from typing import Dict, Any, List
import sys

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import db
from database.models import Document, SourceConfig
from interface.dashboard import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_source_configs() -> List[Dict[str, Any]]:
    """Load source configurations from config.yml."""
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
            sources = []
            
            # Extract source configurations
            collection_config = config.get('collection', {})
            for source in collection_config.get('sources', []):
                source_type = source.get('type')
                if source_type:
                    sources.append({
                        'source_id': source_type,
                        'name': source_type.replace('_', ' ').title(),
                        'enabled': True,
                        'config': source
                    })
            
            return sources
    except Exception as e:
        logger.error(f"Error loading source configs: {e}")
        return []

def migrate_documents(source_id: str, old_dir: str, new_dir: str) -> int:
    """Migrate documents from old to new storage structure.
    
    Args:
        source_id: Source identifier
        old_dir: Old data directory
        new_dir: New storage directory
        
    Returns:
        int: Number of documents migrated
    """
    migrated_count = 0
    
    try:
        # Ensure old directory exists
        if not os.path.exists(old_dir):
            logger.warning(f"Old directory does not exist: {old_dir}")
            return 0
            
        # Create new directory
        os.makedirs(new_dir, exist_ok=True)
        
        # Process all JSON files
        for filename in os.listdir(old_dir):
            if not filename.endswith('.json'):
                continue
                
            old_path = os.path.join(old_dir, filename)
            
            try:
                # Load document
                with open(old_path, 'r') as f:
                    doc_data = json.load(f)
                
                # Generate document ID if not present
                if 'document_id' not in doc_data:
                    doc_data['document_id'] = f"{source_id}_{filename.replace('.json', '')}"
                
                # Create document model
                doc = Document(
                    document_id=doc_data['document_id'],
                    title=doc_data.get('title', 'Untitled'),
                    content=doc_data.get('content', ''),
                    source_type=source_id,
                    url=doc_data.get('url'),
                    doc_metadata=doc_data.get('metadata', {})
                )
                
                # Save to database
                db.session.add(doc)
                
                # Copy file to new location
                new_path = os.path.join(new_dir, f"{doc_data['document_id']}.json")
                shutil.copy2(old_path, new_path)
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Error migrating document {filename}: {e}")
                continue
        
        # Commit all changes
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error migrating documents for {source_id}: {e}")
        db.session.rollback()
    
    return migrated_count

def main():
    """Main migration function."""
    # Initialize Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Define source directories to migrate
            sources_to_migrate = [
                ('pacer', 'data/pacer', 'storage/documents/pacer'),
                ('congress', 'data/congress', 'storage/documents/congress'),
                ('federal_register', 'data/federal_register', 'storage/documents/federal_register'),
                ('state_legislature', 'data/state_legislature', 'storage/documents/state_legislature')
            ]
            
            # Migrate each source
            total_migrated = 0
            for source_id, old_dir, new_dir in sources_to_migrate:
                migrated = migrate_documents(source_id, old_dir, new_dir)
                total_migrated += migrated
                logger.info(f"Migrated {migrated} documents for {source_id}")
            
            logger.info(f"Migration complete. Total documents migrated: {total_migrated}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()

if __name__ == '__main__':
    main() 