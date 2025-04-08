from datetime import datetime
from sqlalchemy import JSON
from database.db import db

class ProcessingStatus(db.Model):
    """Status tracking for document processing jobs."""
    __tablename__ = 'processing_status'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)  # running, completed, failed
    documents_processed = db.Column(db.Integer, default=0)
    alerts_generated = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    processing_metadata = db.Column(JSON)  # Additional processing metadata

    def __init__(self, batch_id: str, status: str = 'running', processing_metadata: dict = None):
        self.batch_id = batch_id
        self.status = status
        self.processing_metadata = processing_metadata or {}
        self.start_time = datetime.utcnow()

    def complete(self, documents_processed: int, alerts_generated: int = 0):
        """Mark processing as completed."""
        self.status = 'completed'
        self.documents_processed = documents_processed
        self.alerts_generated = alerts_generated
        self.end_time = datetime.utcnow()

    def fail(self, error_message: str):
        """Mark processing as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.end_time = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'documents_processed': self.documents_processed,
            'alerts_generated': self.alerts_generated,
            'error_message': self.error_message,
            'processing_metadata': self.processing_metadata
        } 