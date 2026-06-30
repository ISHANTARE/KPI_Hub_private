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
    try:
        from lib.database import get_engine
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB ping failed: {e}")
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "1.0.0",
        "database": db_status
    }

@app.get("/api/v1/metrics", tags=["Metrics"])
def get_portfolio_metrics():
    """Retrieve computed portfolio-level KPIs and penalty metrics."""
    try:
        from lib.data_loader import load_data
        from lib.kpi_engine import calculate_kpis, compute_pm_kpis
        data = load_data()
        if not data:
            raise HTTPException(status_code=500, detail="Data loading failed.")
        kpis = calculate_kpis(data)
        pm_kpis = compute_pm_kpis(data)
        return {
            "portfolio_kpis": kpis,
            "pm_kpis": pm_kpis
        }
    except Exception as e:
        logger.exception(f"API Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving metrics.")

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

@app.get("/api/v1/financials/evm", tags=["Financials"])
def get_portfolio_evm():
    """Retrieve portfolio-level Earned Value Management (EVM) metrics."""
    try:
        from lib.data_loader import load_data
        from lib.kpi_engine import calculate_portfolio_evm
        data = load_data()
        if not data:
            raise HTTPException(status_code=500, detail="Data loading failed.")
        kpis = calculate_portfolio_evm(data)
        return {
            "portfolio_cpi": kpis.get("portfolio_cpi", 1.0),
            "portfolio_spi": kpis.get("portfolio_spi", 1.0),
            "estimate_at_completion": kpis.get("portfolio_eac", 0.0),
            "variance_at_completion": kpis.get("portfolio_vac", 0.0)
        }
    except Exception as e:
        logger.exception(f"API Error fetching EVM financials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving EVM financials.")

@app.get("/api/v1/projects/{project_id}/forecast", tags=["Financials"])
def get_project_forecast(project_id: str):
    """Retrieve predictive budget forecasts (EAC, ETC, VAC) for a specific project."""
    try:
        from lib.data_loader import load_data
        from lib.evm_engine import calculate_forecasts, calculate_evm_metrics
        data = load_data()
        if not data:
            raise HTTPException(status_code=500, detail="Data loading failed.")
        
        budget_df = data.get("budget")
        if budget_df is None or budget_df.empty:
            raise HTTPException(status_code=404, detail="Budget data unavailable.")
        
        proj_budget = budget_df[budget_df["PROJECT_ID"] == project_id]
        if proj_budget.empty:
            raise HTTPException(status_code=404, detail=f"Budget records for '{project_id}' not found.")
        
        planned_col = next((c for c in proj_budget.columns if c.lower() in ['planned','planned_amount','budget_planned','planned_value']), None)
        spent_col = next((c for c in proj_budget.columns if c.lower() in ['spent','actual','actual_spent','budget_spent','spent_amount','actual_cost']), None)
        ev_col = next((c for c in proj_budget.columns if c.lower() in ['earned_value','ev']), None)

        pv = float(proj_budget[planned_col].astype(float).sum()) if planned_col else 0.0
        ac = float(proj_budget[spent_col].astype(float).sum()) if spent_col else 0.0
        ev = float(proj_budget[ev_col].astype(float).sum()) if ev_col else (pv * 0.95)

        evm = calculate_evm_metrics(pv, ev, ac)
        forecast = calculate_forecasts(pv, ev, ac, cpi=evm["cpi"])
        return {
            "project_id": project_id,
            "evm_metrics": evm,
            "forecast": forecast
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"API Error fetching forecast for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

