"""
Unit tests for EVM analytical engine (lib/evm_engine.py).
"""

import pytest
from lib.evm_engine import calculate_evm_metrics, calculate_forecasts


def test_calculate_evm_metrics_healthy():
    pv = 100000.0
    ev = 100000.0
    ac = 90000.0

    res = calculate_evm_metrics(pv, ev, ac)
    assert res["cost_variance"] == 10000.0
    assert res["schedule_variance"] == 0.0
    assert res["cpi"] == 1.111
    assert res["spi"] == 1.0
    assert res["cpi_status"] == "Healthy"
    assert res["spi_status"] == "Healthy"


def test_calculate_evm_metrics_over_budget():
    pv = 100000.0
    ev = 80000.0
    ac = 100000.0

    res = calculate_evm_metrics(pv, ev, ac)
    assert res["cost_variance"] == -20000.0
    assert res["schedule_variance"] == -20000.0
    assert res["cpi"] == 0.8
    assert res["cpi_status"] == "Critical"
    assert res["spi_status"] == "Critical"


def test_calculate_forecasts():
    bac = 200000.0
    ev = 100000.0
    ac = 120000.0
    cpi = 0.833

    res = calculate_forecasts(bac, ev, ac, cpi=cpi)
    assert res["budget_at_completion"] == 200000.0
    assert res["estimate_at_completion"] > bac
    assert res["is_over_budget"] is True
