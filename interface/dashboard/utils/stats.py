"""Utility functions for gathering dashboard statistics."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import Counter, defaultdict

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
    
    alerts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'alerts')
    if not os.path.exists(alerts_dir):
        return stats

    # Initialize counters
    total_threat_score = 0
    category_counter = Counter()
    timeline_data = defaultdict(list)
    
    # Process each alert file
    for filename in os.listdir(alerts_dir):
        if not filename.endswith('.json'):
            continue
            
        with open(os.path.join(alerts_dir, filename), 'r') as f:
            try:
                alert = json.load(f)
                
                # Count documents and alerts
                stats['total_documents'] += 1
                stats['total_alerts'] += 1
                
                # Process threat score
                threat_score = float(alert.get('threat_score', 0))
                total_threat_score += threat_score
                
                # Count high threats
                if threat_score >= 0.7:
                    stats['high_threats'] += 1
                    
                # Update threat distribution
                distribution_index = min(int(threat_score * 5), 4)
                stats['threat_distribution'][distribution_index] += 1
                
                # Count categories
                for category_obj in alert.get('threat_categories', []):
                    category = category_obj.get('category', '')
                    score = float(category_obj.get('score', 0))
                    if category and score > 0:
                        category_counter[category] += score
                    
                # Add to timeline data
                alert_date = datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d')
                timeline_data[alert_date].append(threat_score)
                
                # Format recent alert
                formatted_alert = {
                    'date': datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    'title': alert.get('title', 'Untitled'),
                    'source_type': alert.get('source', 'Unknown'),
                    'threat_score': threat_score,
                    'document_id': alert.get('document_id', ''),
                    'categories': [
                        {
                            'name': cat['category'],
                            'score': cat['score']
                        }
                        for cat in alert.get('threat_categories', [])
                    ]
                }
                stats['recent_alerts'].append(formatted_alert)
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error processing {filename}: {e}")
                continue
    
    # Calculate average threat score
    if stats['total_alerts'] > 0:
        stats['avg_threat_score'] = total_threat_score / stats['total_alerts']
    
    # Sort and format recent alerts
    stats['recent_alerts'] = sorted(
        stats['recent_alerts'],
        key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'),
        reverse=True
    )[:5]
    
    # Get top categories
    stats['top_categories'] = [
        {'category': category, 'score': score}
        for category, score in category_counter.most_common(5)
    ]
    
    # Format timeline data
    timeline = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        scores = timeline_data.get(date_str, [])
        avg_score = sum(scores) / len(scores) if scores else 0
        timeline.append({
            'date': date_str,
            'avg_score': avg_score
        })
        current_date += timedelta(days=1)
    
    stats['threat_timeline'] = timeline
    
    return stats

def _count_documents() -> int:
    """Count total documents from all sources."""
    total = 0
    
    # Count PACER documents
    pacer_dir = os.path.join('data', 'pacer')
    if os.path.exists(pacer_dir):
        for root, _, files in os.walk(pacer_dir):
            total += sum(1 for f in files if f.endswith('.json'))
            
    # Count Congress.gov documents
    congress_dir = os.path.join('data', 'congress')
    if os.path.exists(congress_dir):
        for root, _, files in os.walk(congress_dir):
            total += sum(1 for f in files if f.endswith('.json'))
            
    return total

def _get_alerts() -> List[Dict[str, Any]]:
    """Get all alerts from the alerts directory."""
    alerts = []
    alerts_dir = 'alerts'
    
    if os.path.exists(alerts_dir):
        for root, _, files in os.walk(alerts_dir):
            for file in files:
                if not file.endswith('.json'):
                    continue
                    
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        alert = json.load(f)
                        alerts.append(alert)
                except Exception as e:
                    print(f"Error reading alert file {file}: {e}")
                    continue
                    
    return alerts

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