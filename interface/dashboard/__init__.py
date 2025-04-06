from flask import Flask, redirect, url_for
from flask_cors import CORS
from .routes.api.data_sources.pacer import pacer_bp
from .routes.api.data_sources.congress import congress_bp
from .routes.views import views_bp
from .routes.api.analyze import analyze_bp
from .routes.api.auth import auth_bp
from .database import init_db
from .utils.auth import require_auth

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(pacer_bp, url_prefix='/api/data_sources/pacer')
    app.register_blueprint(congress_bp, url_prefix='/api/data_sources/congress')
    app.register_blueprint(analyze_bp)
    app.register_blueprint(auth_bp)
    
    # Redirect root to login if not authenticated
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Protected dashboard route
    @app.route('/dashboard')
    @require_auth
    def dashboard():
        return render_template('dashboard.html')
    
    return app 