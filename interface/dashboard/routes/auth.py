from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from flask_login import login_user, logout_user, login_required, current_user
from database.db import db
from database.models.user import User
from datetime import datetime
import jwt
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission."""
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    if request.method == 'GET':
        return render_template('login.html')
        
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
            
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            # Generate JWT token
            token = jwt.encode(
                {'user_id': user.id},
                os.environ.get('JWT_SECRET_KEY', 'your-secret-key'),
                algorithm='HS256'
            )
            response = make_response(jsonify({
                'message': 'Login successful',
                'user': user.to_dict(),
                'token': token
            }))
            response.headers['Authorization'] = f'Bearer {token}'
            return response
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    if request.method == 'GET':
        return render_template('register.html')
        
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
            
        try:
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            if User.query.filter_by(email=email).first():
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
            
            db.session.add(user)
            db.session.commit()
            
            # Log in the new user
            login_user(user)
            return jsonify({
                'message': 'Registration successful',
                'user': user.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """Handle user profile operations."""
    if request.method == 'GET':
        return jsonify(current_user.to_dict())
            
    if request.method == 'PUT':
        data = request.get_json()
        try:
            user = User.query.get(current_user.id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            # Update allowed fields
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.set_password(data['password'])
                
            db.session.commit()
            return jsonify({'message': 'Profile updated successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500 