from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()

def init_db(app):
    """Initialize the database with the Flask app."""
    from database.config import DatabaseConfig
    
    # Configure database
    app.config.update(DatabaseConfig.get_config())
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
