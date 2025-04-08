from flask import Flask, render_template, redirect, url_for, request, session
from flask_cors import CORS
from flask_login import LoginManager, current_user
from database.db import db, init_db
from database.models.user import User
import logging
import os
import jwt
import datetime

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "supports_credentials": True,
            "expose_headers": ["Authorization"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize database
    try:
        init_db(app)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Register blueprints
    from .routes.auth import bp as auth_bp
    from .routes.views import views_bp
    
    # Root route - redirect based on auth status
    @app.route('/')
    def index():
        """Landing page route."""
        if current_user.is_authenticated:
            return redirect(url_for('views.index'))
        return redirect(url_for('auth.login'))
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(views_bp, url_prefix='/views')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Configure app
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Enable template auto-reload
    
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=60)

    return app 