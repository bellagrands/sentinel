from functools import wraps
from flask import request, jsonify, current_app
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Callable
from ..database import Session
from ..models.user import User

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
    session = Session()
    try:
        user = session.query(User).filter_by(username=username, is_active=True).first()
        if user and user.verify_password(password):
            # Update last login time
            user.last_login = datetime.utcnow()
            session.commit()
            return str(user.id)
        return None
    finally:
        session.close()

def generate_token(user_id: str) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        JWT token string
    """
    session = Session()
    try:
        user = session.query(User).filter_by(id=int(user_id), is_active=True).first()
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
    finally:
        session.close()

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
        session = Session()
        try:
            user = session.query(User).filter_by(id=int(user_id), is_active=True).first()
            return str(user.id) if user else None
        finally:
            session.close()
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def require_auth(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
            
        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(' ')[1]
            # Verify and decode token
            user_id = validate_token(token)
            if not user_id:
                return jsonify({'error': 'Invalid or expired token'}), 401
                
            # Add user_id to request context
            request.user_id = user_id
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 401
            
    return decorated 