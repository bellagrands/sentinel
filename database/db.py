from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from database.config import DatabaseConfig

class Base(DeclarativeBase):
    pass

# Create engine and session factory
engine = create_engine(DatabaseConfig.get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Get a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)
