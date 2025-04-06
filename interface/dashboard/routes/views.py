from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from ..utils.auth import require_auth
from ..utils.stats import get_dashboard_stats, _get_alerts

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
@require_auth
def index():
    """Dashboard page."""
    try:
        stats = get_dashboard_stats()
        return render_template('index.html', stats=stats, page_name='dashboard')
    except Exception as e:
        return render_template('error.html', error=str(e))

@views_bp.route('/login')
def login():
    """Login page."""
    # If user is already logged in, redirect to dashboard
    if request.headers.get('Authorization'):
        return redirect(url_for('views.index'))
    return_url = request.args.get('returnUrl', '/')
    return render_template('login.html', page_name='login', return_url=return_url)

@views_bp.route('/register')
def register():
    """Registration page."""
    # If user is already logged in, redirect to dashboard
    if request.headers.get('Authorization'):
        return redirect(url_for('views.index'))
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
    
    # Get all alerts and filter them
    all_alerts = _get_alerts()
    filtered_alerts = [
        alert for alert in all_alerts 
        if float(alert.get('threat_score', 0)) >= min_score
    ]
    
    # Sort by timestamp descending and paginate
    filtered_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    paginated_alerts = filtered_alerts[offset:offset + limit]
    
    return render_template(
        'alerts.html',
        page_name='alerts',
        alerts=paginated_alerts,
        min_score=min_score,
        limit=limit,
        offset=offset
    )

@views_bp.route('/analyze')
@require_auth
def analyze():
    """Analysis page."""
    return render_template('analyze.html', page_name='analyze')

@views_bp.route('/visualize')
@require_auth
def visualize():
    """Visualization page."""
    stats = get_dashboard_stats()
    return render_template('visualize.html', page_name='visualize', stats=stats)

@views_bp.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    return jsonify(get_dashboard_stats()) 