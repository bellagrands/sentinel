from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from ..utils.auth import authenticate_user, generate_token
from ..database import Session
from ..models.user import User
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission."""
    if request.method == 'GET':
        return render_template('login.html')
        
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
            
        user_id = authenticate_user(username, password)
        if user_id:
            token = generate_token(user_id)
            return jsonify({'token': token})
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'GET':
        return render_template('register.html')
        
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
            
        session = Session()
        try:
            # Check if username or email already exists
            if session.query(User).filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            if session.query(User).filter_by(email=email).first():
                return jsonify({'error': 'Email already exists'}), 400
                
            # Create new user
            user = User(
                username=username,
                email=email,
                role='user',
                is_active=True,
                created_at=datetime.utcnow()
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            
            # Generate token for immediate login
            token = generate_token(str(user.id))
            return jsonify({
                'message': 'Registration successful',
                'token': token
            })
            
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

@bp.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    # Frontend should remove the token
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/profile', methods=['GET', 'PUT'])
def profile():
    """Handle user profile operations."""
    if request.method == 'GET':
        session = Session()
        try:
            user = session.query(User).filter_by(id=int(request.user_id)).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            return jsonify(user.to_dict())
        finally:
            session.close()
            
    if request.method == 'PUT':
        data = request.get_json()
        session = Session()
        try:
            user = session.query(User).filter_by(id=int(request.user_id)).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            # Update allowed fields
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.set_password(data['password'])
                
            session.commit()
            return jsonify({'message': 'Profile updated successfully'})
            
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close() 