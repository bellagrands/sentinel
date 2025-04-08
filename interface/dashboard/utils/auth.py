from functools import wraps
from flask import request, jsonify, current_app, redirect, url_for
from flask_login import current_user
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Callable
from database.db import db
from database.models.user import User

# Get secret key from environment or use a default for development
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'development-secret-key')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

def authenticate_user(username: str, password: str) -> Optional[str]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        User ID if authentication successful, None otherwise
    """
    try:
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.verify_password(password):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            return str(user.id)
        return None
    except Exception as e:
        db.session.rollback()
        raise

def create_token(user_id: str) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        JWT token string
    """
    try:
        user = User.query.filter_by(id=int(user_id), is_active=True).first()
        if not user:
            raise ValueError("Invalid user ID")
            
        payload = {
            'user_id': user_id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    except Exception as e:
        db.session.rollback()
        raise

def validate_token(token: str) -> Optional[str]:
    """
    Validate a JWT token and return the user ID if valid.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        # Verify user still exists and is active
        user = User.query.filter_by(id=int(user_id), is_active=True).first()
        return str(user.id) if user else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        db.session.rollback()
        return None

def require_auth(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated

def generate_token(user_id):
    """Generate a JWT token for the given user ID."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256') 