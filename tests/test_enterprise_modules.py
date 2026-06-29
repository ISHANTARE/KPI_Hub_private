"""
tests/test_enterprise_modules.py
---------------------------------
Unit tests for tenancy module and REST API sidecar.
"""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from lib.tenancy import get_current_tenant_id, set_tenant_context, filter_dataframe_by_tenant
from api.main import app

client = TestClient(app)

def test_tenancy_context():
    assert get_current_tenant_id() == "tenant_default"
    set_tenant_context("tenant_acme")
    assert get_current_tenant_id() == "tenant_acme"
    set_tenant_context("tenant_default")

def test_filter_dataframe_by_tenant():
    df = pd.DataFrame([
        {"ID": 1, "TENANT_ID": "tenant_default"},
        {"ID": 2, "TENANT_ID": "tenant_other"}
    ])
    filtered = filter_dataframe_by_tenant(df)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ID"] == 1

def test_api_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert "KPI Hub REST API" in res.json()["message"]

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

def test_api_get_projects():
    res = client.get("/api/v1/projects")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
