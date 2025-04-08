from datetime import datetime
from sqlalchemy import JSON
from database.db import db

class Document(db.Model):
    """Document model for storing collected documents."""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(1000), nullable=False)
    content = db.Column(db.Text, nullable=True)
    source_type = db.Column(db.String(100), db.ForeignKey('source_configs.source_id'), nullable=False)
    url = db.Column(db.String(1000), nullable=True)
    raw_path = db.Column(db.String(1000), nullable=True)
    processed_path = db.Column(db.String(1000), nullable=True)
    doc_metadata = db.Column(JSON, nullable=True)
    collected_at = db.Column(db.DateTime, nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    threat_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    alerts = db.relationship('Alert', back_populates='document')
    categories = db.relationship('Category', secondary='document_categories', back_populates='documents')
    source = db.relationship('SourceConfig', backref='documents')
    
    def __init__(self, document_id: str, title: str, content: str = None, source_type: str = None,
                 url: str = None, raw_path: str = None, processed_path: str = None,
                 doc_metadata: dict = None, collected_at: datetime = None,
                 processed_at: datetime = None, threat_score: float = 0.0):
        self.document_id = document_id
        self.title = title
        self.content = content
        self.source_type = source_type
        self.url = url
        self.raw_path = raw_path
        self.processed_path = processed_path
        self.doc_metadata = doc_metadata or {}
        self.collected_at = collected_at
        self.processed_at = processed_at
        self.threat_score = threat_score
    
    def mark_processed(self, threat_score: float = None):
        """Mark document as processed with optional threat score update."""
        self.processed_at = datetime.utcnow()
        if threat_score is not None:
            self.threat_score = threat_score
    
    def to_dict(self) -> dict:
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'title': self.title,
            'content': self.content,
            'source_type': self.source_type,
            'url': self.url,
            'raw_path': self.raw_path,
            'processed_path': self.processed_path,
            'doc_metadata': self.doc_metadata,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'threat_score': self.threat_score,
            'categories': [category.to_dict() for category in self.categories]
        } 