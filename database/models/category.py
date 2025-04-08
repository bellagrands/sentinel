from database.db import db

# Association tables
document_categories = db.Table('document_categories',
    db.Column('document_id', db.Integer, db.ForeignKey('documents.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
)

alert_categories = db.Table('alert_categories',
    db.Column('alert_id', db.Integer, db.ForeignKey('alerts.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(500))
    
    # Relationships
    documents = db.relationship('Document', secondary=document_categories, back_populates='categories')
    alerts = db.relationship('Alert', secondary=alert_categories, back_populates='categories')
    
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        } 