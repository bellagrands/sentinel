from datetime import datetime
from sqlalchemy import JSON
from database.db import db

class SourceConfig(db.Model):
    """Configuration for data sources."""
    __tablename__ = 'source_configs'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    config = db.Column(JSON, nullable=False)  # Stores source-specific configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, source_id: str, name: str, config: dict, enabled: bool = True):
        self.source_id = source_id
        self.name = name
        self.config = config
        self.enabled = enabled

    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'name': self.name,
            'enabled': self.enabled,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 