import os
from database.config import DatabaseConfig

# Database configuration
SQLALCHEMY_DATABASE_URI = DatabaseConfig.get_database_url()
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key for session management
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_123')

# Storage configuration
STORAGE_ROOT = os.path.join(os.path.dirname(__file__), 'storage')
DOCUMENT_STORAGE = os.path.join(STORAGE_ROOT, 'documents') 