# api.py
"""
Sentinel API

This module provides a REST API for accessing Sentinel data,
alerts, and analysis functionality.
"""

import os
import json
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Path, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import logging

# Import Sentinel components
from main import SentinelApp

app = FastAPI(
    title="Sentinel API",
    description="API for the Sentinel democracy watchdog system",
    version="0.1.0"
)

# Initialize Sentinel app
sentinel = SentinelApp()

# Models
class ThreatCategory(BaseModel):
    category: str
    score: float

class Alert(BaseModel):
    id: str
    timestamp: str
    source: str
    document_id: str
    title: str
    url: Optional[str] = None
    threat_score: float
    threat_categories: List[ThreatCategory]
    summary: str
    acknowledged: bool = False
    
class Document(BaseModel):
    id: str
    source_type: str
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    threat_score: Optional[float] = None
    threat_categories: Optional[Dict[str, float]] = None
    entities: Optional[Dict[str, List[str]]] = None
    analysis_timestamp: Optional[str] = None

class AnalysisRequest(BaseModel):
    text: str
    title: Optional[str] = "Submitted Document"
    
class AnalysisResponse(BaseModel):
    threat_score: float
    analysis: str
    categories: Dict[str, float]
    recommended_actions: List[str]
    
class QuestionRequest(BaseModel):
    document_id: str
    question: str

# Routes
@app.get("/")
def read_root():
    return {"message": "Sentinel API is running", "version": "0.1.0"}

@app.get("/alerts", response_model=List[Alert])
def list_alerts(acknowledged: Optional[bool] = None, limit: int = Query(10, ge=1, le=100)):
    """Get list of alerts, optionally filtered by acknowledged status."""
    alerts = []
    alert_files = glob.glob(os.path.join('alerts', '*.json'))
    
    for file_path in alert_files:
        try:
            with open(file_path, 'r') as f:
                alert = json.load(f)
                if acknowledged is None or alert.get('acknowledged', False) == acknowledged:
                    alerts.append(alert)
        except Exception as e:
            logger.error(f"Error reading alert file {file_path}: {e}")
                
    # Sort by timestamp descending and limit results
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return alerts[:limit]