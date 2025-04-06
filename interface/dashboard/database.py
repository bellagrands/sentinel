from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# Get database URL from environment or use SQLite for development
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./sentinel.db')

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize the database, creating all tables."""
    # Import models here to ensure they are registered with Base
    from .models.user import User
    
    Base.metadata.create_all(bind=engine)
    
    # Create admin user if it doesn't exist
    session = Session()
    try:
        admin = session.query(User).filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@sentinel.local',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            session.add(admin)
            session.commit()
    finally:
        session.close()

def get_db():
    """Get a database session."""
    session = Session()
    try:
        yield session
    finally:
        session.close() 