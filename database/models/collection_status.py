from datetime import datetime
from sqlalchemy import JSON
from database.db import db

class CollectionStatus(db.Model):
    """Status tracking for document collection jobs."""
    __tablename__ = 'collection_status'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(50), db.ForeignKey('source_configs.source_id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)  # running, completed, failed
    documents_collected = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    collection_metadata = db.Column(JSON)  # Additional collection metadata

    def __init__(self, source_id: str, status: str = 'running', collection_metadata: dict = None):
        self.source_id = source_id
        self.status = status
        self.collection_metadata = collection_metadata or {}
        self.start_time = datetime.utcnow()

    def complete(self, documents_collected: int):
        """Mark collection as completed."""
        self.status = 'completed'
        self.documents_collected = documents_collected
        self.end_time = datetime.utcnow()

    def fail(self, error_message: str):
        """Mark collection as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.end_time = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'documents_collected': self.documents_collected,
            'error_message': self.error_message,
            'collection_metadata': self.collection_metadata
        } 