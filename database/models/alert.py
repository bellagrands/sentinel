from datetime import datetime
from database.db import db

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    threat_score = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = db.relationship('Document', back_populates='alerts')
    categories = db.relationship('Category', secondary='alert_categories', back_populates='alerts')
    
    def __init__(self, title, description, document_id, threat_score=0.0):
        self.title = title
        self.description = description
        self.document_id = document_id
        self.threat_score = threat_score
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'document_id': self.document_id,
            'threat_score': self.threat_score,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'categories': [category.to_dict() for category in self.categories]
        } 