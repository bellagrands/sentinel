import os
from flask.cli import FlaskGroup
from interface.dashboard import create_app

os.environ['FLASK_APP'] = 'interface.dashboard:create_app'
cli = FlaskGroup(create_app=create_app)

@cli.command()
def create_admin():
    """Create admin user if it doesn't exist."""
    app = create_app()
    with app.app_context():
        from database.models.user import User
        from database.db import db
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@sentinel.local',
                is_admin=True
            )
            admin.set_password('admin')  # You should change this in production
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    cli() 