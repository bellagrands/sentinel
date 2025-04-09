from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database.db import db, Base
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """User model."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    role = Column(String(20), default='user')
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """String representation."""
        return f'<User {self.username}>'
    
    def verify_password(self, password):
        """Verify password (alias for check_password)."""
        return self.check_password(password)
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by their username."""
        return cls.query.filter_by(username=username).first()

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }