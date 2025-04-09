from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Document(Base):
    """Document model."""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(512))
    source_type = Column(String(50))
    collection_date = Column(DateTime, default=datetime.utcnow)
    processed_date = Column(DateTime)
    threat_score = Column(Float, default=0.0)
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Relationships
    category = relationship("Category", back_populates="documents")
    alerts = relationship("Alert", back_populates="document")

    def __repr__(self):
        """String representation."""
        return f'<Document {self.title}>'

    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source_url': self.source_url,
            'source_type': self.source_type,
            'collection_date': self.collection_date.isoformat() if self.collection_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'threat_score': self.threat_score,
            'category_id': self.category_id,
            'category': self.category.name if self.category else None
        } 