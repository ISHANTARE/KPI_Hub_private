"""
tests/test_new_modules.py
--------------------------
Unit tests for models, database, audit, and auth modules.
"""

import os
import pandas as pd
import pytest
from pathlib import Path

from lib.models import ProjectModel, validate_dataframe
from lib.database import init_db, save_dataframe_to_db, load_dataframe_from_db
from lib.audit import log_data_edit
from lib.auth import init_auth, require_role

def test_models_validation():
    df = pd.DataFrame([
        {"PROJECT_ID": "P999", "PROJECT_NAME": "Test Project", "HEALTH_SCORE": 85.0},
        {"PROJECT_ID": "P998", "PROJECT_NAME": "Invalid Score", "HEALTH_SCORE": "Not a number"}
    ])
    valid_df, errors = validate_dataframe(df, ProjectModel)
    assert len(valid_df) >= 1
    assert "P999" in valid_df["PROJECT_ID"].values

def test_database_operations(tmp_path):
    engine = init_db()
    assert engine is not None
    
    test_df = pd.DataFrame([{"ID": "1", "NAME": "Unit Test"}])
    save_dataframe_to_db("test_table", test_df, if_exists="replace")
    
    loaded_df = load_dataframe_from_db("test_table")
    assert not loaded_df.empty
    assert loaded_df.iloc[0]["NAME"] == "Unit Test"

def test_audit_logging():
    log_data_edit("TestRole", "test_file.csv", "Test Action")
    log_file = Path("data/resources/data_edit_log.csv")
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "TestRole" in content

def test_auth_initialization(monkeypatch):
    import streamlit as st
    init_auth()
    assert st.session_state.get("user_role") is not None
