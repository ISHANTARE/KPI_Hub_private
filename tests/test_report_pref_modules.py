"""
tests/test_report_pref_modules.py
----------------------------------
Unit tests for report generator and user preferences modules.
"""

import pytest
from lib.report_generator import generate_pdf_governance_report
from lib.user_preferences import get_user_preferences, update_user_preference

def test_generate_pdf_governance_report():
    kpi_data = {
        "portfolio_health": 82,
        "release_readiness": 75,
        "aspice_compliance": 90,
        "critical_defects": 1
    }
    pdf_bytes = generate_pdf_governance_report("P001", kpi_data)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0

def test_user_preferences():
    prefs = get_user_preferences()
    assert prefs.get("theme") == "light"
    update_user_preference("theme", "dark")
    updated = get_user_preferences()
    assert updated.get("theme") == "dark"
