from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import os
import json
import glob
from datetime import datetime
from config import STORAGE_ROOT
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
        return get_dashboard_stats()
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