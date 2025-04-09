#!/usr/bin/env python
"""Script to create an initial admin user."""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import db
from database.models.user import User
from interface.dashboard import create_app

def create_admin_user(username: str, email: str, password: str) -> None:
    """Create an admin user."""
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        if User.query.filter_by(username=username).first():
            print(f"User {username} already exists")
            return
            
        # Create admin user
        user = User(
            username=username,
            email=email,
            role='admin',
            is_active=True,
            is_admin=True,
            created_at=datetime.utcnow()
        )
        
        # Explicitly set the password hash using werkzeug's generate_password_hash
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        db.session.add(user)
        db.session.commit()
        print(f"Created admin user: {username}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
        
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password) 