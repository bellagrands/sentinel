from flask import Blueprint, request, jsonify, make_response
from ...utils.auth import authenticate_user, create_token, require_auth
from ...database import db_session
from ...models.user import User
from email_validator import validate_email, EmailNotValidError

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
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
            
        if db_session.query(User).filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        user = User(
            username=username,
            email=email,
            role='user',
            is_active=True
        )
        user.set_password(password)
        
        db_session.add(user)
        db_session.commit()
        
        token = create_token(user.id)
        
        response = make_response(jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username
            },
            'token': token,
            'expires_in': 3600  # 1 hour
        }))
        response.headers['Authorization'] = f'Bearer {token}'
        return response
        
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

@bp.route('/login', methods=['POST'])
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
        
        user = authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        token = create_token(user)
        
        response = make_response(jsonify({
            'message': 'Login successful',
            'user': {
                'id': user,
                'username': username
            },
            'token': token,
            'expires_in': 3600  # 1 hour
        }))
        response.headers['Authorization'] = f'Bearer {token}'
        return response
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    # In a more complex implementation, you might want to invalidate the token
    # For now, we'll just return a success response since the client will remove the token
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/check', methods=['GET'])
@require_auth
def check_auth():
    # The @require_auth decorator already checks if the token is valid
    # If we get here, the token is valid
    return jsonify({'message': 'Token is valid'}) 