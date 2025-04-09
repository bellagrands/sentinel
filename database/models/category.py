from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

# Association tables
document_categories = Table(
    'document_categories',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

alert_categories = Table(
    'alert_categories',
    Base.metadata,
    Column('alert_id', Integer, ForeignKey('alerts.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Category(Base):
    """Category model."""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="category")
    alerts = relationship("Alert", back_populates="category")

    def __repr__(self):
        """String representation."""
        return f'<Category {self.name}>'

    def to_dict(self):
        """Convert category to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 