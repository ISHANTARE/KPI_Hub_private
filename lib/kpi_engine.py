"""
lib/kpi_engine.py
-----------------
KPI computation module for KPI Hub.
Exposes:
  - get_status_color(score) -> tuple
  - compute_pm_kpis(data) -> dict
  - calculate_kpis(data) -> dict
  - calculate_portfolio_evm(data) -> dict
"""
import logging
import pandas as pd
from pathlib import Path
from lib.evm_engine import calculate_evm_metrics, calculate_forecasts

logger = logging.getLogger(__name__)


def get_status_color(score: float) -> tuple:
    """
    Map a numeric score to a (css_class, label) tuple.

    Returns:
        ("status-green", "Excellent")  for score >= 90
        ("status-blue",  "Healthy")    for 75 <= score < 90
        ("status-amber", "Watchlist")  for 60 <= score < 75
        ("status-red",   "Critical")   for score < 60
    """
    if score >= 90:
        return "status-green", "Excellent"
    elif score >= 75:
        return "status-blue", "Healthy"
    elif score >= 60:
        return "status-amber", "Watchlist"
    else:
        return "status-red", "Critical"


def compute_pm_kpis(data: dict) -> dict:
    """
    Compute project-management KPIs from available data.

    Returns a dict with exactly these 4 keys:
      milestone_achievement_pct   : float | None
      avg_schedule_variance_days  : float | None
      action_closure_rate_pct     : float | None
      budget_variance_pct         : float | None

    Returns None for any key when data is unavailable.
    Never raises KeyError.
    """
    result = {
        'milestone_achievement_pct': None,
        'avg_schedule_variance_days': None,
        'action_closure_rate_pct': None,
        'budget_variance_pct': None
    }
    try:
        # Milestone achievement: count milestones with status 'Complete' or 'Done'
        milestones = data.get('milestones') if data else None
        if milestones is not None and len(milestones) > 0:
            status_col = None
            for c in ['STATUS', 'status', 'State', 'STATE']:
                if c in milestones.columns:
                    status_col = c
                    break
            if status_col:
                total = len(milestones)
                done = len(milestones[milestones[status_col].str.lower().isin(['done','complete','completed','closed'])])
                result['milestone_achievement_pct'] = round((done / total) * 100, 1) if total > 0 else None

            # schedule variance: if planned vs actual dates exist
            plan_col = None
            actual_col = None
            for c in milestones.columns:
                lc = c.lower()
                if 'plan' in lc and ('date' in lc or 'start' in lc or 'end' in lc):
                    plan_col = c
                if 'actual' in lc and ('date' in lc or 'start' in lc or 'end' in lc):
                    actual_col = c
            variances = []
            if plan_col and actual_col:
                try:
                    ms = milestones.copy()
                    ms[plan_col] = pd.to_datetime(ms[plan_col], errors='coerce')
                    ms[actual_col] = pd.to_datetime(ms[actual_col], errors='coerce')
                    ms = ms.dropna(subset=[plan_col, actual_col])
                    for _, r in ms.iterrows():
                        variances.append((r[actual_col] - r[plan_col]).days)
                    if variances:
                        result['avg_schedule_variance_days'] = round(float(sum(variances)) / len(variances), 1)
                except Exception:
                    pass

        # Action closure rate: from data dictionary or action_log.csv
        actions_df = data.get('actions') if data else None
        if actions_df is None or actions_df.empty:
            action_paths = [Path('data') / 'projects' / 'action_log.csv', Path('data') / 'actions.csv']
            for p in action_paths:
                if p.exists():
                    try:
                        actions_df = pd.read_csv(p)
                        break
                    except Exception:
                        actions_df = None
        if actions_df is not None and len(actions_df) > 0:
            status_col = next((c for c in actions_df.columns if c.lower() in ['status','state']), None)
            if status_col:
                total = len(actions_df)
                closed = len(actions_df[actions_df[status_col].str.lower().isin(['closed','done','completed'])])
                result['action_closure_rate_pct'] = round((closed / total) * 100, 1) if total > 0 else None

        # Budget variance: compare planned vs spent
        budget = data.get('budget') if data else None
        if budget is not None and len(budget) > 0:
            planned_col = next((c for c in budget.columns if c.lower() in ['planned','planned_amount','budget_planned','planned_value']), None)
            spent_col = next((c for c in budget.columns if c.lower() in ['spent','actual','actual_spent','budget_spent','spent_amount','actual_cost']), None)
            if planned_col and spent_col:
                try:
                    total_planned = float(budget[planned_col].astype(float).sum())
                    total_spent = float(budget[spent_col].astype(float).sum())
                    if total_planned != 0:
                        result['budget_variance_pct'] = round(((total_spent - total_planned) / total_planned) * 100, 1)
                except Exception:
                    pass
    except Exception:
        pass
    return result


def calculate_portfolio_evm(data: dict) -> dict:
    """
    Compute portfolio-level EVM metrics (CPI, SPI, EAC, VAC).
    """
    projects = data.get('projects', pd.DataFrame())
    budget = data.get('budget', pd.DataFrame())

    portfolio_cpi = 1.0
    portfolio_spi = 1.0
    portfolio_eac = 0.0
    portfolio_vac = 0.0

    if not budget.empty:
        try:
            planned_col = next((c for c in budget.columns if c.lower() in ['planned','planned_amount','budget_planned','planned_value']), None)
            spent_col = next((c for c in budget.columns if c.lower() in ['spent','actual','actual_spent','budget_spent','spent_amount','actual_cost']), None)
            ev_col = next((c for c in budget.columns if c.lower() in ['earned_value','ev']), None)

            if planned_col and spent_col:
                total_pv = float(budget[planned_col].astype(float).sum())
                total_ac = float(budget[spent_col].astype(float).sum())
                total_ev = float(budget[ev_col].astype(float).sum()) if ev_col else (total_pv * 0.92)

                evm_res = calculate_evm_metrics(total_pv, total_ev, total_ac)
                portfolio_cpi = evm_res['cpi']
                portfolio_spi = evm_res['spi']

                bac = float(projects['BUDGET'].astype(float).sum()) if not projects.empty and 'BUDGET' in projects.columns else total_pv
                forecast_res = calculate_forecasts(bac, total_ev, total_ac, cpi=portfolio_cpi)
                portfolio_eac = forecast_res['estimate_at_completion']
                portfolio_vac = forecast_res['variance_at_completion']
        except Exception as e:
            logger.warning(f"Error calculating portfolio EVM: {e}")

    return {
        'portfolio_cpi': portfolio_cpi,
        'portfolio_spi': portfolio_spi,
        'portfolio_eac': portfolio_eac,
        'portfolio_vac': portfolio_vac
    }


def calculate_per_project_evm(data: dict) -> pd.DataFrame:
    """
    Compute per-project EVM metrics (PV, EV, AC, CPI, SPI, EAC, VAC).
    Returns a pandas DataFrame with columns:
      PROJECT_ID, PV, EV, AC, CPI, SPI, EAC, VAC, CPI_Status, SPI_Status
    """
    budget = data.get('budget', pd.DataFrame())
    projects = data.get('projects', pd.DataFrame())
    
    records = []
    
    if projects.empty:
        return pd.DataFrame(columns=['PROJECT_ID', 'PV', 'EV', 'AC', 'CPI', 'SPI', 'EAC', 'VAC', 'CPI_Status', 'SPI_Status'])
        
    project_ids = projects['PROJECT_ID'].unique()
    
    planned_col = next((c for c in budget.columns if c.lower() in ['planned','planned_amount','budget_planned','planned_value']), None) if not budget.empty else None
    spent_col = next((c for c in budget.columns if c.lower() in ['spent','actual','actual_spent','budget_spent','spent_amount','actual_cost']), None) if not budget.empty else None
    ev_col = next((c for c in budget.columns if c.lower() in ['earned_value','ev']), None) if not budget.empty else None

    for pid in project_ids:
        # Filter budget for this project
        p_budget = budget[budget['PROJECT_ID'] == pid] if not budget.empty else pd.DataFrame()
        # Filter out rows that represent totals to avoid double counting
        if not p_budget.empty and 'BUDGET_CATEGORY' in p_budget.columns:
            p_budget = p_budget[~p_budget['BUDGET_CATEGORY'].astype(str).str.upper().str.contains('TOTAL')]
            
        p_proj = projects[projects['PROJECT_ID'] == pid]
        bac = float(p_proj['BUDGET'].iloc[0]) if 'BUDGET' in p_proj.columns and not p_proj.empty and not pd.isna(p_proj['BUDGET'].iloc[0]) else 0.0
        
        pv = 0.0
        ac = 0.0
        ev = 0.0
        
        if not p_budget.empty and planned_col and spent_col:
            pv = float(p_budget[planned_col].astype(float).sum())
            ac = float(p_budget[spent_col].astype(float).sum())
            ev = float(p_budget[ev_col].astype(float).sum()) if ev_col else (pv * 0.92)
        else:
            # Fallback if no budget lines
            pv = bac
            ac = bac * 0.95
            ev = bac * 0.92
            
        if bac == 0.0:
            bac = pv
            
        evm = calculate_evm_metrics(pv, ev, ac)
        forecasts = calculate_forecasts(bac, ev, ac, cpi=evm['cpi'])
        
        records.append({
            'PROJECT_ID': pid,
            'PV': pv,
            'EV': ev,
            'AC': ac,
            'CPI': evm['cpi'],
            'SPI': evm['spi'],
            'EAC': forecasts['estimate_at_completion'],
            'VAC': forecasts['variance_at_completion'],
            'CPI_Status': evm['cpi_status'],
            'SPI_Status': evm['spi_status']
        })
        
    return pd.DataFrame(records)


def calculate_kpis(data: dict) -> dict:
    """
    Compute portfolio-level KPIs from the 22-key data dict.

    Returns exactly these 9 keys:
      portfolio_health, on_time_delivery, quality_score, test_pass_rate,
      critical_risks, high_risks, resource_util, release_readiness, active_components

    Any missing input key returns 0 for the affected KPI (never raises KeyError).
    """
    projects = data.get('projects', pd.DataFrame())
    risks = data.get('risks', pd.DataFrame())
    defects = data.get('defects', pd.DataFrame())
    tests = data.get('tests', pd.DataFrame())
    resources = data.get('resources', pd.DataFrame())

    # Portfolio Health Score
    portfolio_health = projects['HEALTH_SCORE'].mean() if not projects.empty else 0
    if pd.isna(portfolio_health):
        portfolio_health = 0

    # On-Time Delivery
    if len(projects) > 0:
        on_time = len(projects[projects['SCHEDULE_STATUS'] == 'GREEN']) / len(projects) * 100
    else:
        on_time = 0

    # Quality Score (inverse of defect density)
    critical_defects = len(defects[defects['SEVERITY'] == 'CRITICAL']) if not defects.empty else 0
    quality_score = max(0, 100 - (critical_defects * 10))

    # Test Pass Rate
    if not tests.empty and len(tests) > 0:
        test_pass_rate = (len(tests[tests['STATUS'] == 'PASSED']) / len(tests)) * 100
    else:
        test_pass_rate = 0

    # Risk Count
    critical_risks = len(risks[risks['SEVERITY'] == 'CRITICAL']) if not risks.empty else 0
    high_risks = len(risks[risks['SEVERITY'] == 'HIGH']) if not risks.empty else 0

    # Resource Utilization
    if not resources.empty:
        def parse_util(val):
            try:
                s = str(val).replace('%', '').replace('>', '')
                if '(' in s:
                    s = s.split('(')[1].replace(')', '')
                return float(s)
            except:
                return 100.0
        resource_util = resources['UTILIZATION_PCT'].apply(parse_util).mean()
        if pd.isna(resource_util):
            resource_util = 0
    else:
        resource_util = 0

    # Release Readiness (Base calculation)
    release_ready = (portfolio_health / 100) * (test_pass_rate / 100) * 100

    # ---------------------------------------------------------
    # Cross-System Penalty Integration (Dynamic Profiles)
    # ---------------------------------------------------------
    try:
        from lib.profile_loader import get_active_profile
        profile = get_active_profile()
        rules = profile.get('rules', {})

        total_penalty = 0

        # 1. Resource Overallocation Penalties
        res_penalties = rules.get('resource_overallocation_penalties', {})
        default_res_penalty = res_penalties.get('Default', 1.0)

        if not resources.empty:
            overallocated = resources[resources['UTILIZATION_PCT'].str.rstrip('%').astype(float) > 100.0]
            for _, r in overallocated.iterrows():
                role = str(r.get('ROLE', '')).lower()
                pen = default_res_penalty
                for role_key, penalty_val in res_penalties.items():
                    if role_key.lower() != 'default' and role_key.lower() in role:
                        pen = penalty_val
                        break
                total_penalty += pen

        # 2. Traceability & Phase Mismatch Penalties
        trace_insights = data.get('traceability_insights', pd.DataFrame())
        trace_weights = rules.get('traceability_severity_weights', {})

        if not trace_insights.empty:
            structural_issues = trace_insights[trace_insights['ISSUE_CATEGORY'] == 'Structural']
            for _, issue in structural_issues.iterrows():
                cat = str(issue.get('CATEGORY', 'System')).capitalize()
                pen = trace_weights.get(cat, 2.0)
                total_penalty += pen

        release_ready = max(0, release_ready - total_penalty)
    except Exception as e:
        logger.warning(f"Error executing dynamic profile penalty calculations: {e}")
    # ---------------------------------------------------------

    # Active Components
    active_components = len(projects[projects['STATUS'].isin(['In Progress', 'Planned'])]) if not projects.empty else 0

    return {
        'portfolio_health': portfolio_health,
        'on_time_delivery': on_time,
        'quality_score': quality_score,
        'test_pass_rate': test_pass_rate,
        'critical_risks': critical_risks,
        'high_risks': high_risks,
        'resource_util': resource_util,
        'release_readiness': release_ready,
        'active_components': active_components
    }
