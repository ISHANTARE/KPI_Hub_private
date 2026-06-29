"""
tests/test_data_loader.py
--------------------------
Smoke tests for lib.data_loader.

Requirements: 3.2, 3.4, 10.2, 10.6
"""

import pandas as pd
import pytest

from lib.data_loader import (
    load_data,
    init_resource_cost_data,
    compute_traceability_insights,
)

# ── Expected 23-key contract ──────────────────────────────────────────────────
EXPECTED_23_KEYS = {
    "projects", "milestones", "budget", "risks", "resources",
    "monthly_utilization", "cost_rates", "defects", "tests",
    "requirements", "issues", "escalations", "aspice", "ecrs",
    "dev_metrics", "design_reviews", "verification",
    "traceability_insights", "forecast", "audit_log",
    "decisions", "defect_trends", "org_mapping",
}


# ── Test: load_data() returns the complete 23-key contract ────────────────────

def test_load_data_returns_23_keys():
    """Req 3.2, 10.2 — load_data() must return exactly 23 keys."""
    result = load_data()
    assert result is not None, "load_data() returned None — critical data load failed"
    assert set(result.keys()) == EXPECTED_23_KEYS, (
        f"Key mismatch.\n  Missing: {EXPECTED_23_KEYS - set(result.keys())}\n"
        f"  Extra:   {set(result.keys()) - EXPECTED_23_KEYS}"
    )


def test_load_data_all_values_are_dataframes():
    """All 22 values must be pd.DataFrame instances."""
    result = load_data()
    assert result is not None
    for key, val in result.items():
        assert isinstance(val, pd.DataFrame), (
            f"Key '{key}' is {type(val).__name__}, expected DataFrame"
        )


# ── Test: non-critical files return empty DataFrames, never raise ─────────────

_NON_CRITICAL_KEYS = [
    "ecrs", "forecast", "audit_log", "decisions",
    "defect_trends", "dev_metrics", "design_reviews", "verification",
]


@pytest.mark.parametrize("key", _NON_CRITICAL_KEYS)
def test_noncritical_key_is_dataframe(key):
    """Req 3.4 — non-critical keys must be DataFrames even if source is absent."""
    result = load_data()
    assert result is not None
    assert key in result, f"Key '{key}' missing from load_data() result"
    assert isinstance(result[key], pd.DataFrame), (
        f"Key '{key}' is {type(result[key]).__name__}, expected DataFrame"
    )


# ── Test: traceability_insights key is a DataFrame ────────────────────────────

def test_traceability_insights_is_dataframe():
    """Req 3.6 — traceability_insights must be a DataFrame."""
    result = load_data()
    assert result is not None
    assert isinstance(result["traceability_insights"], pd.DataFrame)


# ── Test: compute_traceability_insights with empty inputs ─────────────────────

def test_traceability_empty_inputs_returns_correct_columns():
    """When either input is empty, return empty DF with 7 expected columns."""
    expected_cols = [
        "REQUIREMENT_ID", "TEST_ID", "PROJECT_ID",
        "CATEGORY", "ISSUE_CATEGORY", "ISSUE_TYPE", "DETAILS",
    ]
    result = compute_traceability_insights(pd.DataFrame(), pd.DataFrame())
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == expected_cols, (
        f"Column mismatch: {list(result.columns)}"
    )
    assert len(result) == 0


# ── Test: load_data() keys match minimal_data fixture ────────────────────────

def test_load_data_keys_match_minimal_data_fixture(minimal_data):
    """Req 10.7 — load_data() keys must match the minimal_data fixture keys."""
    result = load_data()
    assert result is not None
    assert set(result.keys()) == set(minimal_data.keys())
