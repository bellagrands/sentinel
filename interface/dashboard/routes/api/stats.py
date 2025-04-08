from flask import Blueprint, jsonify
from ...utils.auth import require_auth
from ...database import db_session
from ...models.document import Document
from ...models.alert import Alert
from ...models.category import Category
from datetime import datetime, timedelta
import random  # Temporary for demo data

bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@bp.route('', methods=['GET'])
@require_auth
def get_stats():
    """Get dashboard statistics."""
    try:
        # For demo purposes, we'll generate some sample data
        # In production, this would be replaced with actual database queries
        
        # Sample data for stats
        total_documents = random.randint(1000, 5000)
        active_alerts = random.randint(50, 200)
        high_threats = random.randint(10, 50)
        avg_threat_score = random.uniform(0.3, 0.7)
        
        # Sample data for threat timeline
        today = datetime.now()
        threat_timeline = []
        for i in range(7):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            threat_timeline.append({
                'date': date,
                'score': random.uniform(0.2, 0.8)
            })
        threat_timeline.reverse()
        
        # Sample data for threat categories
        threat_categories = [
            {'name': 'Disinformation', 'count': random.randint(50, 200)},
            {'name': 'Hate Speech', 'count': random.randint(30, 150)},
            {'name': 'Manipulation', 'count': random.randint(20, 100)},
            {'name': 'Propaganda', 'count': random.randint(40, 180)},
            {'name': 'Other', 'count': random.randint(10, 50)}
        ]
        
        # Sample data for recent alerts
        recent_alerts = []
        for i in range(10):
            alert = {
                'id': i + 1,
                'date': (today - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d'),
                'title': f'Alert {i + 1}: Potential threat detected',
                'source': random.choice(['Twitter', 'Facebook', 'News', 'Forum']),
                'threat_score': random.uniform(0.2, 0.9),
                'categories': [
                    {'name': cat['name']} 
                    for cat in random.sample(threat_categories, random.randint(1, 3))
                ]
            }
            recent_alerts.append(alert)
        
        # Sort alerts by date
        recent_alerts.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'total_documents': total_documents,
            'active_alerts': active_alerts,
            'high_threats': high_threats,
            'avg_threat_score': avg_threat_score,
            'threat_timeline': threat_timeline,
            'threat_categories': threat_categories,
            'recent_alerts': recent_alerts
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch dashboard statistics',
            'details': str(e)
        }), 500 