"""
lib/database.py
---------------
SQLite Database Layer using SQLAlchemy.
Provides seamless synchronization between CSV files (as work artifacts)
and SQLite (as operational truth for dashboards).
"""

import os
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DB_PATH = Path("data/kpihub.db")
ENGINE = None

def get_engine():
    global ENGINE
    if ENGINE is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return ENGINE

def init_db():
    """Ensure DB engine is created and ready."""
    return get_engine()

def save_dataframe_to_db(table_name: str, df: pd.DataFrame, if_exists: str = "replace"):
    """Save a pandas DataFrame to SQLite table."""
    if df is None or df.empty:
        return
    engine = get_engine()
    with engine.begin() as conn:
        df.to_sql(table_name, con=conn, if_exists=if_exists, index=False)
    logger.info(f"Saved {len(df)} rows to table '{table_name}' in SQLite DB.")

def load_dataframe_from_db(table_name: str) -> pd.DataFrame:
    """Load a pandas DataFrame from SQLite table."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_table(table_name, con=conn)
            return df
    except Exception as e:
        logger.warning(f"Could not load table '{table_name}' from DB: {e}")
        return pd.DataFrame()

def sync_all_csvs_to_db(force: bool = False):
    """
    Scans runtime CSV files in data/ and imports them to SQLite if table doesn't exist or force=True.
    """
    data_dir = Path("data")
    engine = get_engine()
    
    csv_mapping = {
        "projects": data_dir / "projects" / "projects_status.csv",
        "milestones": data_dir / "projects" / "milestones.csv",
        "budget": data_dir / "projects" / "budget_tracking.csv",
        "risks": data_dir / "risks" / "risk_register.csv",
        "resources": data_dir / "resources" / "resource_allocation.csv",
        "monthly_utilization": data_dir / "resources" / "monthly_utilization.csv",
        "cost_rates": data_dir / "resources" / "cost_rates.csv",
        "defects": data_dir / "metrics" / "defects.csv",
        "tests": data_dir / "metrics" / "test_execution.csv",
        "requirements": data_dir / "metrics" / "requirements.csv",
        "issues": data_dir / "projects" / "issues.csv",
        "escalations": data_dir / "projects" / "escalations.csv",
        "aspice": data_dir / "metrics" / "aspice_status.csv",
        "ecrs": data_dir / "projects" / "ecrs.csv",
        "forecast": data_dir / "resources" / "forecast.csv",
        "audit_log": data_dir / "resources" / "rebalancing_audit_log.csv",
        "decisions": data_dir / "projects" / "decisions.csv",
        "defect_trends": data_dir / "metrics" / "defect_trends.csv",
        "dev_metrics": data_dir / "metrics" / "development_metrics.csv",
        "design_reviews": data_dir / "metrics" / "design_reviews.csv",
        "verification": data_dir / "metrics" / "verification_activities.csv",
        "org_mapping": data_dir / "resources" / "org_mapping.csv",
        "actions": data_dir / "projects" / "action_log.csv",
    }

    with engine.connect() as conn:
        existing_tables = set(engine.table_names() if hasattr(engine, 'table_names') else 
                              [row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))])

    for table_name, csv_path in csv_mapping.items():
        if csv_path.exists():
            if force or table_name not in existing_tables:
                try:
                    df = pd.read_csv(csv_path)
                    save_dataframe_to_db(table_name, df, if_exists="replace")
                except Exception as e:
                    logger.error(f"Failed to sync {csv_path} to DB: {e}")
