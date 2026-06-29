"""
lib/baseline.py
---------------
Project Baselining and Diff Engine for ASPICE compliance.
Snapshots requirements and verification artifacts at milestone baselines
and calculates change deltas between baselines.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

def create_project_baseline(project_id: str, milestone_name: str, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Creates a formal frozen snapshot of project requirements, test cases, and risks.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    req_df = data_dict.get("requirements", pd.DataFrame())
    proj_reqs = req_df[req_df["PROJECT_ID"] == project_id].to_dict(orient="records") if not req_df.empty and "PROJECT_ID" in req_df.columns else []

    tests_df = data_dict.get("tests", pd.DataFrame())
    proj_tests = tests_df[tests_df["PROJECT_ID"] == project_id].to_dict(orient="records") if not tests_df.empty and "PROJECT_ID" in tests_df.columns else []

    baseline_snapshot = {
        "project_id": project_id,
        "milestone_name": milestone_name,
        "timestamp": timestamp,
        "requirements_count": len(proj_reqs),
        "tests_count": len(proj_tests),
        "requirements": proj_reqs,
        "tests": proj_tests
    }

    try:
        from lib.database import save_dataframe_to_db
        df_baseline = pd.DataFrame([{
            "BASELINE_ID": f"BASE_{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "PROJECT_ID": project_id,
            "MILESTONE": milestone_name,
            "TIMESTAMP": timestamp,
            "SNAPSHOT_JSON": json.dumps(baseline_snapshot)
        }])
        save_dataframe_to_db("project_baselines", df_baseline, if_exists="append")
    except Exception as e:
        logger.warning(f"Failed to persist baseline to DB: {e}")

    return baseline_snapshot

def compare_baselines(old_baseline: Dict[str, Any], new_baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two baseline snapshots and return added, removed, and modified counts."""
    old_reqs = {r.get("REQUIREMENT_ID"): r for r in old_baseline.get("requirements", []) if r.get("REQUIREMENT_ID")}
    new_reqs = {r.get("REQUIREMENT_ID"): r for r in new_baseline.get("requirements", []) if r.get("REQUIREMENT_ID")}

    added = set(new_reqs.keys()) - set(old_reqs.keys())
    removed = set(old_reqs.keys()) - set(new_reqs.keys())
    common = set(old_reqs.keys()).intersection(set(new_reqs.keys()))

    modified = [rid for rid in common if old_reqs[rid] != new_reqs[rid]]

    return {
        "added_count": len(added),
        "removed_count": len(removed),
        "modified_count": len(modified),
        "added_ids": list(added),
        "removed_ids": list(removed),
        "modified_ids": modified
    }
