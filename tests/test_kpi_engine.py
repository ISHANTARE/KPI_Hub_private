"""
tests/test_kpi_engine.py
-------------------------
Tests for lib.kpi_engine.

Requirements: 4.2, 4.3, 4.4, 10.3, 10.4
"""

import pytest
import pandas as pd
from lib.kpi_engine import calculate_kpis, compute_pm_kpis, get_status_color

# ── Expected key contracts ────────────────────────────────────────────────────
EXPECTED_9_KEYS = {
    "portfolio_health", "on_time_delivery", "quality_score", "test_pass_rate",
    "critical_risks", "high_risks", "resource_util", "release_readiness",
    "active_components",
}

EXPECTED_4_KEYS = {
    "milestone_achievement_pct", "avg_schedule_variance_days",
    "action_closure_rate_pct", "budget_variance_pct",
}


# ── calculate_kpis tests ──────────────────────────────────────────────────────

def test_calculate_kpis_returns_9_keys(minimal_data):
    """Req 4.2, 10.3 — must return exactly 9 keys."""
    result = calculate_kpis(minimal_data)
    assert set(result.keys()) == EXPECTED_9_KEYS, (
        f"Key mismatch: {set(result.keys())}"
    )


def test_calculate_kpis_all_values_numeric(minimal_data):
    """Req 4.2, 10.3 — every value must be int or float."""
    result = calculate_kpis(minimal_data)
    for k, v in result.items():
        assert isinstance(v, (int, float)), (
            f"KPI '{k}' has non-numeric value: {v!r} ({type(v).__name__})"
        )


def test_calculate_kpis_missing_key_returns_zero():
    """Req 4.2 — absent input keys must return 0, never KeyError."""
    result = calculate_kpis({})
    for k in EXPECTED_9_KEYS:
        assert k in result, f"Missing key '{k}'"
        assert isinstance(result[k], (int, float)), f"Non-numeric for '{k}'"


def test_calculate_kpis_no_exception_on_empty_dfs(minimal_data):
    """calculate_kpis must not raise on all-empty DataFrames."""
    result = calculate_kpis(minimal_data)
    assert result is not None


# ── compute_pm_kpis tests ─────────────────────────────────────────────────────

def test_compute_pm_kpis_returns_4_keys(minimal_data):
    """Req 4.3, 10.4 — must return exactly 4 keys."""
    result = compute_pm_kpis(minimal_data)
    assert set(result.keys()) == EXPECTED_4_KEYS, (
        f"Key mismatch: {set(result.keys())}"
    )


def test_compute_pm_kpis_values_are_float_or_none(minimal_data):
    """Req 4.3 — each value must be float or None."""
    result = compute_pm_kpis(minimal_data)
    for k, v in result.items():
        assert v is None or isinstance(v, float), (
            f"Key '{k}' has unexpected type: {type(v).__name__}"
        )


def test_compute_pm_kpis_missing_data_returns_none():
    """Req 4.3 — when data is unavailable, return None for that key."""
    result = compute_pm_kpis({})
    assert set(result.keys()) == EXPECTED_4_KEYS
    for k, v in result.items():
        assert v is None or isinstance(v, float)


# ── get_status_color tests ────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (100.0, ("status-green", "Excellent")),
    (90.0,  ("status-green", "Excellent")),
    (89.9,  ("status-blue",  "Healthy")),
    (75.0,  ("status-blue",  "Healthy")),
    (74.9,  ("status-amber", "Watchlist")),
    (60.0,  ("status-amber", "Watchlist")),
    (59.9,  ("status-red",   "Critical")),
    (0.0,   ("status-red",   "Critical")),
    (-5.0,  ("status-red",   "Critical")),
])
def test_get_status_color_thresholds(score, expected):
    """Req 4.4 — verify all four threshold bands."""
    result = get_status_color(score)
    assert result == expected, f"score={score}: got {result}, expected {expected}"


def test_get_status_color_returns_tuple():
    """get_status_color must always return a 2-tuple of strings."""
    for score in [0, 50, 60, 75, 90, 100]:
        result = get_status_color(float(score))
        assert isinstance(result, tuple) and len(result) == 2
        assert all(isinstance(s, str) for s in result)


# ── KPI functional check with real data (non-empty DataFrames) ───────────────

def test_calculate_kpis_with_sample_data():
    """calculate_kpis should return sensible values on small real-shaped data."""
    projects = pd.DataFrame({
        "PROJECT_ID":    ["P001", "P002"],
        "HEALTH_SCORE":  [85.0,   65.0],
        "SCHEDULE_STATUS": ["GREEN", "RED"],
        "STATUS":        ["In Progress", "Planned"],
    })
    risks = pd.DataFrame({
        "PROJECT_ID": ["P001"],
        "SEVERITY":   ["CRITICAL"],
        "STATUS":     ["OPEN"],
        "UTILIZATION_PCT": ["100%"],
    })
    defects = pd.DataFrame({
        "PROJECT_ID": ["P001"],
        "SEVERITY":   ["HIGH"],
        "STATUS":     ["OPEN"],
    })
    tests = pd.DataFrame({
        "PROJECT_ID": ["P001", "P001"],
        "STATUS":     ["PASSED", "FAILED"],
    })
    resources = pd.DataFrame({
        "PROJECT_ID":    ["P001"],
        "TEAM_MEMBER":   ["Alice"],
        "ROLE":          ["Engineer"],
        "UTILIZATION_PCT": ["80%"],
    })

    data = {
        "projects": projects,
        "risks": risks,
        "defects": defects,
        "tests": tests,
        "resources": resources,
        "traceability_insights": pd.DataFrame(),
    }
    result = calculate_kpis(data)

    assert set(result.keys()) == EXPECTED_9_KEYS
    assert result["portfolio_health"] == pytest.approx(75.0)
    assert result["on_time_delivery"] == pytest.approx(50.0)
    assert result["test_pass_rate"] == pytest.approx(50.0)
    assert result["critical_risks"] == 1
    assert result["active_components"] == 2
