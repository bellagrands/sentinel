import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from database import db
from database.models import SourceConfig

def init_source_configs():
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
        config = SourceConfig(
            source_id=source['source_id'],
            name=source['name'],
            config=source['config']
        )
        db.session.add(config)
    
    db.session.commit()

if __name__ == '__main__':
    init_source_configs() 