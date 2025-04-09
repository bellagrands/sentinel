from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from flask_sqlalchemy import SQLAlchemy
from database.config import DatabaseConfig

# Create SQLAlchemy base class for models
Base = declarative_base()

# Create Flask-SQLAlchemy instance for Flask app
db = SQLAlchemy()

# Create SQLAlchemy engine and session factory for FastAPI
engine = create_engine(DatabaseConfig.get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Get a database session for FastAPI."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Initialize database for Flask."""
    Base.metadata.create_all(bind=engine)
