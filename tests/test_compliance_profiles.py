import pytest
import pandas as pd
import yaml
from pathlib import Path
from lib.profile_loader import get_active_profile
from lib.kpi_engine import calculate_kpis
from lib.knowledge_base import search_knowledge_base

class ConfigProfileOverride:
    """Context manager to temporarily override general.compliance_profile in config.yaml."""
    def __init__(self, profile_name):
        self.profile_name = profile_name
        self.config_path = Path("integrations/config.yaml")
        self.original_content = None

    def __enter__(self):
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()
            try:
                cfg = yaml.safe_load(self.original_content) or {}
            except Exception:
                cfg = {}
            if "general" not in cfg:
                cfg["general"] = {}
            cfg["general"]["compliance_profile"] = self.profile_name
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_content is not None:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(self.original_content)

def test_profile_loader_default():
    """Verify that default profile loading retrieves automotive configuration."""
    with ConfigProfileOverride("automotive"):
        profile = get_active_profile(force_reload=True)
        assert profile is not None
        assert "Automotive" in profile["name"]
        assert profile["labels"]["requirements"] == "ASPICE Requirement"

def test_profile_loader_aerospace():
    """Verify that aerospace profile is loaded successfully when configured."""
    with ConfigProfileOverride("aerospace"):
        profile = get_active_profile(force_reload=True)
        assert profile is not None
        assert "Aerospace" in profile["name"]
        assert profile["labels"]["requirements"] == "DO-178C HLR/LLR Requirement"

def test_profile_loader_fallback():
    """Verify that loader falls back to automotive if configured profile doesn't exist."""
    with ConfigProfileOverride("invalid_profile_xyz"):
        profile = get_active_profile(force_reload=True)
        assert profile is not None
        assert "Automotive" in profile["name"]

def test_kpi_penalties_automotive():
    """Verify that KPI overallocation penalties match automotive values (Safety = 4.0)."""
    resources_df = pd.DataFrame([
        {"TEAM_MEMBER": "Jane Doe", "ROLE": "Safety Architect", "UTILIZATION_PCT": "130%"}
    ])
    data = {
        "projects": pd.DataFrame([{"HEALTH_SCORE": 100.0, "SCHEDULE_STATUS": "GREEN", "STATUS": "In Progress"}]),
        "risks": pd.DataFrame(),
        "defects": pd.DataFrame(),
        "tests": pd.DataFrame([{"STATUS": "PASSED"}]),
        "resources": resources_df,
        "traceability_insights": pd.DataFrame()
    }
    
    with ConfigProfileOverride("automotive"):
        get_active_profile(force_reload=True)
        kpis = calculate_kpis(data)
        # Base release readiness = 100.0 (health 100 * test pass 100)
        # Safety overallocation penalty = 4.0
        # Expected readiness = 100.0 - 4.0 = 96.0
        assert kpis["release_readiness"] == 96.0

def test_kpi_penalties_aerospace():
    """Verify that KPI overallocation penalties match aerospace values (Safety = 6.0)."""
    resources_df = pd.DataFrame([
        {"TEAM_MEMBER": "Jane Doe", "ROLE": "Safety Architect", "UTILIZATION_PCT": "130%"}
    ])
    data = {
        "projects": pd.DataFrame([{"HEALTH_SCORE": 100.0, "SCHEDULE_STATUS": "GREEN", "STATUS": "In Progress"}]),
        "risks": pd.DataFrame(),
        "defects": pd.DataFrame(),
        "tests": pd.DataFrame([{"STATUS": "PASSED"}]),
        "resources": resources_df,
        "traceability_insights": pd.DataFrame()
    }
    
    with ConfigProfileOverride("aerospace"):
        get_active_profile(force_reload=True)
        kpis = calculate_kpis(data)
        # Base release readiness = 100.0 (health 100 * test pass 100)
        # Safety overallocation penalty = 6.0
        # Expected readiness = 100.0 - 6.0 = 94.0
        assert kpis["release_readiness"] == 94.0

def test_knowledge_base_search_by_profile():
    """Verify search returns correct entries according to the active compliance profile."""
    # Under automotive profile
    with ConfigProfileOverride("automotive"):
        get_active_profile(force_reload=True)
        res_auto = search_knowledge_base("ASIL")
        assert len(res_auto) > 0
        assert res_auto[0]["standard"] == "ISO 26262"
        
        res_none = search_knowledge_base("DO-178C")
        assert len(res_none) == 0

    # Under aerospace profile
    with ConfigProfileOverride("aerospace"):
        get_active_profile(force_reload=True)
        res_aero = search_knowledge_base("DO-178C")
        assert len(res_aero) > 0
        assert res_aero[0]["standard"] == "DO-178C"
