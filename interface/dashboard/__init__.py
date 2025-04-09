from flask import Flask, render_template, redirect, url_for, request, session
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from database.db import db, init_db
from database.config import DatabaseConfig
from .routes.views import views_bp
from .routes.auth import auth_bp
import logging
import os
import jwt
import datetime

# Set up logging
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Configure app
    app.config.update(DatabaseConfig.get_config())
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@sentinel-postgres:5432/postgres')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
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
        from database.models.user import User
        return User.query.get(int(user_id))
    
    # Initialize database
    try:
        db.init_app(app)
        migrate = Migrate(app, db)
        with app.app_context():
            init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Root route - redirect based on auth status
    @app.route('/')
    def index():
        """Landing page route."""
        if current_user.is_authenticated:
            return redirect(url_for('views.index'))
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Configure app
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Enable template auto-reload
    
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=60)
        logger.info(f"Processing request: {request.method} {request.path}")

    return app 