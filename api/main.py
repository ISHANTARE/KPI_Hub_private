"""
api/main.py
-----------
REST API service sidecar for KPI Hub powered by FastAPI.
Exposes programmatically accessible endpoints for project metrics, health statuses, and reports.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(
    title="KPI Hub REST API",
    description="Programmatic API endpoints for Engineering PMO KPI Hub Platform.",
    version="1.0.0"
)

logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str

class ProjectStatusSummary(BaseModel):
    project_id: str
    project_name: Optional[str] = None
    status: Optional[str] = None
    health_score: Optional[float] = None

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to KPI Hub REST API. Access /docs for OpenAPI documentation."}

@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected"
    }

@app.get("/api/v1/projects", response_model=List[ProjectStatusSummary], tags=["Projects"])
def get_projects(limit: int = Query(50, ge=1, le=500)):
    """Retrieve summary status for active projects."""
    try:
        from lib.database import load_dataframe_from_db
        df = load_dataframe_from_db("projects")
        if df.empty:
            return []
        
        results = []
        for _, row in df.head(limit).iterrows():
            results.append({
                "project_id": str(row.get("PROJECT_ID", "")),
                "project_name": str(row.get("PROJECT_NAME", "")),
                "status": str(row.get("STATUS", "")),
                "health_score": float(row.get("HEALTH_SCORE", 0.0)) if row.get("HEALTH_SCORE") is not None else None
            })
        return results
    except Exception as e:
        logger.exception(f"API Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving projects.")

@app.get("/api/v1/projects/{project_id}", tags=["Projects"])
def get_project_details(project_id: str):
    """Retrieve detailed KPIs for a specific project ID."""
    try:
        from lib.database import load_dataframe_from_db
        df = load_dataframe_from_db("projects")
        if df.empty:
            raise HTTPException(status_code=404, detail="Project not found.")
        
        proj_match = df[df["PROJECT_ID"] == project_id]
        if proj_match.empty:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        
        return proj_match.iloc[0].to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"API Error fetching project details for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
