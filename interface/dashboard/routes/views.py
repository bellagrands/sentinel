from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required
from ..utils.auth import require_auth, validate_token
from ..utils.stats import get_dashboard_stats
import requests
import os

views_bp = Blueprint('views', __name__)

# Use the Docker service name and port for the API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://sentinel-api:8000/api')

@views_bp.route('/')
@require_auth
def index():
    """Dashboard page."""
    # dashboard.html fetches its own data asynchronously
    return render_template('dashboard.html', page_name='dashboard')

@views_bp.route('/login')
def login():
    """Login page."""
    # If user is already logged in, redirect to dashboard
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            user_id = validate_token(token)
            if user_id:
                return redirect(url_for('views.index'))
        except:
            pass
    return_url = request.args.get('returnUrl', '/')
    return render_template('login.html', page_name='login', return_url=return_url)

@views_bp.route('/register')
def register():
    """Registration page."""
    # If user is already logged in, redirect to dashboard
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            user_id = validate_token(token)
            if user_id:
                return redirect(url_for('views.index'))
        except:
            pass
    return render_template('register.html', page_name='register')

@views_bp.route('/dashboard')
def dashboard():
    """Redirect to index for backward compatibility."""
    return index()

@views_bp.route('/alerts')
@require_auth
def alerts():
    """Alerts page."""
    # Get filter parameters
    min_score = float(request.args.get('min_score', 0.0))
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    try:
        # Get alerts from FastAPI endpoint
        response = requests.get(
            f"{API_BASE_URL}/alerts/db",
            params={
                'min_score': min_score,
                'limit': limit,
                'offset': offset
            }
        )
        alerts = response.json()
        
        return render_template(
            'alerts.html',
            page_name='alerts',
            alerts=alerts,
            min_score=min_score,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        return render_template('errors/error.html', error=str(e))

@views_bp.route('/analyze')
@require_auth
def analyze():
    """Analysis page."""
    return render_template('analyze.html', page_name='analyze')

@views_bp.route('/visualize')
@require_auth
def visualize():
    """Visualization page."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        stats = response.json()
        return render_template('visualize.html', page_name='visualize', stats=stats)
    except Exception as e:
        return render_template('errors/error.html', error=str(e))

@views_bp.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Failed to fetch stats: {response.status_code}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500 