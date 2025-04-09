from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.db import Base

class Alert(Base):
    """Alert model."""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    threat_level = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))

    # Relationships
    document = relationship("Document", back_populates="alerts")
    category = relationship("Category", back_populates="alerts")

    def __repr__(self):
        """String representation."""
        return f'<Alert {self.title}>'

    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'threat_level': self.threat_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'document_id': self.document_id,
            'category_id': self.category_id,
            'document': self.document.to_dict() if self.document else None,
            'category': self.category.name if self.category else None
        } 