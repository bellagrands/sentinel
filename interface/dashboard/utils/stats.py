"""Utility functions for gathering dashboard statistics."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import Counter, defaultdict
from sqlalchemy import func
from database.models import Alert, Document, Category
from database.db import db
from config import DOCUMENT_STORAGE

def get_dashboard_stats() -> Dict[str, Any]:
    """Get statistics for the dashboard."""
    stats = {
        'total_documents': 0,
        'total_alerts': 0,
        'high_threats': 0,
        'avg_threat_score': 0,
        'recent_alerts': [],
        'threat_distribution': [0, 0, 0, 0, 0],
        'top_categories': [],
        'threat_timeline': []
    }
    
    # Get basic counts
    stats['total_documents'] = Document.query.count()
    stats['total_alerts'] = Alert.query.count()
    stats['high_threats'] = Alert.query.filter(Alert.threat_score >= 0.7).count()
    
    # Get average threat score
    avg_score = db.session.query(func.avg(Alert.threat_score)).scalar()
    stats['avg_threat_score'] = float(avg_score) if avg_score else 0
    
    # Get threat distribution
    for i in range(5):
        min_score = i * 0.2
        max_score = min_score + 0.2
        count = Alert.query.filter(
            Alert.threat_score >= min_score,
            Alert.threat_score < max_score
        ).count()
        stats['threat_distribution'][i] = count
    
    # Get recent alerts
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    stats['recent_alerts'] = [
        {
            'date': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'title': alert.title,
            'source_type': alert.document.source if alert.document else 'Unknown',
            'threat_score': alert.threat_score,
            'document_id': alert.document_id,
            'categories': [
                {
                    'name': category.name,
                    'score': 1.0  # We don't store category scores in the DB
                }
                for category in alert.categories
            ]
        }
        for alert in recent_alerts
    ]
    
    # Get top categories
    category_counts = db.session.query(
        Category.name,
        func.count(Category.id).label('count')
    ).join(
        Alert.categories
    ).group_by(
        Category.name
    ).order_by(
        func.count(Category.id).desc()
    ).limit(5).all()
    
    stats['top_categories'] = [
        {'category': name, 'score': count}
        for name, count in category_counts
    ]
    
    # Get threat timeline
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    daily_scores = db.session.query(
        func.date(Alert.created_at).label('date'),
        func.avg(Alert.threat_score).label('avg_score')
    ).filter(
        Alert.created_at >= start_date
    ).group_by(
        func.date(Alert.created_at)
    ).all()
    
    # Convert to dict for easier lookup
    score_by_date = {
        date.strftime('%Y-%m-%d'): float(avg_score)
        for date, avg_score in daily_scores
    }
    
    # Fill in missing dates
    timeline = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        timeline.append({
            'date': date_str,
            'avg_score': score_by_date.get(date_str, 0)
        })
        current_date += timedelta(days=1)
    
    stats['threat_timeline'] = timeline
    
    return stats

def _get_alerts() -> List[Dict[str, Any]]:
    """Get all alerts from the database."""
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return [
        {
            'id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'document_id': alert.document_id,
            'threat_score': alert.threat_score,
            'is_active': alert.is_active,
            'timestamp': alert.created_at.isoformat(),
            'categories': [
                {
                    'category': category.name,
                    'score': 1.0  # We don't store category scores in the DB
                }
                for category in alert.categories
            ]
        }
        for alert in alerts
    ]

def _count_documents() -> int:
    """Count total documents from all sources."""
    total = 0
    
    # Count documents in storage
    for source_dir in ['pacer', 'congress', 'federal_register', 'state_legislature']:
        source_path = os.path.join(DOCUMENT_STORAGE, source_dir)
        if os.path.exists(source_path):
            for root, _, files in os.walk(source_path):
                total += sum(1 for f in files if f.endswith('.json'))
            
    return total

def _calculate_threat_trend(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate threat trend over the last 30 days."""
    trend = []
    today = datetime.now()
    
    # Initialize counts for last 30 days
    for i in range(30):
        date = today - timedelta(days=i)
        trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': 0
        })
        
    # Count alerts per day
    for alert in alerts:
        try:
            alert_date = datetime.fromisoformat(alert.get('timestamp', '')).date()
            days_ago = (today.date() - alert_date).days
            
            if 0 <= days_ago < 30:
                trend[days_ago]['count'] += 1
        except Exception:
            continue
            
    # Reverse to get chronological order
    return list(reversed(trend))