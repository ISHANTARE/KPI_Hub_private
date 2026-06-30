"""
Earned Value Management (EVM) Analytical Engine for KPI Hub.
Provides core industry-grade financial metrics (CPI, SPI, CV, SV) and predictive forecasts (EAC, ETC, VAC).
"""

from typing import Dict, Any


def calculate_evm_metrics(planned_value: float, earned_value: float, actual_cost: float) -> Dict[str, Any]:
    """
    Computes Earned Value Management core metrics.
    
    Args:
        planned_value (float): PV - Budgeted cost of work scheduled.
        earned_value (float): EV - Budgeted cost of work performed.
        actual_cost (float): AC - Actual cost of work performed.
        
    Returns:
        Dict[str, Any]: Calculated metrics including CPI, SPI, CV, SV, and status indicators.
    """
    pv = float(planned_value or 0.0)
    ev = float(earned_value or 0.0)
    ac = float(actual_cost or 0.0)

    # Cost Variance & Schedule Variance
    cv = ev - ac
    sv = ev - pv

    # Cost Performance Index (CPI)
    cpi = round(ev / ac, 3) if ac > 0 else (1.0 if ev == 0 else 1.5)

    # Schedule Performance Index (SPI)
    spi = round(ev / pv, 3) if pv > 0 else (1.0 if ev == 0 else 1.5)

    # Status classifications
    if cpi >= 1.0:
        cpi_status = "Healthy"
    elif cpi >= 0.9:
        cpi_status = "Warning"
    else:
        cpi_status = "Critical"

    if spi >= 1.0:
        spi_status = "Healthy"
    elif spi >= 0.9:
        spi_status = "Warning"
    else:
        spi_status = "Critical"

    return {
        "planned_value": pv,
        "earned_value": ev,
        "actual_cost": ac,
        "cost_variance": cv,
        "schedule_variance": sv,
        "cpi": cpi,
        "spi": spi,
        "cpi_status": cpi_status,
        "spi_status": spi_status
    }


def calculate_forecasts(budget_at_completion: float, earned_value: float, actual_cost: float, cpi: float = None) -> Dict[str, Any]:
    """
    Computes predictive financial forecasts based on EVM metrics.
    
    Args:
        budget_at_completion (float): BAC - Total planned budget for the project.
        earned_value (float): EV - Work completed to date.
        actual_cost (float): AC - Actual spend to date.
        cpi (float, optional): CPI override. If None, calculated from EV/AC.
        
    Returns:
        Dict[str, Any]: Predictive forecasts (EAC, ETC, VAC).
    """
    bac = float(budget_at_completion or 0.0)
    ev = float(earned_value or 0.0)
    ac = float(actual_cost or 0.0)

    if cpi is None:
        cpi_metrics = calculate_evm_metrics(bac, ev, ac)
        cpi = cpi_metrics["cpi"]

    # Estimate at Completion (EAC)
    if cpi > 0:
        eac = round(bac / cpi, 2)
    else:
        eac = bac

    # Estimate to Complete (ETC)
    etc = round(max(0.0, eac - ac), 2)

    # Variance at Completion (VAC)
    vac = round(bac - eac, 2)

    return {
        "budget_at_completion": bac,
        "estimate_at_completion": eac,
        "estimate_to_complete": etc,
        "variance_at_completion": vac,
        "is_over_budget": eac > bac
    }
