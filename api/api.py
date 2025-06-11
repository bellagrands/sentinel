from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import os
import json
import glob
from datetime import datetime, timedelta
from config import STORAGE_ROOT
from sqlalchemy import func
from database.models import Alert, Document, Category # Keep Alert, Document, Category if used elsewhere by router
from database.db import get_session # Keep get_session if used elsewhere by router
from interface.dashboard.utils.stats import get_dashboard_stats, _get_alerts # Keep if used by existing router
# Imports for DataSourceService
from interface.dashboard.services.data_sources import DataSourceService, DataSource, DataSourceConfig # DataSourceConfig might be used for input validation
from pydantic import BaseModel # For request body validation if needed, though DataSource and DataSourceConfig are Pydantic models

# Existing router
router = APIRouter()

# New router for Data Sources
sources_router = APIRouter(
    prefix="/sources",
    tags=["data-sources"],
)

# Initialize DataSourceService
# data_dir can be configured if it's different from default, but service has a default.
data_source_service = DataSourceService()

# Pydantic model for creating/updating a source.
# We'll use DataSource for now, but ideally, this would be a subset of fields
# that a user is allowed to configure. For example, status fields might be system-managed.
# Let's define a model that makes sense for user input, primarily based on DataSourceConfig
# but within the DataSource structure that the service expects.

class SourceInput(BaseModel):
    name: str
    # status: str # Usually system-managed
    # auth_type: str # This might be configured
    # last_update: str # System-managed
    # documents: int # System-managed
    # health_score: int # System-managed
    config: DataSourceConfig # This is the core configuration

    # Add other fields from DataSource that are user-configurable if any
    # For now, let's assume these are derived or have defaults in the service for a new source
    status: str = "configured" # Default status for a newly configured source
    status_class: str = "secondary"
    auth_type: str = "Not Configured"
    auth_class: str = "muted"
    last_update: str = "Never"
    documents: int = 0
    update_frequency: str = "N/A" # Will be derived from config.update_frequency
    health_score: int = 0 # Initial health score

# Let's make source_id a path parameter for POST, implying "create or replace"
@sources_router.post("/{source_id}", response_model=DataSource)
async def create_or_update_source_api(source_id: str, source_input: SourceInput):
    """
    Create a new data source or update an existing one using its source_id.
    This acts as an "upsert" operation for the file-based storage.
    """
    # Construct the full DataSource model from SourceInput
    # DataSourceConfig.update_frequency is an int (e.g., hours)
    # DataSource.update_frequency is a string (e.g., "1 hour", "24 hours")
    update_frequency_val = source_input.config.update_frequency
    if update_frequency_val == 1:
        update_frequency_str = "1 hour"
    elif update_frequency_val > 1:
        update_frequency_str = f"{update_frequency_val} hours"
    else: # 0 or negative, could mean "manual" or "not set"
        update_frequency_str = "N/A"


    source_data = DataSource(
        name=source_input.name,
        status=source_input.status,
        status_class=source_input.status_class,
        auth_type=source_input.auth_type,
        auth_class=source_input.auth_class,
        last_update=source_input.last_update,
        documents=source_input.documents,
        update_frequency=update_frequency_str, # This needs to be mapped from config
        health_score=source_input.health_score,
        config=source_input.config
        # recent_activity can be omitted, service might initialize it
    )

    if data_source_service.update_source(source_id, source_data):
        updated_source = data_source_service.get_source(source_id)
        if updated_source:
            return updated_source
        raise HTTPException(status_code=500, detail="Source updated but could not be retrieved.")
    raise HTTPException(status_code=500, detail="Failed to update data source.")

@sources_router.get("/", response_model=Dict[str, DataSource])
async def get_all_sources_api():
    """Get all configured data sources."""
    sources = data_source_service.get_all_sources()
    if not sources:
        # Return default sources if no custom sources are found, or an empty dict
        # The service itself returns default if data_dir is empty.
        pass
    return sources

@sources_router.get("/{source_id}", response_model=DataSource)
async def get_source_api(source_id: str):
    """Get details for a specific data source."""
    source = data_source_service.get_source(source_id)
    if source:
        return source
    raise HTTPException(status_code=404, detail=f"Data source '{source_id}' not found.")

@sources_router.delete("/{source_id}", response_model=Dict[str, str])
async def delete_source_api(source_id: str):
    """Delete a data source configuration."""
    if data_source_service.delete_source(source_id):
        return {"message": f"Data source '{source_id}' deleted successfully."}
    # If delete_source itself doesn't raise error for non-existent file,
    # we might want to check if it existed first using get_source.
    # However, delete_source in the service just removes if exists, so it's idempotent.
    # Let's assume if it returns false, it's because it couldn't delete (e.g. permissions) or didn't exist.
    # For now, if it didn't exist, os.remove wouldn't error, so service returns True.
    # To give more specific feedback, we'd check existence first.
    existing_source = data_source_service.get_source(source_id)
    if not existing_source and not os.path.exists(data_source_service._get_source_file(source_id)): # Check if file actually exists
        raise HTTPException(status_code=404, detail=f"Data source '{source_id}' not found for deletion.")

    # Corrected logic for delete:
    source_file_path = data_source_service._get_source_file(source_id)
    is_default_source_without_config = source_id in data_source_service._get_default_sources() and not os.path.exists(source_file_path)

    if not os.path.exists(source_file_path) and not is_default_source_without_config:
        raise HTTPException(status_code=404, detail=f"Data source configuration file for '{source_id}' not found.")

    if is_default_source_without_config:
        # This means it's a default source that doesn't have a custom JSON file.
        # Such sources cannot be "deleted" by removing a file.
        raise HTTPException(status_code=400, detail=f"Data source '{source_id}' is a default source and does not have a custom configuration file to delete.")

    if data_source_service.delete_source(source_id): # This will delete the file if it exists
        return {"message": f"Data source '{source_id}' deleted successfully."}
    else: # pragma: no cover
        # This path should ideally not be reached if checks above are correct.
        # delete_source returns False if os.remove fails for some reason (e.g. permissions)
        raise HTTPException(status_code=500, detail=f"Failed to delete data source '{source_id}'. This might be due to a permissions issue.")


# It's important to include this new router in the main FastAPI application instance.
# This part is usually handled in app.py or where the FastAPI app is created.
# For now, this change is only in api.py. The subtask implies modifying api.py.
# If app.py also needs modification to include sources_router, that's outside this specific file change.
# Let's assume the main app (app.py) will include this router.

# The following lines are for context if the main app is in this file, which is not typical.
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router)
# app.include_router(sources_router)

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

# The main FastAPI app instance would typically be in app.py
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router) # Existing routes
# app.include_router(sources_router) # New data source routes

# --- Router for Scrapers ---
scrapers_router = APIRouter(
    prefix="/scrapers",
    tags=["scrapers"],
)

SCRAPERS_DIR = "scrapers"
AVAILABLE_SCRAPERS = [
    f.name for f in os.scandir(SCRAPERS_DIR)
    if f.is_file() and f.name.endswith(".py") and not f.name.startswith("__init__")
]

# In-memory store for subprocesses (very basic, not for production)
# { "scraper_name": subprocess.Popen_object }
active_scraper_processes: Dict[str, subprocess.Popen] = {}


class ScraperInfo(BaseModel):
    name: str
    description: Optional[str] = None
    # Add other metadata if available, e.g. expected parameters

class ScraperRunParams(BaseModel):
    search_terms: Optional[List[str]] = None
    days_back: Optional[int] = None
    # Add other common params; specific scrapers might have unique ones.
    # For now, these are passed as command line args.
    # A more robust solution would involve per-scraper config models.

@scrapers_router.get("/", response_model=List[ScraperInfo])
async def list_available_scrapers():
    """List available scrapers."""
    scraper_infos = []
    for scraper_name_py in AVAILABLE_SCRAPERS:
        scraper_name = scraper_name_py.replace(".py", "")
        # In a real system, descriptions might come from a config file or docstrings
        scraper_infos.append(ScraperInfo(name=scraper_name, description=f"The {scraper_name} scraper."))
    return scraper_infos

@scrapers_router.post("/{scraper_name}/run", response_model=Dict[str, str])
async def run_scraper(scraper_name: str, params: Optional[ScraperRunParams] = None):
    """
    Trigger a specific scraper to run as a background process.
    """
    scraper_file_py = f"{scraper_name}.py"
    if scraper_file_py not in AVAILABLE_SCRAPERS:
        raise HTTPException(status_code=404, detail=f"Scraper '{scraper_name}' not found.")

    if scraper_name in active_scraper_processes and active_scraper_processes[scraper_name].poll() is None:
        raise HTTPException(status_code=400, detail=f"Scraper '{scraper_name}' is already running.")

    cmd = ["python", os.path.join(SCRAPERS_DIR, scraper_file_py)]
    if params:
        if params.search_terms:
            # Assuming scrapers take search terms like: --search_terms "term1" "term2"
            cmd.append("--search_terms")
            cmd.extend(params.search_terms)
        if params.days_back is not None:
            cmd.append("--days_back")
            cmd.append(str(params.days_back))
        # Add other param conversions to CLI args here

    try:
        # Using Popen for non-blocking execution.
        # stdout and stderr can be redirected to files if needed.
        process = subprocess.Popen(cmd, cwd=os.getcwd()) # Run from project root
        active_scraper_processes[scraper_name] = process
        return {"message": f"Scraper '{scraper_name}' started.", "pid": str(process.pid)}
    except Exception as e:
        active_scraper_processes.pop(scraper_name, None) # Clean up if start failed
        raise HTTPException(status_code=500, detail=f"Failed to start scraper '{scraper_name}': {str(e)}")


@scrapers_router.get("/{scraper_name}/status", response_model=Dict[str, str])
async def get_scraper_status(scraper_name: str):
    """
    Check the status of a scraper run (basic implementation).
    """
    scraper_file_py = f"{scraper_name}.py"
    if scraper_file_py not in AVAILABLE_SCRAPERS:
        raise HTTPException(status_code=404, detail=f"Scraper '{scraper_name}' not found.")

    process = active_scraper_processes.get(scraper_name)
    if process:
        poll_result = process.poll()
        if poll_result is None:
            status = "running"
            pid = str(process.pid)
            return_code = ""
        else:
            status = "completed" if poll_result == 0 else "failed"
            pid = str(process.pid)
            return_code = str(poll_result)
            active_scraper_processes.pop(scraper_name, None) # Clean up completed/failed process
        return {"scraper": scraper_name, "status": status, "pid": pid, "return_code": return_code}

    return {"scraper": scraper_name, "status": "idle", "pid": "", "return_code": ""}

# Ensure the main FastAPI app (e.g., in app.py) includes this router:
# app.include_router(scrapers_router)
import subprocess # Added for running scrapers

# app.include_router(router) # Existing routes
import random # For mock analysis

# app.include_router(sources_router) # New data source routes
# app.include_router(scrapers_router) # New scrapers routes

# --- Router for Analysis ---
# This could also be part of the main `router` or a new one.
# For simplicity, adding to the main `router` if it's defined as a general v1 router.
# If `router` is specific (e.g. to /v0 paths), a new one might be better.
# Let's assume `router` can be used. If not, will define `analysis_router = APIRouter()`.
# Using existing `router` and adding a new prefix for these types of utilities.

analysis_v1_router = APIRouter(
    prefix="/v1",
    tags=["analysis"],
)

class DocumentAnalysisRequest(BaseModel):
    text: str
    # url: Optional[str] = None # Could add URL fetching later

class Entity(BaseModel):
    name: str
    type: str
    # context: Optional[str] = None

class DocumentAnalysisResponse(BaseModel):
    threat_score: float
    categories: List[str]
    entities: List[Entity]
    summary: Optional[str] = None


@analysis_v1_router.post("/analyze_document", response_model=DocumentAnalysisResponse)
async def analyze_document_api(request_data: DocumentAnalysisRequest):
    """
    Perform mock analysis on the provided text.
    """
    if not request_data.text or not request_data.text.strip():
        raise HTTPException(status_code=400, detail="Text for analysis cannot be empty.")

    # Mock logic
    text_length = len(request_data.text)

    # Threat score based on length (simple heuristic)
    threat_score = min(1.0, text_length / 1000.0) * random.uniform(0.5, 1.0)

    # Mock categories
    possible_categories = ["Geopolitical", "Cybersecurity", "Economic", "Social Unrest", "Disinformation"]
    num_categories = random.randint(1, 3)
    categories = random.sample(possible_categories, num_categories)

    # Mock entities
    entities = []
    words = request_data.text.split()
    if text_length > 0: # Ensure there are words to pick from
        num_entities = random.randint(min(len(words),1), min(len(words), 5)) # Avoid error if less than 5 words
        entity_names = random.sample(words, min(len(words), num_entities)) # Ensure sample size doesn't exceed population
        entity_types = ["Person", "Organization", "Location", "Keyword", "Event"]
        for name in entity_names:
            entities.append(Entity(name=name, type=random.choice(entity_types)))

    # Mock summary
    summary = f"This document of {text_length} characters appears to be related to {', '.join(categories)}. " \
              f"A threat score of {threat_score:.2f} has been assigned." \
              if text_length > 0 else "Document is empty."

    return DocumentAnalysisResponse(
        threat_score=threat_score,
        categories=categories,
        entities=entities,
        summary=summary
    )

# Remember to include this new router in your main FastAPI app:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router) # General, alerts, stats
# app.include_router(sources_router)
# app.include_router(scrapers_router)
# app.include_router(analysis_v1_router) # New analysis router