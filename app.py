from flask import Flask
from flask_migrate import Migrate
from database.db import db, init_db
from database.models import SourceConfig
import click

app = Flask(__name__)
app.config.from_object('config')

init_db(app)
migrate = Migrate(app, db)

@app.cli.command('init-sources')
def init_sources():
    """Initialize source configurations in the database."""
    sources = [
        {
            'source_id': 'congress',
            'name': 'Congress.gov',
            'config': {
                'days_back': 30,
                'keywords': ['cybersecurity', 'cyber security', 'data breach', 'ransomware']
            }
        },
        {
            'source_id': 'federal_register',
            'name': 'Federal Register',
            'config': {
                'days_back': 30,
                'keywords': ['cybersecurity', 'cyber security', 'data breach', 'ransomware']
            }
        },
        {
            'source_id': 'pacer',
            'name': 'PACER',
            'config': {
                'days_back': 30,
                'keywords': ['cybersecurity', 'cyber security', 'data breach', 'ransomware']
            }
        },
        {
            'source_id': 'state_legislature',
            'name': 'State Legislature',
            'config': {
                'days_back': 30,
                'keywords': ['cybersecurity', 'cyber security', 'data breach', 'ransomware'],
                'states': ['CA', 'NY', 'TX', 'FL']
            }
        }
    ]

    for source in sources:
        existing = SourceConfig.query.filter_by(source_id=source['source_id']).first()
        if existing:
            existing.name = source['name']
            existing.config = source['config']
            click.echo(f"Updated configuration for {source['source_id']}")
        else:
            config = SourceConfig(
                source_id=source['source_id'],
                name=source['name'],
                config=source['config']
            )
            db.session.add(config)
            click.echo(f"Created configuration for {source['source_id']}")
    
    db.session.commit()
    click.echo('Source configurations initialized successfully.') 