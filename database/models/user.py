from datetime import datetime
from flask_login import UserMixin
from passlib.hash import bcrypt_sha256
from database.db import db

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by their username."""
        return cls.query.filter_by(username=username).first()
    
    def set_password(self, password: str):
        """Hash and set the user's password."""
        self.password_hash = bcrypt_sha256.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify the provided password against the stored hash."""
        return bcrypt_sha256.verify(password, self.password_hash)
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        } 