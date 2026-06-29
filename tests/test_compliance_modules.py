"""
tests/test_compliance_modules.py
---------------------------------
Unit tests for ASPICE workflow engine and project baselining modules.
"""

import pandas as pd
import pytest
from lib.workflow_engine import validate_transition
from lib.baseline import create_project_baseline, compare_baselines

def test_validate_transition():
    valid, msg = validate_transition("PLANNED", "IN_PROGRESS")
    assert valid is True
    
    invalid, msg = validate_transition("PLANNED", "COMPLETED")
    assert invalid is False
    
    gate_fail, msg = validate_transition("REVIEW", "COMPLETED", {"OPEN_FINDINGS": 2})
    assert gate_fail is False

def test_baselining_and_diff():
    data = {
        "requirements": pd.DataFrame([
            {"REQUIREMENT_ID": "REQ1", "PROJECT_ID": "P001", "TEXT": "Req 1"},
            {"REQUIREMENT_ID": "REQ2", "PROJECT_ID": "P001", "TEXT": "Req 2"}
        ]),
        "tests": pd.DataFrame()
    }
    b1 = create_project_baseline("P001", "M1", data)
    assert b1["requirements_count"] == 2

    data2 = {
        "requirements": pd.DataFrame([
            {"REQUIREMENT_ID": "REQ1", "PROJECT_ID": "P001", "TEXT": "Req 1 Modified"},
            {"REQUIREMENT_ID": "REQ3", "PROJECT_ID": "P001", "TEXT": "Req 3 New"}
        ]),
        "tests": pd.DataFrame()
    }
    b2 = create_project_baseline("P001", "M2", data2)

    diff = compare_baselines(b1, b2)
    assert diff["added_count"] == 1
    assert diff["removed_count"] == 1
    assert diff["modified_count"] == 1
