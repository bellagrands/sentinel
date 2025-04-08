from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import os
import json
import glob
from datetime import datetime, timedelta
from config import STORAGE_ROOT
from sqlalchemy import func
from database.models import Alert, Document, Category
from database.db import get_session
from interface.dashboard.utils.stats import get_dashboard_stats, _get_alerts

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Sentinel API is running"}

@router.get("/alerts")
async def list_alerts(acknowledged: Optional[bool] = None, limit: int = 10):
    """List alerts with optional filtering by acknowledged status."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    alerts = []
    try:
        alert_files = glob.glob(os.path.join(STORAGE_ROOT, "alerts", "*.json"))
        for file_path in alert_files:
            try:
                with open(file_path, 'r') as f:
                    alert = json.load(f)
                    if acknowledged is None or alert.get('acknowledged') == acknowledged:
                        alerts.append(alert)
            except Exception as e:
                continue
        
        # Sort alerts by timestamp in descending order
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return alerts[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Mark an alert as acknowledged."""
    try:
        alert_file = os.path.join(STORAGE_ROOT, "alerts", f"{alert_id}.json")
        if not os.path.exists(alert_file):
            raise HTTPException(status_code=404, detail="Alert not found")
        
        with open(alert_file, 'r') as f:
            alert = json.load(f)
        
        alert['acknowledged'] = True
        alert['acknowledged_at'] = datetime.now().isoformat()
        
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
        
        return alert
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get dashboard statistics."""
    try:
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
        
        # Get database session
        session = get_session()
        
        try:
            # Get basic counts
            stats['total_documents'] = session.query(Document).count()
            stats['total_alerts'] = session.query(Alert).count()
            stats['high_threats'] = session.query(Alert).filter(Alert.threat_score >= 0.7).count()
            
            # Get average threat score
            avg_score = session.query(func.avg(Alert.threat_score)).scalar()
            stats['avg_threat_score'] = float(avg_score) if avg_score else 0
            
            # Get threat distribution
            for i in range(5):
                min_score = i * 0.2
                max_score = min_score + 0.2
                count = session.query(Alert).filter(
                    Alert.threat_score >= min_score,
                    Alert.threat_score < max_score
                ).count()
                stats['threat_distribution'][i] = count
            
            # Get recent alerts
            recent_alerts = session.query(Alert).order_by(Alert.created_at.desc()).limit(5).all()
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
            category_counts = session.query(
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
            
            daily_scores = session.query(
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
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/db")
async def list_db_alerts(min_score: float = 0.0, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Get alerts from the database with filtering and pagination."""
    try:
        all_alerts = _get_alerts()
        filtered_alerts = [
            alert for alert in all_alerts 
            if float(alert.get('threat_score', 0)) >= min_score
        ]
        
        # Sort by timestamp descending and paginate
        filtered_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return filtered_alerts[offset:offset + limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 