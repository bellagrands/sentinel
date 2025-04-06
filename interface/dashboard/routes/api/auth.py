from flask import Blueprint, request, jsonify
from ...utils.auth import authenticate_user, generate_token
from ...database import Session
from ...models.user import User
from email_validator import validate_email, EmailNotValidError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Handle user registration."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({
                'error': 'Username, email and password required'
            }), 400

        username = data['username']
        email = data['email']
        password = data['password']
        
        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({
                'error': 'Invalid email address'
            }), 400
            
        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'error': 'Password must be at least 8 characters long'
            }), 400
            
        session = Session()
        try:
            # Check if username or email already exists
            if session.query(User).filter_by(username=username).first():
                return jsonify({
                    'error': 'Username already taken'
                }), 400
                
            if session.query(User).filter_by(email=email).first():
                return jsonify({
                    'error': 'Email already registered'
                }), 400
            
            # Create new user
            user = User(
                username=username,
                email=email,
                role='user',
                is_active=True
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            
            # Generate token for immediate login
            token = generate_token(str(user.id))
            
            return jsonify({
                'token': token,
                'expires_in': 24 * 3600,  # 24 hours in seconds
                'user': user.to_dict()
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Handle user login and return JWT token."""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'error': 'Username and password required'
            }), 400

        username = data['username']
        password = data['password']
        
        # Authenticate user
        user_id = authenticate_user(username, password)
        if not user_id:
            return jsonify({
                'error': 'Invalid credentials'
            }), 401
            
        # Generate JWT token
        token = generate_token(user_id)
        
        # Get user details
        session = Session()
        try:
            user = session.query(User).filter_by(id=int(user_id)).first()
            return jsonify({
                'token': token,
                'expires_in': 24 * 3600,  # 24 hours in seconds
                'user': user.to_dict()
            })
        finally:
            session.close()
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500 