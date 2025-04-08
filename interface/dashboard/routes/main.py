from flask import Blueprint, render_template, send_from_directory, request, jsonify, redirect, url_for
from ..utils.auth import require_auth
import os
import jwt

bp = Blueprint('main', __name__)

@bp.route('/login')
def login():
    """Login page route."""
    # Check if user is already authenticated
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = auth_header
            # If token is valid, redirect to dashboard
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
            return redirect(url_for('main.dashboard'))
        except:
            pass
    return render_template('login.html')

@bp.route('/dashboard')
@require_auth
def dashboard():
    """Dashboard page route."""
    return render_template('dashboard.html')

@bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename) 