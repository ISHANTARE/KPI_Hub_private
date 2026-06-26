import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
from integrations.scheduler import IntegrationScheduler
from integrations.config_helper import load_config
from integrations.openai_client import get_completion
from lib.copilot import launch_copilot
from lib.styling import (
    load_css, render_page_header, badge, severity_badge,
    escalation_panel, COLORS, CHART_DEFAULTS, STATUS_COLORS,
)

# Page configuration
st.set_page_config(
    page_title="KPI Hub — Engineering PMO",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject design system CSS (single call, replaces all inline <style> blocks)
load_css()


# Load data
@st.cache_data
def compute_traceability_insights(reqs, tests_df):
    if reqs.empty or tests_df.empty:
        return pd.DataFrame()
        
    insights = []
    test_to_reqs = {tc: [] for tc in tests_df['TEST_ID'].tolist()}
    
    valid_mappings = {}
    try:
        import yaml
        with open("integrations/config.yaml", "r") as f:
            cfg = yaml.safe_load(f)
            if 'traceability' in cfg and 'valid_phase_mappings' in cfg['traceability']:
                valid_mappings = {k.upper(): [v_item.upper() for v_item in v] 
                                  for k, v in cfg['traceability']['valid_phase_mappings'].items()}
    except Exception as e:
        pass
    
    for _, row in reqs.iterrows():
        req_id = row['REQUIREMENT_ID']
        proj_id = row.get('PROJECT_ID', 'UNKNOWN')
        trace_raw = str(row.get('TRACE_TEST_CASE', 'N/A'))
        
        req_last_changed = row.get('LAST_CHANGED', '1970-01-01')
        if pd.isna(req_last_changed):
            req_last_changed = '1970-01-01'
        req_last_changed = str(req_last_changed)
        req_status = str(row.get('STATUS', '')).upper()
        req_cat = str(row.get('CATEGORY', '')).upper()
        is_minor_rev = str(row.get('IS_MINOR_REVISION', 'FALSE')).upper() == 'TRUE'
        
        base_insight = {'REQUIREMENT_ID': req_id, 'PROJECT_ID': proj_id, 'CATEGORY': req_cat}
        
        if pd.isna(trace_raw) or trace_raw.strip().upper() in ['N/A', 'NONE', '', 'NAN']:
            insights.append({**base_insight, 'TEST_ID': 'NONE', 'ISSUE_CATEGORY': 'Structural', 'ISSUE_TYPE': 'Traceability Gap', 'DETAILS': 'No Test Ticket'})
        else:
            tcs = [t.strip() for t in trace_raw.split(',')]
            for tc in tcs:
                test_match = tests_df[tests_df['TEST_ID'] == tc]
                if test_match.empty:
                    insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Structural', 'ISSUE_TYPE': 'Traceability Gap', 'DETAILS': 'Linked test not found'})
                else:
                    t_row = test_match.iloc[0]
                    t_status = str(t_row.get('STATUS', 'UNKNOWN')).upper()
                    
                    t_exec_date = t_row.get('EXECUTION_DATE', '1970-01-01')
                    if pd.isna(t_exec_date):
                        t_exec_date = '1970-01-01'
                    t_exec_date = str(t_exec_date)
                    t_cat = str(t_row.get('TEST_CATEGORY', '')).upper()
                    
                    if req_last_changed != 'N/A' and t_exec_date != 'N/A' and req_last_changed > t_exec_date:
                        if is_minor_rev:
                            insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Info', 'ISSUE_TYPE': 'Minor Revision Update', 'DETAILS': f'Req updated {req_last_changed} but marked as minor revision. Coverage remains valid.'})
                        else:
                            insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Freshness', 'ISSUE_TYPE': 'Stale Coverage', 'DETAILS': f'Req updated {req_last_changed} after test {t_exec_date}'})
                        
                    if t_status == 'PASSED' and req_status in ['DRAFT', 'PROPOSED', 'UNDER_REVIEW', 'OPEN']:
                        insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Freshness', 'ISSUE_TYPE': 'Premature Testing', 'DETAILS': f'Testing {req_status} requirement'})
                        
                    if req_cat in valid_mappings:
                        if t_cat not in valid_mappings[req_cat]:
                            insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Structural', 'ISSUE_TYPE': 'Phase Mismatch', 'DETAILS': f'{t_cat} test for {req_cat} req'})
                    else:
                        if 'INTEGRATION' in t_cat and req_cat in ['THERMAL', 'CONTROL', 'MECHANICAL', 'MOTOR']:
                            insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Structural', 'ISSUE_TYPE': 'Phase Mismatch', 'DETAILS': f'{t_cat} test for {req_cat} req'})
                        
                    if t_status in ['NOT RUN', 'PENDING', 'NOT_STARTED']:
                        insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Freshness', 'ISSUE_TYPE': 'Unexecuted', 'DETAILS': f'Test status: {t_status}'})
                    elif t_status == 'FAILED':
                        insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Freshness', 'ISSUE_TYPE': 'Verification Failure', 'DETAILS': 'Test FAILED'})
                    elif t_status == 'BLOCKED':
                        insights.append({**base_insight, 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Freshness', 'ISSUE_TYPE': 'Blocked', 'DETAILS': 'Test BLOCKED'})
                    
                    if tc in test_to_reqs:
                        test_to_reqs[tc].append(req_id)
                        
    for tc, r_list in test_to_reqs.items():
        if len(r_list) == 0:
            insights.append({'REQUIREMENT_ID': 'N/A', 'PROJECT_ID': 'UNKNOWN', 'CATEGORY': 'UNKNOWN', 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Structural', 'ISSUE_TYPE': 'Orphaned Test', 'DETAILS': 'No Requirements Linked'})
        elif len(r_list) >= 3:
            insights.append({'REQUIREMENT_ID': 'Multiple', 'PROJECT_ID': 'UNKNOWN', 'CATEGORY': 'UNKNOWN', 'TEST_ID': tc, 'ISSUE_CATEGORY': 'Structural', 'ISSUE_TYPE': 'Over-linked', 'DETAILS': f'Test mapped to {len(r_list)} requirements'})
            
    return pd.DataFrame(insights)


# ── Month-range helper ───────────────────────────────────────────────────────
_MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
_MONTH_ABBR = {m: m[:3] for m in _MONTH_ORDER}

def _derive_month_range(util_df):
    """
    Return a sorted list of (month_name, year) tuples that exist in the
    monthly_utilization DataFrame.  Falls back to a rolling 12-month window
    from the current month when the DataFrame is empty or malformed.
    """
    try:
        if util_df is not None and not util_df.empty \
                and 'MONTH' in util_df.columns and 'YEAR' in util_df.columns:
            pairs = (
                util_df[['MONTH', 'YEAR']]
                .dropna()
                .drop_duplicates()
                .copy()
            )
            pairs['YEAR'] = pairs['YEAR'].astype(int)
            pairs['_ord'] = pairs.apply(
                lambda r: r['YEAR'] * 100 + (_MONTH_ORDER.index(r['MONTH']) + 1)
                if r['MONTH'] in _MONTH_ORDER else 0,
                axis=1,
            )
            pairs = pairs[pairs['_ord'] > 0].sort_values('_ord')
            result = list(zip(pairs['MONTH'], pairs['YEAR']))
            if result:
                return result
    except Exception:
        pass
    # Fallback: rolling 12 months from today
    from datetime import date
    today = date.today()
    out = []
    for i in range(12):
        m_idx = (today.month - 1 + i) % 12
        yr    = today.year + (today.month - 1 + i) // 12
        out.append((_MONTH_ORDER[m_idx], yr))
    return out


def init_resource_cost_data():
    import os
    import pandas as pd
    from pathlib import Path
    
    data_dir = Path("data")
    util_file = data_dir / "resources" / "monthly_utilization.csv"
    cost_file = data_dir / "resources" / "cost_rates.csv"
    
    # 1. Initialize cost_rates.csv if missing
    if not cost_file.exists():
        cost_file.parent.mkdir(parents=True, exist_ok=True)
        default_rates = [
            {"ROLE": "Project Manager", "COST_RATE_MONTHLY": 8000},
            {"ROLE": "Program Manager", "COST_RATE_MONTHLY": 8000},
            {"ROLE": "Program Director", "COST_RATE_MONTHLY": 10000},
            {"ROLE": "Engineering Manager", "COST_RATE_MONTHLY": 8000},
            {"ROLE": "Senior Design Engineer", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "CFD Engineers", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Controls Engineer", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Safety Engineer", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Security Architect", "COST_RATE_MONTHLY": 6500},
            {"ROLE": "Safety Architect", "COST_RATE_MONTHLY": 6500},
            {"ROLE": "Test Engineer", "COST_RATE_MONTHLY": 5000},
            {"ROLE": "Knowledge Engineer", "COST_RATE_MONTHLY": 4500},
            {"ROLE": "Systems Engineer", "COST_RATE_MONTHLY": 5000},
            {"ROLE": "Security Analyst", "COST_RATE_MONTHLY": 5000},
            {"ROLE": "Junior Dev", "COST_RATE_MONTHLY": 4000},
            {"ROLE": "Normal Worker", "COST_RATE_MONTHLY": 4000},
            {"ROLE": "CFD Analysis", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Thermal Systems", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Motor Control", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Functional Safety", "COST_RATE_MONTHLY": 6000},
            {"ROLE": "Test & Validation", "COST_RATE_MONTHLY": 5000},
            {"ROLE": "Documentation", "COST_RATE_MONTHLY": 4000},
            {"ROLE": "Cybersecurity", "COST_RATE_MONTHLY": 6000},
        ]
        pd.DataFrame(default_rates).to_csv(cost_file, index=False)
        
    # 2. Initialize monthly_utilization.csv if missing
    if not util_file.exists():
        util_file.parent.mkdir(parents=True, exist_ok=True)
        alloc_file = data_dir / "resources" / "resource_allocation.csv"
        if alloc_file.exists():
            alloc_df = pd.read_csv(alloc_file)
            months_list = [
                ("April", 2026), ("May", 2026), ("June", 2026), ("July", 2026), 
                ("August", 2026), ("September", 2026), ("October", 2026), ("November", 2026), 
                ("December", 2026), ("January", 2027), ("February", 2027), ("March", 2027)
            ]
            rows = []
            for _, r in alloc_df.iterrows():
                member = r.get("TEAM_MEMBER")
                proj_id = r.get("PROJECT_ID")
                util_str = str(r.get("UTILIZATION_PCT", "100%"))
                try:
                    util_val = float(util_str.replace("%", "").strip()) / 100.0
                except Exception:
                    util_val = 1.0
                
                # Check start/end dates if available
                start_date_str = r.get("START_DATE")
                end_date_str = r.get("END_DATE")
                try:
                    start_dt = pd.to_datetime(start_date_str) if pd.notna(start_date_str) else None
                    end_dt = pd.to_datetime(end_date_str) if pd.notna(end_date_str) else None
                except Exception:
                    start_dt = None
                    end_dt = None
                
                for month_name, year in months_list:
                    # Determine if month overlaps with the resource allocation period
                    is_active = True
                    try:
                        month_num = datetime.strptime(month_name, "%B").month
                        month_start_dt = pd.Timestamp(year=year, month=month_num, day=1)
                        if start_dt and month_start_dt < start_dt.replace(day=1):
                            is_active = False
                        if end_dt and month_start_dt > end_dt.replace(day=1):
                            is_active = False
                    except Exception:
                        pass
                        
                    val = util_val if is_active else 0.0
                    rows.append({
                        "RESOURCE_ID": member,
                        "PROJECT_ID": proj_id,
                        "MONTH": month_name,
                        "YEAR": year,
                        "UTILIZATION_PCT": round(val, 2)
                    })
            pd.DataFrame(rows).to_csv(util_file, index=False)
        else:
            pd.DataFrame(columns=["RESOURCE_ID", "PROJECT_ID", "MONTH", "YEAR", "UTILIZATION_PCT"]).to_csv(util_file, index=False)

def load_data():
    data_dir = Path("data")
    
    try:
        init_resource_cost_data()
        projects = pd.read_csv(data_dir / "projects" / "projects_status.csv")
        milestones = pd.read_csv(data_dir / "projects" / "milestones.csv")
        budget = pd.read_csv(data_dir / "projects" / "budget_tracking.csv")
        risks = pd.read_csv(data_dir / "risks" / "risk_register.csv")
        resources = pd.read_csv(data_dir / "resources" / "resource_allocation.csv")
        monthly_utilization = pd.read_csv(data_dir / "resources" / "monthly_utilization.csv")
        cost_rates = pd.read_csv(data_dir / "resources" / "cost_rates.csv")
        defects = pd.read_csv(data_dir / "metrics" / "defects.csv")
        tests = pd.read_csv(data_dir / "metrics" / "test_execution.csv")
        requirements = pd.read_csv(data_dir / "metrics" / "requirements.csv")
        issues = pd.read_csv(data_dir / "projects" / "issues.csv")
        escalations = pd.read_csv(data_dir / "projects" / "escalations.csv")
        aspice = pd.read_csv(data_dir / "metrics" / "aspice_status.csv")
        
        try:
            ecrs = pd.read_csv(data_dir / "projects" / "ecrs.csv")
        except Exception:
            ecrs = pd.DataFrame(columns=['ECR_ID', 'PROJECT_ID', 'TITLE', 'STATUS', 'CHANGE_TYPE', 'IMPACT_SCHEDULE_DAYS', 'IMPACT_COST', 'RAISED_BY', 'DATE_RAISED', 'DATE_APPROVED', 'DESCRIPTION'])

        try:
            forecast = pd.read_csv(data_dir / "resources" / "forecast.csv")
        except Exception:
            forecast = pd.DataFrame()
            
        try:
            audit_log = pd.read_csv(data_dir / "resources" / "rebalancing_audit_log.csv")
        except Exception:
            audit_log = pd.DataFrame()

        try:
            decisions = pd.read_csv(data_dir / "projects" / "decisions.csv")
        except Exception:
            decisions = pd.DataFrame()

        try:
            defect_trends = pd.read_csv(data_dir / "metrics" / "defect_trends.csv")
        except Exception:
            defect_trends = pd.DataFrame()

        try:
            dev_metrics = pd.read_csv(data_dir / "metrics" / "development_metrics.csv")
        except Exception:
            dev_metrics = pd.DataFrame(columns=['PROJECT_ID','WEEK_START','COMMITS_COUNT','PR_CYCLE_TIME_HOURS','CODE_REVIEWS_PENDING','CODE_REVIEWS_APPROVED','DEVELOPMENT_VELOCITY'])

        try:
            design_reviews = pd.read_csv(data_dir / "metrics" / "design_reviews.csv")
        except Exception:
            design_reviews = pd.DataFrame(columns=['PROJECT_ID','REVIEW_ID','STATUS','CRITICAL_ISSUES','ACTION_COMPLETION_PCT'])

        try:
            verification = pd.read_csv(data_dir / "metrics" / "verification_activities.csv")
        except Exception:
            verification = pd.DataFrame(columns=['VERIFICATION_ID','PROJECT_ID','STATUS','RESULT'])

        traceability_insights = compute_traceability_insights(requirements, tests)

        return {
            'projects': projects,
            'milestones': milestones,
            'budget': budget,
            'risks': risks,
            'resources': resources,
            'monthly_utilization': monthly_utilization,
            'cost_rates': cost_rates,
            'defects': defects,
            'tests': tests,
            'requirements': requirements,
            'issues': issues,
            'escalations': escalations,
            'aspice': aspice,
            'ecrs': ecrs,
            'dev_metrics': dev_metrics,
            'design_reviews': design_reviews,
            'verification': verification,
            'traceability_insights': traceability_insights,
            'forecast': forecast,
            'audit_log': audit_log,
            'decisions': decisions,
            'defect_trends': defect_trends
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Calculate KPIs
def calculate_kpis(data):
    projects = data['projects']
    risks = data['risks']
    defects = data['defects']
    tests = data['tests']
    resources = data['resources']
    
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
    # Cross-System Penalty Integration
    # ---------------------------------------------------------
    try:
        from integrations.config_helper import load_config
        cfg = load_config()
        
        total_penalty = 0
        
        # 1. Resource Overallocation Penalties
        res_penalties = cfg.get('resources', {}).get('resource_overallocation_penalties', {})
        default_res_penalty = res_penalties.get('Default', 1.0)
        
        if not resources.empty:
            overallocated = resources[resources['UTILIZATION_PCT'].str.rstrip('%').astype(float) > 100.0]
            for _, r in overallocated.iterrows():
                role = str(r.get('ROLE', '')).lower()
                pen = default_res_penalty
                if 'safety' in role: pen = res_penalties.get('Safety', 4.0)
                elif 'integration' in role: pen = res_penalties.get('Integration', 2.0)
                elif 'test' in role: pen = res_penalties.get('Testing', 1.5)
                elif 'critical' in role: pen = res_penalties.get('Critical', 3.0)
                total_penalty += pen
                
        # 2. Traceability & Phase Mismatch Penalties
        trace_insights = data.get('traceability_insights', pd.DataFrame())
        trace_weights = cfg.get('traceability', {}).get('severity_weights', {})
        
        if not trace_insights.empty:
            # Penalize Structural issues (Phase Mismatch, Traceability Gap, Orphans)
            structural_issues = trace_insights[trace_insights['ISSUE_CATEGORY'] == 'Structural']
            for _, issue in structural_issues.iterrows():
                # Capitalize to match yaml keys (e.g., 'Safety', 'Control')
                cat = str(issue.get('CATEGORY', 'System')).capitalize()
                pen = trace_weights.get(cat, 2.0)
                total_penalty += pen
                
        release_ready = max(0, release_ready - total_penalty)
    except Exception:
        pass
    # ---------------------------------------------------------
    
    # Active Components
    active_components = len(projects[projects['STATUS'].isin(['In Progress', 'Planned'])])
    
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

# Create status indicator — returns (css_class, label) for use in HTML
def get_status_color(score):
    if score >= 90:
        return "status-green", "Excellent"
    elif score >= 75:
        return "status-blue", "Healthy"
    elif score >= 60:
        return "status-amber", "Watchlist"
    else:
        return "status-red", "Critical"


def compute_pm_kpis(data):
    """Compute a small set of project-management KPIs from available CSVs."""
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

        # Action closure rate: from data/projects/action_log.csv or data/actions
        action_paths = [Path('data') / 'projects' / 'action_log.csv', Path('data') / 'actions.csv']
        actions_df = None
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

        # Budget variance: compare planned vs spent if available
        budget = data.get('budget') if data else None
        if budget is not None and len(budget) > 0:
            # expect columns PLANNED, SPENT or Planned, Actual
            planned_col = next((c for c in budget.columns if c.lower() in ['planned','planned_amount','budget_planned']), None)
            spent_col = next((c for c in budget.columns if c.lower() in ['spent','actual','actual_spent','budget_spent']), None)
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

@st.cache_data
def get_base64_logo():
    import base64
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            pass
    return ""

def log_data_edit(role, file_path):
    log_file = Path('data/resources/data_edit_log.csv')
    if not log_file.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("TIMESTAMP,ROLE,FILE_EDITED,ACTION\n")
    with open(log_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp},{role},{file_path},File Saved\n")

# Main App
def main():
    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = 'Manager'

    import yaml
    import os
    config_path = "integrations/config.yaml"
    config_valid = True
    config_error = ""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as exc:
            config_valid = False
            config_error = str(exc)
            
    if not config_valid:
        st.error(
            f"Configuration file `integrations/config.yaml` is malformed and cannot be loaded. "
            f"The traceability and penalty engines are offline.\n\n```\n{config_error}\n```"
        )
        st.stop()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=120)

    st.sidebar.markdown(
        '<div style="font-size:13px;font-weight:600;color:#94A3B8;'
        'letter-spacing:0.3px;margin-bottom:12px;">KPI Hub</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # user_role is already initialised at the top of main(); no duplicate needed here.
    st.session_state['current_pm'] = None

    nav_options = [
        "Portfolio Overview",
        "Project Health & Schedule",
        "Development Operations",
        "Testing & Quality",
        "Resource Utilization",
        "System Integrations",
        "Data Upload",
        "AI Insights",
    ]

    selected = st.sidebar.radio(
        "Navigation", nav_options, index=0, label_visibility="collapsed"
    )

    st.sidebar.divider()

    # Scope expander (moved out of main content area)
    with st.sidebar.expander("Scope", expanded=False):
        try:
            org_df_scope = pd.read_csv('data/resources/org_mapping.csv')
            if st.session_state.get('user_role') == 'Project Manager' and st.session_state.get('current_pm'):
                manager_options = [st.session_state['current_pm']]
            else:
                manager_options = ["All"] + sorted(org_df_scope['MANAGER_NAME'].dropna().unique().tolist())
        except Exception:
            org_df_scope = pd.DataFrame()
            manager_options = ["All"]

        selected_manager = st.selectbox('Manager', options=manager_options, index=0, key='scope_manager')

        proj_to_prog_scope = {}
        project_options = ["All"]
        try:
            raw_p = pd.read_csv(Path("data") / "projects" / "projects_status.csv")
            if 'PROJECT_ID' in raw_p.columns and 'PROGRAM' in raw_p.columns:
                proj_to_prog_scope = dict(zip(raw_p['PROJECT_ID'], raw_p['PROGRAM']))
            if selected_manager != "All" and not org_df_scope.empty:
                mgr_projs = org_df_scope[org_df_scope['MANAGER_NAME'] == selected_manager]['PROJECT_ID'].dropna().unique().tolist()
                project_options = ["All"] + sorted(mgr_projs)
        except Exception:
            pass

        selected_project = st.selectbox(
            'Project',
            options=project_options,
            index=0,
            key='scope_project',
            format_func=lambda x: f"{x} — {proj_to_prog_scope.get(x, x)}" if x != "All" else "All",
        )

    st.session_state['current_manager'] = selected_manager
    st.session_state['current_project'] = selected_project

    # Action buttons
    if st.sidebar.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    copilot_clicked = st.sidebar.button("AI Copilot", use_container_width=True)

    st.sidebar.divider()

    # AI Weekly Summary
    st.sidebar.markdown(
        '<div style="font-size:11px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.5px;color:#94A3B8;margin-bottom:6px;">Weekly Summary</div>',
        unsafe_allow_html=True,
    )
    confirm = st.sidebar.checkbox("Confirm OpenAI API call (billing applies)", value=False)
    cooldown_seconds = 60
    if 'ai_last_call' not in st.session_state:
        st.session_state['ai_last_call'] = None

    if st.sidebar.button("Generate AI Summary", use_container_width=True):
        if not confirm:
            st.sidebar.error("Check the confirmation box to proceed.")
        else:
            import time
            now = time.time()
            last = st.session_state.get('ai_last_call')
            remaining = 0
            if last:
                elapsed = now - last
                remaining = int(max(0, cooldown_seconds - elapsed))
            if last and (now - last) < cooldown_seconds:
                st.sidebar.error(f"Please wait {remaining}s before retrying.")
            else:
                st.session_state['ai_last_call'] = now
                st.session_state['run_ai_summary'] = True

    if st.session_state.get('ai_last_call'):
        import time
        rem = int(max(0, cooldown_seconds - (time.time() - st.session_state['ai_last_call'])))
        if rem > 0:
            st.sidebar.caption(f"Cooldown: {rem}s")


    # Load data
    data = load_data()
    if data is None:
        st.error("Could not load data. Please ensure CSV files are in the data/ folder.")
        return

    # Early filter of budget for non-Managers (Project Manager, Viewer, etc.)
    if st.session_state.get('user_role') != 'Manager':
        if st.session_state.get('user_role') == 'Project Manager' and st.session_state.get('current_pm'):
            pm_identity = st.session_state['current_pm']
            try:
                org_df_filter = pd.read_csv('data/resources/org_mapping.csv')
                pm_projects = org_df_filter[org_df_filter['MANAGER_NAME'] == pm_identity]['PROJECT_ID'].dropna().unique().tolist()
                if 'budget' in data:
                    data['budget'] = data['budget'][data['budget']['PROJECT_ID'].isin(pm_projects)].reset_index(drop=True)
            except Exception as e:
                st.error(f"Error applying early PM budget filters: {e}")
        else:
            # Viewer or any other non-Manager role: clear budget data entirely
            if 'budget' in data:
                data['budget'] = pd.DataFrame(columns=data['budget'].columns)

    # Pre-calculate global KPIs from unfiltered data
    global_kpis = calculate_kpis(data)

    # Build org mapping (used by pages below)
    org_df = pd.DataFrame()
    proj_to_mgr = {}
    res_to_mgr = {}
    try:
        org_df = pd.read_csv('data/resources/org_mapping.csv')
        proj_to_mgr = dict(zip(org_df['PROJECT_ID'].dropna(), org_df['MANAGER_NAME'].dropna()))
        res_to_mgr  = dict(zip(org_df['TEAM_MEMBER'].dropna().str.lower(), org_df['MANAGER_NAME'].dropna()))
    except Exception:
        pass

    proj_to_prog = {}
    try:
        raw_projects = pd.read_csv(Path("data") / "projects" / "projects_status.csv")
        if 'PROJECT_ID' in raw_projects.columns and 'PROGRAM' in raw_projects.columns:
            proj_to_prog = dict(zip(raw_projects['PROJECT_ID'], raw_projects['PROGRAM']))
    except Exception:
        pass

    # Apply Filters to internal data model
    projects = data.get('projects') if data else pd.DataFrame()
    if not projects.empty:
        valid_project_ids = set(projects['PROJECT_ID'].tolist())
        
        if selected_manager != "All":
            if selected_project != "All":
                scoped_proj = {selected_project}
            else:
                scoped_proj = set(org_df[org_df['MANAGER_NAME'] == selected_manager]['PROJECT_ID'].tolist())
            valid_project_ids = valid_project_ids.intersection(scoped_proj)
            
        valid_project_ids_list = list(valid_project_ids)
        for key in ['projects', 'requirements', 'issues', 'risks', 'tests', 'test_execution', 'defects', 'design_reviews', 'resources', 'kpis', 'milestones', 'budget', 'aspice', 'ecrs', 'dev_metrics', 'decisions', 'defect_trends', 'monthly_utilization']:
            if key in data and data[key] is not None and not data[key].empty:
                if 'PROJECT_ID' in data[key].columns:
                    data[key] = data[key][data[key]['PROJECT_ID'].isin(valid_project_ids_list)]
                    
    kpis = calculate_kpis(data)
    
    if hasattr(st, "dialog") or hasattr(st, "experimental_dialog"):
        if copilot_clicked:
            launch_copilot(data, global_kpis=global_kpis)
    else:
        if copilot_clicked:
            st.session_state['show_copilot'] = True
        if st.session_state.get('show_copilot', False):
            launch_copilot(data, global_kpis=global_kpis)
    
    # Dashboard View
    if "Portfolio Overview" in selected:
        render_page_header(
            "Portfolio Overview",
            "Program health, risk status, and escalation flags across all active projects.",
        )
        
        # AI Weekly Summary execution
        if st.session_state.get('run_ai_summary', False):
            st.session_state['run_ai_summary'] = False
            with st.spinner("Generating AI summary..."):
                try:
                    projects = data.get('projects')
                    risks = data.get('risks')
                    defects = data.get('defects')
                    tests = data.get('tests')
                    milestones = data.get('milestones')

                    total_projects = len(projects) if projects is not None else 0
                    critical_risks = 0
                    top_risks = []
                    if risks is not None and len(risks) > 0:
                        if 'EXPOSURE_SCORE' in risks.columns:
                            top = risks.sort_values('EXPOSURE_SCORE', ascending=False).head(3)
                            top_risks = [f"{r['RISK_TITLE']} (exposure={r['EXPOSURE_SCORE']})" for _, r in top.iterrows()]
                        else:
                            top = risks.head(3)
                            top_risks = [r['RISK_TITLE'] for _, r in top.iterrows()]
                        critical_risks = len(risks[risks['SEVERITY'] == 'CRITICAL']) if 'SEVERITY' in risks.columns else 0

                    open_issues_list = []
                    if defects is not None and len(defects) > 0:
                        open_issues = defects[defects.get('STATUS', '') == 'OPEN'] if 'STATUS' in defects.columns else defects
                        for _, row in open_issues.head(5).iterrows():
                            title = row.get('TITLE') or row.get('ISSUE_TITLE') or str(row.get('DEFECT_ID', ''))
                            open_issues_list.append(title)

                    recent_milestones = []
                    if milestones is not None and len(milestones) > 0:
                        if 'END_DATE' in milestones.columns:
                            try:
                                ms = milestones.copy()
                                ms['END_DATE'] = pd.to_datetime(ms['END_DATE'], errors='coerce')
                                now_dt = pd.Timestamp.now()
                                window = ms[(ms['END_DATE'] >= (now_dt - pd.Timedelta(days=14))) & (ms['END_DATE'] <= (now_dt + pd.Timedelta(days=30)))]
                                for _, m in window.head(5).iterrows():
                                    recent_milestones.append(f"{m.get('SPRINT_NAME') or m.get('MILESTONE') or m.get('name')} on {m['END_DATE'].date()}")
                            except Exception:
                                recent_milestones = list(milestones.head(5).astype(str).itertuples(index=False, name=None))

                    test_pass_rate = 0
                    try:
                        if tests is not None and len(tests) > 0 and 'STATUS' in tests.columns:
                            test_pass_rate = (len(tests[tests['STATUS'] == 'PASSED']) / len(tests)) * 100
                    except Exception:
                        test_pass_rate = 0

                    prompt = (
                        f"You are an engineering program analyst. Produce a concise weekly executive summary (4-6 bullets) for leadership. "
                        f"Context: total_projects={total_projects}, critical_risks={critical_risks}, test_pass_rate={test_pass_rate:.1f}%.\n"
                    )
                    if top_risks:
                        prompt += "Top risks: " + "; ".join(top_risks) + ".\n"
                        prompt += "For each top risk, provide 1-2 concise mitigation actions, suggested owner role, and an estimated timeline.\n"
                    if open_issues_list:
                        prompt += "Top open issues: " + "; ".join(open_issues_list) + ".\n"
                    if recent_milestones:
                        prompt += "Recent/upcoming milestones: " + "; ".join(recent_milestones) + ".\n"
                    prompt += "End with 2 recommended next actions and a confidence level (low/med/high). Keep it short and actionable."

                    ai_text = get_completion(prompt)
                    if ai_text:
                        st.session_state['ai_summary_text'] = ai_text
                    else:
                        st.error("AI summary failed — ensure OPENAI_API_KEY is set and network access is available.")
                except Exception as e:
                    st.error(f"Failed to generate AI summary: {e}")

        if st.session_state.get('ai_summary_text'):
            st.markdown("### Weekly AI Summary")
            st.info(st.session_state['ai_summary_text'])
            st.divider()

        # --- NEW GOVERNANCE & ESCALATION PANEL ---
        now = datetime.now()
        
        # Calculate Overdue High Risks
        risks = data.get('risks', pd.DataFrame())
        overdue_high_risks = 0
        if not risks.empty and 'DUE_DATE' in risks.columns:
            open_risks = risks[risks['STATUS'] == 'OPEN']
            for _, r in open_risks.iterrows():
                try:
                    due_date = pd.to_datetime(r['DUE_DATE'])
                    if due_date < now and str(r.get('SEVERITY', '')).upper() in ['HIGH', 'CRITICAL']:
                        overdue_high_risks += 1
                except Exception:
                    pass
                    
        # Calculate ASPICE < 70%
        aspice = data.get('aspice', pd.DataFrame())
        poor_aspice_projects = 0
        if not aspice.empty and 'PROJECT_ID' in aspice.columns and 'ASSESSMENT_READINESS' in aspice.columns:
            for p in aspice['PROJECT_ID'].unique():
                proj_data = aspice[aspice['PROJECT_ID'] == p]
                ready = len(proj_data[proj_data['ASSESSMENT_READINESS'] == 'READY'])
                if len(proj_data) > 0 and (ready / len(proj_data)) < 0.7:
                    poor_aspice_projects += 1
                    
        # Calculate Pending Decisions > 7 days
        decisions = data.get('decisions', pd.DataFrame())
        pending_decisions = 0
        if not decisions.empty and 'APPROVAL_STATUS' in decisions.columns:
            for _, d in decisions.iterrows():
                if d.get('APPROVAL_STATUS') == 'Pending Approval':
                    try:
                        due_date = pd.to_datetime(d['DUE_DATE'])
                        if (now - due_date).days > 7:
                            pending_decisions += 1
                    except Exception:
                        pass

        st.markdown(escalation_panel([
            {"value": overdue_high_risks,  "label": "Overdue Risks",       "description": "High/Critical past due date"},
            {"value": poor_aspice_projects,"label": "ASPICE Below 70%",    "description": "Projects below readiness threshold"},
            {"value": pending_decisions,   "label": "Pending Decisions",   "description": "Approval delayed 7+ days"},
        ]), unsafe_allow_html=True)

        # One-Click Report
        with st.expander("Generate One-Click Weekly Governance Report"):
            report_md = f"""# Weekly Governance Report
**Date:** {now.strftime('%Y-%m-%d')}
## Executive Summary
- Overdue High Risks: {overdue_high_risks}
- Projects failing ASPICE targets: {poor_aspice_projects}
- Bottlenecked Decisions: {pending_decisions}

## Portfolio Status
- Active Projects: {kpis['active_components']}
- Critical Risks: {kpis['critical_risks']}
- Test Pass Rate: {kpis['test_pass_rate']:.1f}%
            """
            st.markdown("Report generated. Review below or download for distribution.")
            st.code(report_md, language="markdown")
            st.download_button("Download Report (.md)", data=report_md, file_name=f"Governance_Report_{now.strftime('%Y%m%d')}.md", mime="text/markdown")

        st.divider()


        # Charts Row 1
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Program Health Scores")
            projects = data['projects']

            domain_data = {}
            if 'PROGRAM' in projects.columns and 'HEALTH_SCORE' in projects.columns:
                domain_data = projects.groupby('PROGRAM')['HEALTH_SCORE'].mean().to_dict()
            domain_data = {k: (v if not pd.isna(v) else 0) for k, v in domain_data.items()}

            bar_colors = [
                STATUS_COLORS.get(
                    "HEALTHY" if v >= 75 else ("WATCHLIST" if v >= 60 else "CRITICAL"),
                    COLORS["blue"]
                )
                for v in domain_data.values()
            ]

            fig = go.Figure(data=[
                go.Bar(
                    x=list(domain_data.keys()),
                    y=list(domain_data.values()),
                    marker=dict(color=bar_colors),
                    text=[f"{v:.0f}%" for v in domain_data.values()],
                    textposition='outside',
                    textfont=dict(color=COLORS["text_secondary"], size=12, family='Inter, sans-serif'),
                )
            ])
            layout = dict(**CHART_DEFAULTS)
            layout["yaxis"] = dict(range=[0, 115], **CHART_DEFAULTS["yaxis"])
            layout["height"] = 300
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Risk Distribution")
            risks = data['risks']
            risk_counts = risks['SEVERITY'].value_counts()

            fig = go.Figure(data=[
                go.Pie(
                    labels=risk_counts.index,
                    values=risk_counts.values,
                    marker=dict(
                        colors=[STATUS_COLORS.get(x, COLORS["text_muted"]) for x in risk_counts.index],
                    ),
                    hole=0.6,
                    textfont=dict(color=COLORS["text_secondary"], size=12, family='Inter, sans-serif'),
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>',
                )
            ])
            pie_layout = dict(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                height=300,
                showlegend=True,
                legend=dict(font=dict(color=COLORS["text_secondary"], size=11), bgcolor='rgba(0,0,0,0)'),
                margin=dict(t=8, b=8, l=0, r=0),
            )
            fig.update_layout(**pie_layout)
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()

        # Charts Row 2
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Readiness Breakdown")
            base_maturity = kpis['portfolio_health']

            # Risk penalty: -1% per critical risk, -0.5% per high risk (capped at -20%)
            _risks_rd = data.get('risks', pd.DataFrame())
            _n_critical = int(kpis.get('critical_risks', 0))
            _n_high     = int(kpis.get('high_risks', 0))
            risk_penalty = max(-20.0, -(_n_critical * 1.0 + _n_high * 0.5))
            final_readiness = base_maturity + risk_penalty

            col1a, col1b = st.columns(2)
            with col1a:
                st.metric("Base Maturity", f"{base_maturity:.1f}%")
            with col1b:
                st.metric(
                    "Risk Penalty",
                    f"{risk_penalty:.1f}%",
                    delta=risk_penalty,
                    help=f"{_n_critical} critical × 1% + {_n_high} high × 0.5%",
                )

            st.progress(min(100, max(0, int(final_readiness))) / 100)
            st.caption(f"Final Readiness: {final_readiness:.1f}%")

            readiness_categories = ['Design', 'Test', 'Requirements', 'Verification']

            # Requirements rate — from requirements.csv STATUS column
            try:
                reqs = data.get('requirements')
                if reqs is not None and len(reqs) > 0 and 'STATUS' in reqs.columns:
                    req_rate = len(reqs[reqs['STATUS'].str.upper() == 'APPROVED']) / len(reqs) * 100
                else:
                    req_rate = None
            except Exception:
                req_rate = None

            # Test rate — from test_execution.csv STATUS column
            try:
                tests_rd = data.get('tests')
                if tests_rd is not None and len(tests_rd) > 0 and 'STATUS' in tests_rd.columns:
                    test_rate = len(tests_rd[tests_rd['STATUS'].str.upper() == 'PASSED']) / len(tests_rd) * 100
                else:
                    test_rate = None
            except Exception:
                test_rate = None

            # Design rate — from design_reviews.csv ACTION_COMPLETION_PCT column
            # Strip '%' and 'TBD'; average only numeric rows
            try:
                dr = data.get('design_reviews')
                if dr is not None and len(dr) > 0 and 'ACTION_COMPLETION_PCT' in dr.columns:
                    _pct = pd.to_numeric(
                        dr['ACTION_COMPLETION_PCT'].astype(str).str.rstrip('%').replace('TBD', float('nan')),
                        errors='coerce'
                    ).dropna()
                    design_rate = float(_pct.mean()) if len(_pct) > 0 else None
                else:
                    design_rate = None
            except Exception:
                design_rate = None

            # Verification rate — from verification_activities.csv STATUS column
            try:
                ver = data.get('verification')
                if ver is not None and len(ver) > 0 and 'STATUS' in ver.columns:
                    _closed = ver['STATUS'].str.upper().isin(['COMPLETED', 'CLOSED', 'PASSED'])
                    ver_rate = len(ver[_closed]) / len(ver) * 100
                else:
                    ver_rate = None
            except Exception:
                ver_rate = None

            readiness_pcts  = [design_rate, test_rate, req_rate, ver_rate]
            # Show "N/A" label for any metric that couldn't be calculated
            bar_texts = [f"{p:.1f}%" if p is not None else "N/A" for p in readiness_pcts]
            # Use 0 for chart height when no data; colour based on value
            bar_values = [p if p is not None else 0.0 for p in readiness_pcts]
            readiness_colors = [
                STATUS_COLORS.get("HEALTHY" if (p or 0) >= 75 else ("WATCHLIST" if (p or 0) >= 60 else "CRITICAL"))
                for p in readiness_pcts
            ]

            fig = go.Figure(data=[
                go.Bar(
                    y=readiness_categories,
                    x=bar_values,
                    orientation='h',
                    marker=dict(color=readiness_colors),
                    text=bar_texts,
                    textfont=dict(color=COLORS["text_secondary"], size=11, family='Inter, sans-serif'),
                    textposition='outside',
                )
            ])
            r_layout = dict(**CHART_DEFAULTS)
            r_layout["xaxis"] = dict(title="% Complete", range=[0, 120], **CHART_DEFAULTS["xaxis"])
            r_layout["height"] = 240
            r_layout["margin"] = dict(t=8, b=8, l=0, r=0)
            fig.update_layout(**r_layout)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Project Health Distribution")
            projects = data['projects']
            health_counts_series = pd.cut(
                projects['HEALTH_SCORE'],
                bins=[0, 60, 75, 90, 100],
                labels=['Critical', 'Watchlist', 'Healthy', 'Excellent'],
            ).value_counts()

            categories_order = ['Excellent', 'Healthy', 'Watchlist', 'Critical']
            counts_ordered = [health_counts_series.get(cat, 0) for cat in categories_order]
            h_colors = [STATUS_COLORS[c.upper()] for c in categories_order]

            fig = go.Figure(data=[
                go.Bar(
                    x=categories_order,
                    y=counts_ordered,
                    marker_color=h_colors,
                    text=counts_ordered,
                    textposition='outside',
                    textfont=dict(color=COLORS["text_secondary"], size=13, family='Inter, sans-serif'),
                )
            ])
            h_layout = dict(**CHART_DEFAULTS)
            h_layout["height"] = 300
            h_layout["xaxis"] = dict(title="", **CHART_DEFAULTS["xaxis"])
            h_layout["yaxis"] = dict(title="Projects", **CHART_DEFAULTS["yaxis"])
            fig.update_layout(**h_layout)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Critical Items Section
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### Critical Risks")
            critical_risks_df = data['risks'][data['risks']['SEVERITY'] == 'CRITICAL']
            if len(critical_risks_df) > 0:
                for _, risk in critical_risks_df.head(3).iterrows():
                    st.markdown(
                        f'<div class="data-card">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                        f'{severity_badge("CRITICAL")}'
                        f'<span class="data-card-meta">Exposure: {risk["EXPOSURE_SCORE"]}/9</span>'
                        f'</div>'
                        f'<div class="data-card-title">{risk["RISK_TITLE"]}</div>'
                        f'<div class="data-card-meta" style="margin-top:4px;">{risk["OWNER"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("**Top Risks**")
                for _, r in critical_risks_df.head(3).iterrows():
                    st.markdown(f"- **{r['PROJECT_ID']}** — {r['RISK_TITLE']}")
            else:
                st.markdown(
                    '<div class="data-card" style="border-left:3px solid var(--green);">'
                    '<div class="data-card-title" style="color:var(--green);">No critical risks detected</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown("#### Open Issues")
            open_issues = data['issues'][data['issues']['STATUS'] == 'OPEN']
            st.metric("Total Open Issues", len(open_issues))
            if len(open_issues) > 0:
                for idx, issue in open_issues.head(3).iterrows():
                    severity = str(issue['SEVERITY']).upper()
                    sev_map = {"HIGH": "red", "CRITICAL": "red", "MEDIUM": "amber", "LOW": "green"}
                    issue_id = issue.get('ISSUE_ID') or issue.get('ID') or f'I{idx+1}'
                    st.markdown(
                        f'<div class="data-card">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                        f'{badge(severity, sev_map.get(severity, "blue"))}'
                        f'<span class="data-card-meta">{issue_id}</span>'
                        f'</div>'
                        f'<div class="data-card-title">{issue["ISSUE_TITLE"]}</div>'
                        f'<div class="data-card-meta" style="margin-top:4px;">{issue["ASSIGNED_TO"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="data-card" style="border-left:3px solid var(--green);">'
                    '<div class="data-card-title" style="color:var(--green);">No open issues</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

        with col3:
            st.markdown("#### Resource Utilization")
            resources = data['resources']
            try:
                overallocated = len(resources[resources['UTILIZATION_PCT'].str.rstrip('%').astype(float) > 100.0])
                avg_util = resources['UTILIZATION_PCT'].str.rstrip('%').astype(float).mean()
            except Exception:
                overallocated = 0
                avg_util = 0.0

            st.metric("Avg Utilization", f"{avg_util:.1f}%")
            ovr_color = COLORS["red"] if overallocated > 0 else COLORS["green"]
            st.markdown(
                f'<div class="data-card">'
                f'<div class="data-card-meta">OVERALLOCATED RESOURCES</div>'
                f'<div style="font-size:28px;font-weight:700;color:{ovr_color};line-height:1.2;">{overallocated}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            try:
                cfd = resources[resources['TEAM_MEMBER'].str.contains('CFD', case=False, na=False)]
                if not cfd.empty:
                    cfd_util = cfd.iloc[0].get('UTILIZATION_PCT', 'N/A')
                    st.markdown(
                        f'<div class="data-card">'
                        f'<div class="data-card-title">CFD Team</div>'
                        f'<div class="data-card-meta">Utilization: {cfd_util}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                pass


    # Project Health View
    elif "Project Health & Schedule" in selected:
        render_page_header(
            "Project Health & Schedule",
            "Milestone status, budget tracking, change requests, and decision register.",
        )

        milestones = data.get('milestones', pd.DataFrame())
        budget = data.get('budget', pd.DataFrame())
        ecrs = data.get('ecrs', pd.DataFrame())

        pm_kpis = compute_pm_kpis(data)

        try:
            org_df_raw = pd.read_csv('data/resources/org_mapping.csv')
            proj_to_mgr = dict(zip(org_df_raw['PROJECT_ID'], org_df_raw['MANAGER_NAME']))
        except Exception:
            proj_to_mgr = {}

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Upcoming Milestones & Status")
            if len(milestones) > 0:
                ms_df = milestones.copy()
                ms_df['PROJECT_MANAGER'] = ms_df['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
                ms_df['PLANNED_DATE'] = pd.to_datetime(ms_df['PLANNED_DATE'], errors='coerce')
                ms_df = ms_df.sort_values(by=['PROJECT_MANAGER', 'PROJECT_ID', 'PLANNED_DATE'], na_position='last')
                st.dataframe(ms_df[['PROJECT_MANAGER', 'PROJECT_ID', 'MILESTONE_NAME', 'PLANNED_DATE', 'BASELINE_DATE', 'STATUS', 'OWNER']], use_container_width=True, hide_index=True)
            else:
                st.info("No milestone records available")
                
        with col2:
            st.markdown("#### Interactive Budget Allocation")
            st.caption("Select a project to review and manage category budgets.")
            
            if len(budget) > 0 and 'projects' in locals() and len(projects) > 0:
                # 1. Project Selector
                proj_list = sorted(projects['PROJECT_ID'].unique().tolist(), key=lambda p: (proj_to_mgr.get(p, "Unknown"), p))
                if 'budget_selected_proj' not in st.session_state:
                    st.session_state['budget_selected_proj'] = proj_list[0] if proj_list else None
                    
                selected_proj = st.selectbox(
                    "Select Project:", 
                    options=proj_list,
                    index=proj_list.index(st.session_state['budget_selected_proj']) if st.session_state['budget_selected_proj'] in proj_list else 0,
                    key="budget_proj_select"
                )
                st.session_state['budget_selected_proj'] = selected_proj
                
                # Filter budget to this project
                proj_budget = budget[budget['PROJECT_ID'] == selected_proj].copy()
                
                if len(proj_budget) > 0:
                    is_manager = st.session_state.get('user_role') == 'Manager'
                    
                    st.markdown(f"**{selected_proj} Allocations**")
                    
                    # 2. Data Editor Config
                    col_config = {
                        "BUDGET_ID": st.column_config.TextColumn(disabled=True),
                        "PROJECT_ID": st.column_config.TextColumn(disabled=True),
                        "BUDGET_PERIOD": st.column_config.TextColumn(disabled=not is_manager),
                        "SPENT_AMOUNT": st.column_config.NumberColumn("SPENT_AMOUNT (Read-Only)", disabled=True, format="€%.0f"),
                        "COMMITTED_AMOUNT": st.column_config.NumberColumn(disabled=True, format="€%.0f"),
                        "VARIANCE_AMOUNT": st.column_config.NumberColumn(disabled=True),
                        "VARIANCE_PCT": st.column_config.TextColumn(disabled=True),
                        "NOTES": st.column_config.TextColumn(disabled=not is_manager)
                    }
                    
                    if is_manager:
                        col_config["PLANNED_AMOUNT"] = st.column_config.NumberColumn(format="€%.0f")
                        col_config["BUDGET_CATEGORY"] = st.column_config.TextColumn()
                        col_config["STATUS"] = st.column_config.SelectboxColumn(options=["ON_TRACK", "UNDERSPEND", "OVERSPEND", "AT_RISK"])
                    else:
                        col_config["PLANNED_AMOUNT"] = st.column_config.NumberColumn(disabled=True, format="€%.0f")
                        col_config["BUDGET_CATEGORY"] = st.column_config.TextColumn(disabled=True)
                        col_config["STATUS"] = st.column_config.TextColumn(disabled=True)
                    
                    edited_budget = st.data_editor(
                        proj_budget,
                        use_container_width=True,
                        hide_index=True,
                        column_config=col_config,
                        key=f"budget_editor_{selected_proj}",
                        disabled=not is_manager
                    )
                    
                    # 3. Save Logic
                    if is_manager:
                        if st.button("Save Budget Allocations", use_container_width=True, type="primary"):
                            try:
                                # Re-calculate Variances before saving
                                for idx, row in edited_budget.iterrows():
                                    planned = float(row.get('PLANNED_AMOUNT', 0))
                                    spent = float(row.get('SPENT_AMOUNT', 0))
                                    var_amt = planned - spent
                                    var_pct = f"{(var_amt / planned * 100):.1f}%" if planned > 0 else "0%"
                                    edited_budget.at[idx, 'VARIANCE_AMOUNT'] = var_amt
                                    edited_budget.at[idx, 'VARIANCE_PCT'] = var_pct
                                
                                # Update global budget dataframe
                                budget.update(edited_budget)
                                
                                # Save to CSV
                                budget_file_path = Path("data") / "projects" / "budget_tracking.csv"
                                budget.to_csv(budget_file_path, index=False)
                                
                                # Audit logging
                                log_data_edit('Manager', str(budget_file_path))
                                
                                st.cache_data.clear()
                                st.success("Allocations updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to save allocations: {e}")
                    else:
                        st.info("Log in as Manager to edit Planned Amounts and Classifications.")
                else:
                    st.warning(f"No budget items found for {selected_proj}")
            else:
                st.info("No budget data available")

        st.divider()
        st.markdown("#### Change Request Analysis")
        if len(ecrs) > 0:
            ecr_col1, ecr_col2 = st.columns([2, 1])
            with ecr_col1:
                ecrs_df = ecrs.copy()
                ecrs_df['PROJECT_MANAGER'] = ecrs_df['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
                ecrs_df = ecrs_df.sort_values(by=['PROJECT_MANAGER', 'PROJECT_ID'])
                st.dataframe(ecrs_df[['PROJECT_MANAGER', 'PROJECT_ID', 'ECR_ID', 'TITLE', 'STATUS', 'CHANGE_TYPE', 'IMPACT_SCHEDULE_DAYS', 'IMPACT_COST']], use_container_width=True, hide_index=True)
            with ecr_col2:
                # Change Request status distribution chart
                ecr_status_counts = ecrs['STATUS'].value_counts()
                fig_ecr = px.pie(
                    names=ecr_status_counts.index,
                    values=ecr_status_counts.values,
                    color_discrete_sequence=['#16a34a', '#1a6fdb', '#f59e0b', '#dc2626'],
                    hole=0.4
                )
                fig_ecr.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#475569', family='Inter, sans-serif'),
                    height=250,
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_ecr, use_container_width=True)

        st.divider()
        st.markdown("#### Decision & Risk Register")
        decisions_df = data.get('decisions', pd.DataFrame())
        if not decisions_df.empty:
            decisions_df_copy = decisions_df.copy()
            decisions_df_copy['PROJECT_MANAGER'] = decisions_df_copy['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
            decisions_df_copy = decisions_df_copy.sort_values(by=['PROJECT_MANAGER', 'PROJECT_ID'])
            cols = ['PROJECT_MANAGER', 'PROJECT_ID', 'DECISION_ID', 'TYPE', 'TITLE', 'IMPACT', 'OWNER', 'DUE_DATE', 'APPROVAL_STATUS']
            disp_cols = [c for c in cols if c in decisions_df_copy.columns]
            st.dataframe(decisions_df_copy[disp_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No decisions or assumptions logged yet.")

    # Development View
    elif "Development Operations" in selected:
        render_page_header(
            "Development Operations",
            "Commit trends, PR cycle times, code reviews, design reviews, and change requests.",
        )
        
        dev_metrics = data.get('dev_metrics', pd.DataFrame())
        design_rev = data.get('design_reviews', pd.DataFrame())
        
        if len(dev_metrics) > 0:
            avg_commits = dev_metrics['COMMITS_COUNT'].mean()
            avg_pr_cycle = dev_metrics['PR_CYCLE_TIME_HOURS'].mean()
            pending_reviews = dev_metrics['CODE_REVIEWS_PENDING'].sum()
            

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Weekly Commit Count Trends")
                # Group by week and project to draw line chart
                fig = px.line(
                    dev_metrics,
                    x='WEEK_START',
                    y='COMMITS_COUNT',
                    color='PROJECT_ID',
                    markers=True,
                    color_discrete_sequence=[COLORS["blue"], COLORS["green"], COLORS["amber"], COLORS["red"], COLORS["text_secondary"]],
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                    margin=dict(t=8, b=8, l=0, r=0),
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.markdown("#### Average PR Cycle Time by Project")
                pr_summary = dev_metrics.groupby('PROJECT_ID')['PR_CYCLE_TIME_HOURS'].mean().reset_index()
                fig = px.bar(
                    pr_summary,
                    x='PROJECT_ID',
                    y='PR_CYCLE_TIME_HOURS',
                    color='PR_CYCLE_TIME_HOURS',
                    color_continuous_scale=[[0, COLORS["green"]], [0.5, COLORS["amber"]], [1, COLORS["red"]]],
                    labels={'PR_CYCLE_TIME_HOURS': 'PR Cycle Time (Hours)'},
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                    margin=dict(t=8, b=8, l=0, r=0),
                )
                st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.info("No development metrics data found. Configure GitHub/GitLab integration to pull code statistics.")

        st.divider()
        st.markdown("#### Jira Ticket Analysis: Planned vs Actual Hours")
        st.caption("Compare the estimated effort against actual logged hours. Requires active Jira API credentials to sync live data.")
        
        issues_log = data.get('issues', pd.DataFrame())
        if not issues_log.empty and 'PLANNED_HOURS' in issues_log.columns and 'ACTUAL_HOURS' in issues_log.columns:
            # Coerce to numeric — rows with no hours logged are excluded from the chart
            _iss = issues_log.copy()
            _iss['PLANNED_HOURS'] = pd.to_numeric(_iss['PLANNED_HOURS'], errors='coerce')
            _iss['ACTUAL_HOURS']  = pd.to_numeric(_iss['ACTUAL_HOURS'],  errors='coerce')
            _iss = _iss.dropna(subset=['PLANNED_HOURS', 'ACTUAL_HOURS'])

            if not _iss.empty:
                fig = px.scatter(
                    _iss,
                    x='PLANNED_HOURS',
                    y='ACTUAL_HOURS',
                    color='STATUS',
                    hover_data=['ISSUE_ID', 'ISSUE_TITLE', 'ASSIGNED_TO'],
                    labels={'PLANNED_HOURS': 'Planned Hours', 'ACTUAL_HOURS': 'Actual Hours Logged'},
                    color_discrete_map={k: STATUS_COLORS.get(k, COLORS["blue"]) for k in _iss['STATUS'].unique()},
                )
                # Perfect-estimation reference line (y = x)
                max_val = max(_iss['PLANNED_HOURS'].max(), _iss['ACTUAL_HOURS'].max())
                fig.add_shape(
                    type="line", line=dict(dash="dash", color="#94a3b8"),
                    x0=0, y0=0, x1=max_val, y1=max_val
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='#f8fafc',
                    font=dict(color='#475569', family='Inter, sans-serif')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No issues with both planned and actual hours recorded yet.")
        else:
            st.info("PLANNED_HOURS / ACTUAL_HOURS columns not found in issues data. Sync from Jira to populate.")

        st.divider()
        st.markdown("#### Design & Code Architecture Reviews")
        if len(design_rev) > 0:
            st.dataframe(design_rev[['DESIGN_REVIEW_ID', 'PROJECT_ID', 'REVIEW_TYPE', 'REVIEW_DATE', 'DESIGN_PHASE', 'STATUS', 'ACTION_COMPLETION_PCT']], use_container_width=True, hide_index=True)
        else:
            st.info("No design reviews data available.")
            
        st.divider()
        st.markdown("#### Change Request Analysis")
        st.caption("Formal governance trail for all ASIL deviations and architecture changes.")
        
        ecr_path = Path('data/projects/ecrs.csv')
        if ecr_path.exists():
            ecrs = pd.read_csv(ecr_path)
            
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric("Total Change Requests", len(ecrs))
            ec2.metric("Pending Approval", len(ecrs[ecrs['STATUS'].str.upper() == 'PENDING']))
            ec3.metric("Total Cost Impact", f"€{ecrs['IMPACT_COST'].sum():,.0f}")
            
            # Show dataframe with relevant columns
            st.dataframe(
                ecrs[['ECR_ID', 'TITLE', 'STATUS', 'CHANGE_TYPE', 'IMPACT_SCHEDULE_DAYS', 'IMPACT_COST', 'LINKED_REQUIREMENT', 'APPROVAL_DATE', 'DECISION_REASON']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No Engineering Change Requests found in database.")

    # Testing & Quality View
    elif "Testing & Quality" in selected:
        render_page_header(
            "Testing & Quality",
            "Test execution pass rates, defect severity distribution, and defect trends.",
        )
        
        defects = data.get('defects', pd.DataFrame())
        tests = data.get('tests', pd.DataFrame())

        st.markdown("#### Weekly Defect Trend")
        defect_trends = data.get('defect_trends', pd.DataFrame())
        if not defect_trends.empty:
            trend_sum = defect_trends.groupby('WEEK')['OPEN_DEFECTS'].sum().reset_index()
            fig_trend = px.line(
                trend_sum,
                x='WEEK', y='OPEN_DEFECTS', markers=True,
                title="8-Week Open Defect Trend",
                color_discrete_sequence=['#ef4444']
            )
            fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#f8fafc', height=250, margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No defect trend data available")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Defect Severity Distribution")
            defect_sev = defects['SEVERITY'].value_counts()

            fig = px.pie(
                names=defect_sev.index,
                values=defect_sev.values,
                color=defect_sev.index,
                color_discrete_map={k: STATUS_COLORS.get(k, COLORS["text_muted"]) for k in defect_sev.index},
                hole=0.6,
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                margin=dict(t=8, b=8, l=0, r=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Test Execution Status")
            test_status = tests['STATUS'].value_counts()

            fig = px.pie(
                names=test_status.index,
                values=test_status.values,
                color=test_status.index,
                color_discrete_map={k: STATUS_COLORS.get(k, COLORS["text_muted"]) for k in test_status.index},
                hole=0.6,
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                margin=dict(t=8, b=8, l=0, r=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Team Roster View
    elif "Resource Utilization" in selected:
        render_page_header(
            "Resource Utilization",
            "Team allocation, utilization rates, cost planning matrix, and capacity forecasting.",
        )
        tab_cap, tab_rost = st.tabs(["Capacity & Load", "Team Roster"])

        with tab_rost:
        
            try:
                org_df = pd.read_csv('data/resources/org_mapping.csv')
            
                # If scoped, we filter org_df
                if st.session_state.get('current_manager', 'All') != "All":
                    org_df = org_df[org_df['MANAGER_NAME'] == st.session_state['current_manager']]
                if st.session_state.get('current_project', 'All') != "All":
                    org_df = org_df[org_df['PROJECT_ID'] == st.session_state['current_project']]
                
                if org_df.empty:
                    st.info("No roster data available for the selected scope.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Headcount", len(org_df))
                    with col2:
                        st.metric("Projects Covered", len(org_df['PROJECT_ID'].unique()))
                    
                    st.markdown("### Organizational Mapping")
                    org_df = org_df.sort_values(by=['MANAGER_NAME', 'TEAM_MEMBER'])
                    st.dataframe(org_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Could not load organization mapping: {e}")

        with tab_cap:
            subtab_matrix, subtab_charts = st.tabs(["Resource-Cost Matrix", "Capacity Charts"])
            
            with subtab_matrix:
                st.markdown("#### Resource-Cost Planning Matrix")
                st.caption("Month-by-month utilization planning with live budget guard rails and cost forecasting.")

                try:
                    full_util = data.get('monthly_utilization', pd.DataFrame()).copy()
                    if full_util.empty:
                        full_util = pd.read_csv('data/resources/monthly_utilization.csv')
                    cost_rates_df = pd.read_csv('data/resources/cost_rates.csv')
                    resources_alloc = pd.read_csv('data/resources/resource_allocation.csv')
                except Exception as e:
                    st.error(f"Error loading matrix files: {e}")
                    full_util = pd.DataFrame()
                    cost_rates_df = pd.DataFrame()
                    resources_alloc = pd.DataFrame()

                if not full_util.empty:
                    # ── Filters ──────────────────────────────────────────────
                    col_p, col_r = st.columns(2)
                    with col_p:
                        matrix_projects = ["All"] + sorted(full_util['PROJECT_ID'].dropna().unique().tolist())
                        selected_proj_matrix = st.selectbox("Filter by Project", options=matrix_projects, index=0, key="matrix_proj_filter")
                    with col_r:
                        matrix_resources = sorted(full_util['RESOURCE_ID'].dropna().unique().tolist())
                        selected_res_matrix = st.multiselect("Filter by Resource", options=matrix_resources, default=[], key="matrix_res_filter")

                    # ── Simulation Mode toggle ────────────────────────────────
                    sim_mode = st.toggle("Simulation Mode — edits are temporary until you apply", key="sim_mode_toggle")
                    if sim_mode:
                        st.info("Simulation Mode ON — Changes below are temporary. Use Apply to Live Data to commit, or Discard to revert.")

                    # ── Build lookup dicts ────────────────────────────────────
                    role_to_cost = dict(zip(cost_rates_df['ROLE'].str.lower(), cost_rates_df['COST_RATE_MONTHLY']))
                    res_to_role  = dict(zip(resources_alloc['TEAM_MEMBER'].str.lower(), resources_alloc['ROLE']))
                    try:
                        org_df_raw = pd.read_csv('data/resources/org_mapping.csv')
                        res_to_mgr = dict(zip(org_df_raw['TEAM_MEMBER'].str.lower(), org_df_raw['MANAGER_NAME']))
                    except Exception:
                        res_to_mgr = {}

                    # ── Short month labels derived from actual CSV data ───────
                    month_abbr = _MONTH_ABBR
                    cols_chrono_full = _derive_month_range(full_util)
                    cols_chrono      = [f"{m} {y}" for m, y in cols_chrono_full]
                    cols_short       = [f"{month_abbr[m]} {str(y)[2:]}" for m, y in cols_chrono_full]
                    long_to_short    = dict(zip(cols_chrono, cols_short))
                    short_to_long    = dict(zip(cols_short, cols_chrono))

                    # ── Apply local filters ───────────────────────────────────
                    df_mat = full_util.copy()
                    if selected_proj_matrix != "All":
                        df_mat = df_mat[df_mat['PROJECT_ID'] == selected_proj_matrix]
                    if selected_res_matrix:
                        df_mat = df_mat[df_mat['RESOURCE_ID'].isin(selected_res_matrix)]

                    # Enrich with role / cost
                    roles, rates = [], []
                    for _, r in df_mat.iterrows():
                        res_name = str(r['RESOURCE_ID']).lower()
                        role = res_to_role.get(res_name, "Normal Worker")
                        rate = role_to_cost.get(role.lower(), 4000)
                        roles.append(role); rates.append(rate)
                    df_mat['ROLE']             = roles
                    df_mat['COST_RATE_MONTHLY'] = rates
                    df_mat['MONTH_YEAR']        = df_mat['MONTH'] + " " + df_mat['YEAR'].astype(str)

                    # ── Pivot to wide format ──────────────────────────────────
                    try:
                        pivot_mat = df_mat.pivot_table(
                            index=['RESOURCE_ID','ROLE','PROJECT_ID','COST_RATE_MONTHLY'],
                            columns='MONTH_YEAR',
                            values='UTILIZATION_PCT',
                            aggfunc='first'
                        ).reset_index()
                        for c in cols_chrono:
                            if c not in pivot_mat.columns:
                                pivot_mat[c] = 0.0
                        pivot_mat = pivot_mat[['RESOURCE_ID','ROLE','PROJECT_ID','COST_RATE_MONTHLY'] + cols_chrono]

                        # Rename month columns to short labels
                        pivot_mat.rename(columns=long_to_short, inplace=True)

                        # Add projected cost column
                        total_costs = []
                        for _, row in pivot_mat.iterrows():
                            rate = row['COST_RATE_MONTHLY']
                            total_costs.append(sum(float(row[s]) for s in cols_short) * rate)
                        pivot_mat['PROJECTED_COST'] = total_costs

                        # Add manager and sort
                        pivot_mat['MANAGER'] = pivot_mat['RESOURCE_ID'].str.lower().map(res_to_mgr).fillna("Unknown")
                        display_cols = ['MANAGER','RESOURCE_ID','ROLE','PROJECT_ID','COST_RATE_MONTHLY','PROJECTED_COST'] + cols_short
                        pivot_mat    = pivot_mat[display_cols].sort_values(by=['MANAGER','RESOURCE_ID'])

                        # ── Emoji status column ───────────────────────────────
                        def _util_status(row):
                            vals = [float(row[s]) for s in cols_short]
                            peak = max(vals) if vals else 0.0
                            if peak > 1.0:   return "Over"
                            if peak >= 0.96: return "Full"
                            if peak >= 0.31: return "OK"
                            return "Under"
                        pivot_mat.insert(4, 'STATUS', pivot_mat.apply(_util_status, axis=1))

                        # Build column config
                        col_configs = {
                            "MANAGER":          st.column_config.TextColumn("Manager",         width="medium"),
                            "RESOURCE_ID":      st.column_config.TextColumn("Resource",        width="medium"),
                            "ROLE":             st.column_config.TextColumn("Role",            width="medium"),
                            "PROJECT_ID":       st.column_config.TextColumn("Project",         width="small"),
                            "STATUS":           st.column_config.TextColumn("Status",          width="small"),
                            "COST_RATE_MONTHLY":st.column_config.NumberColumn("Rate/Mo",    format="€%.0f",  width="small"),
                            "PROJECTED_COST":   st.column_config.NumberColumn("Proj. Cost", format="€%.0f",  width="medium"),
                        }
                        for s in cols_short:
                            col_configs[s] = st.column_config.NumberColumn(s, format="%.2f", min_value=0.0, max_value=2.0, width="small")

                        # Frozen index: set read-only columns as the index so they pin left
                        frozen_cols   = ['MANAGER','RESOURCE_ID','ROLE','PROJECT_ID','STATUS']
                        editable_cols = ['COST_RATE_MONTHLY','PROJECTED_COST'] + cols_short

                        pivot_display = pivot_mat.copy()

                    except Exception as e:
                        st.warning(f"No matrix records matched the filters: {e}")
                        pivot_mat     = pd.DataFrame()
                        pivot_display = pd.DataFrame()

                    # ════════════════════════════════════════════════════════
                    # BUDGET GUARD RAIL — reads live from the data_editor
                    # output, not from CSV, so it updates on every cell edit.
                    # ════════════════════════════════════════════════════════
                    def _compute_budget_panel(pivot_df, proj_id, labor_budget):
                        """Compute budget metrics from the current pivot state."""
                        monthly_spend = []
                        proj_rows = pivot_df[pivot_df['PROJECT_ID'] == proj_id] if not pivot_df.empty else pd.DataFrame()
                        for s in cols_short:
                            month_total = 0.0
                            for _, row in proj_rows.iterrows():
                                month_total += float(row[s]) * float(row['COST_RATE_MONTHLY'])
                            monthly_spend.append(month_total)
                        cumulative = []
                        running = 0.0
                        for ms in monthly_spend:
                            running += ms
                            cumulative.append(running)
                        total_proj = running
                        remaining  = labor_budget - total_proj
                        avg_monthly = total_proj / len(cols_short) if cols_short else 0
                        exhaust_idx = -1
                        for idx, cv in enumerate(cumulative):
                            if cv >= labor_budget:
                                exhaust_idx = idx
                                break
                        return monthly_spend, cumulative, total_proj, remaining, avg_monthly, exhaust_idx

                    if selected_proj_matrix != "All":
                        # Role-based visibility check
                        is_budget_allowed = True
                        if st.session_state.get('user_role') == 'Project Manager' and st.session_state.get('current_pm'):
                            try:
                                _org_sec = pd.read_csv('data/resources/org_mapping.csv')
                                pm_projs = _org_sec[_org_sec['MANAGER_NAME'] == st.session_state['current_pm']]['PROJECT_ID'].dropna().unique().tolist()
                                if selected_proj_matrix not in pm_projs:
                                    is_budget_allowed = False
                            except Exception:
                                is_budget_allowed = False

                        if is_budget_allowed:
                            try:
                                budget_df      = pd.read_csv('data/projects/budget_tracking.csv')
                                proj_budget_df = budget_df[budget_df['PROJECT_ID'] == selected_proj_matrix]
                                labor_row      = proj_budget_df[proj_budget_df['BUDGET_CATEGORY'].str.contains('Labor|Engineering', case=False, na=False)]
                                if not labor_row.empty:
                                    labor_budget = float(labor_row.iloc[0]['PLANNED_AMOUNT'])
                                else:
                                    non_total    = proj_budget_df[~proj_budget_df['BUDGET_CATEGORY'].str.contains('TOTAL', case=False, na=False)]
                                    labor_budget = float(non_total['PLANNED_AMOUNT'].sum()) if not non_total.empty else 0.0
                            except Exception as e:
                                labor_budget = 0.0

                            if labor_budget > 0.0 and not pivot_mat.empty:
                                # ── REAL-TIME guard rail — computed from CURRENT editor state ──
                                # We compute from pivot_mat first (pre-edit baseline), then
                                # re-compute after the data_editor is rendered using its output.
                                _ms, _cum, _total, _rem, _avg, _ei = _compute_budget_panel(pivot_mat, selected_proj_matrix, labor_budget)

                                used_pct = (_total / labor_budget * 100) if labor_budget else 0

                                if _cum and _cum[0] >= labor_budget:
                                    _guard_color  = COLORS["red"]
                                    _guard_status = "OVER BUDGET"
                                    _guard_msg    = "Already over budget at current allocations."
                                elif _ei != -1:
                                    _guard_color  = COLORS["amber"]
                                    _guard_status = "AT RISK"
                                    months_left   = _ei
                                    _guard_msg    = f"Budget exhausted by {cols_chrono[_ei]} — {months_left} month{'s' if months_left != 1 else ''} from now."
                                else:
                                    _guard_color  = COLORS["green"]
                                    _guard_status = "ON TRACK"
                                    _guard_msg    = f"Budget sufficient through {cols_chrono[-1]}."

                                st.markdown(f"""
<div style="background:#0F1923;border-left:3px solid {_guard_color};border-radius:6px;padding:16px 20px;margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <span style="font-size:13px;font-weight:600;color:#CBD5E1;">Budget Guard Rail — {selected_proj_matrix}</span>
    <span style="background:{_guard_color};color:white;font-size:10px;font-weight:600;padding:2px 8px;border-radius:4px;letter-spacing:0.4px;text-transform:uppercase;">{_guard_status}</span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
    <div><div style="color:#8896A7;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">Labor Budget</div><div style="color:#F1F5F9;font-size:18px;font-weight:700;">€{labor_budget:,.0f}</div></div>
    <div><div style="color:#8896A7;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">Projected Spend</div><div style="color:#F1F5F9;font-size:18px;font-weight:700;">€{_total:,.0f} <span style="font-size:12px;color:#8896A7;">({used_pct:.0f}%)</span></div></div>
    <div><div style="color:#8896A7;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">Remaining</div><div style="color:{'#16803C' if _rem >= 0 else '#B91C1C'};font-size:18px;font-weight:700;">€{_rem:,.0f}</div></div>
    <div><div style="color:#8896A7;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">Avg Burn Rate</div><div style="color:#F1F5F9;font-size:18px;font-weight:700;">€{_avg:,.0f}<span style="font-size:11px;color:#8896A7;">/mo</span></div></div>
  </div>
  <div style="color:#CBD5E1;font-size:12px;margin-top:10px;">{_guard_msg}</div>
</div>
""", unsafe_allow_html=True)
                            elif labor_budget <= 0.0:
                                st.warning("No labor budget configured for this project in budget_tracking.csv.")
                        else:
                            st.info("Budget visibility restricted — resource cost rates are visible for cross-team negotiation, but budget envelopes for other PMs' projects are hidden.")

                    st.divider()

                    # ── Matrix Data Editor ────────────────────────────────────
                    st.markdown("#### Consolidated Matrix — Edit in Place")
                    st.caption("Enter utilization as decimal: 0.8 = 80%, 1.0 = 100%. Status column updates after applying changes.")

                    if not pivot_display.empty:
                        edited_pivot = st.data_editor(
                            pivot_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config=col_configs,
                            disabled=frozen_cols,
                            key="pivot_editor"
                        )

                        # ── Re-compute budget guard rail from EDITOR OUTPUT ───
                        # This is the live update — reads edited_pivot, not CSV.
                        if selected_proj_matrix != "All" and is_budget_allowed if 'is_budget_allowed' in dir() else False:
                            try:
                                if 'labor_budget' in dir() and labor_budget > 0.0:
                                    _ms2, _cum2, _total2, _rem2, _avg2, _ei2 = _compute_budget_panel(edited_pivot, selected_proj_matrix, labor_budget)
                                    if _total2 != _total:  # Values changed → show updated panel
                                        used2 = (_total2 / labor_budget * 100)
                                        _delta_str = f"€{_total2 - _total:+,.0f} vs baseline"
                                        if _ei2 != -1:
                                            st.warning(f"Live Update: Projected spend now €{_total2:,.0f} ({used2:.0f}%) — exhaustion at {cols_chrono[_ei2]} — {_delta_str}")
                                        elif _cum2 and _cum2[0] >= labor_budget:
                                            st.error(f"Live Update: Already over budget — €{_total2:,.0f} — {_delta_str}")
                                        else:
                                            st.success(f"Live Update: Projected spend €{_total2:,.0f} — budget healthy — {_delta_str}")
                            except Exception:
                                pass

                        # Simulation vs Live save buttons
                        m_col1, m_col2, m_col3 = st.columns(3)

                        if sim_mode:
                            sim_label  = "Apply to Live Data"
                            disc_label = "Discard Simulation"
                        else:
                            sim_label  = "Save Matrix Changes"
                            disc_label = None

                        with m_col1:
                            if st.button(sim_label, type="primary", use_container_width=True, key="save_matrix_btn"):
                                try:
                                    disk_util = pd.read_csv('data/resources/monthly_utilization.csv')
                                    original_util = disk_util.copy()

                                    # Melt edited pivot back to long format
                                    id_cols   = ['MANAGER','RESOURCE_ID','ROLE','PROJECT_ID','STATUS','COST_RATE_MONTHLY','PROJECTED_COST']
                                    melt_cols = [c for c in edited_pivot.columns if c in cols_short]
                                    melted    = edited_pivot.melt(id_vars=['RESOURCE_ID','PROJECT_ID'], value_vars=melt_cols,
                                                                   var_name='MONTH_SHORT', value_name='UTILIZATION_PCT')
                                    melted['MONTH']      = melted['MONTH_SHORT'].map({v: k.split()[0] for k, v in long_to_short.items()})
                                    melted['YEAR']       = melted['MONTH_SHORT'].map({v: int(k.split()[1]) for k, v in long_to_short.items()})
                                    melted               = melted.drop(columns=['MONTH_SHORT'])
                                    melted.set_index(['RESOURCE_ID','PROJECT_ID','MONTH','YEAR'], inplace=True)

                                    disk_util.set_index(['RESOURCE_ID','PROJECT_ID','MONTH','YEAR'], inplace=True)
                                    disk_util.update(melted)
                                    disk_util.reset_index(inplace=True)
                                    disk_util.to_csv('data/resources/monthly_utilization.csv', index=False)
                                    log_data_edit(st.session_state.get('user_role'), 'data/resources/monthly_utilization.csv')

                                    # Audit log — compute cost delta
                                    try:
                                        old_cost = sum(float(r['COST_RATE_MONTHLY']) * sum(float(r[s]) for s in cols_short)
                                                        for _, r in pivot_display.iterrows()) if not pivot_display.empty else 0
                                        new_cost = sum(float(r['COST_RATE_MONTHLY']) * sum(float(r[s]) for s in cols_short)
                                                        for _, r in edited_pivot.iterrows()) if not edited_pivot.empty else 0
                                        cost_delta = round(new_cost - old_cost)

                                        df_audit  = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                                        new_entry = pd.DataFrame([{
                                            'TIMESTAMP':            datetime.now().isoformat(),
                                            'SOURCE_RESOURCE':      st.session_state.get('user_role', 'Manager'),
                                            'TARGET_BOTTLENECK':    selected_proj_matrix if selected_proj_matrix != "All" else "All Projects",
                                            'HOURS_TRANSFERRED':    0,
                                            'ESTIMATED_COST_DELTA': cost_delta,
                                            'NEW_SOURCE_UTIL':      'N/A',
                                            'NEW_TARGET_UTIL':      'N/A',
                                            'DECISION':             'MANUAL_OVERRIDE',
                                            'RATIONALE':            f'PM manually updated utilization matrix. Cost delta: €{cost_delta:+,}'
                                        }])
                                        pd.concat([df_audit, new_entry], ignore_index=True).to_csv('data/resources/rebalancing_audit_log.csv', index=False)
                                    except Exception:
                                        pass

                                    st.cache_data.clear()
                                    if sim_mode:
                                        st.success("Simulation applied to live data and logged to Governance Audit Trail.")
                                    else:
                                        st.success("Matrix saved successfully.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error saving matrix: {e}")

                        if sim_mode and disc_label:
                            with m_col2:
                                if st.button(disc_label, use_container_width=True, key="discard_sim_btn"):
                                    st.cache_data.clear()
                                    st.rerun()

                        with m_col3:
                            try:
                                import io
                                buffer = io.BytesIO()
                                export_df = pivot_display.copy()
                                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                                    export_df.to_excel(writer, index=False, sheet_name='Planning_Matrix')
                                st.download_button(
                                    label="Export to Excel",
                                    data=buffer.getvalue(),
                                    file_name="planning_matrix_export.xlsx",
                                    mime="application/vnd.ms-excel",
                                    use_container_width=True
                                )
                            except Exception:
                                pass





                    


                    
            with subtab_charts:
                resources = data.get('resources', pd.DataFrame())
                issues = data.get('issues', pd.DataFrame())
            
                if len(resources) > 0:
                    st.markdown("#### Capacity & Demand Forecasting")
                    fc1, fc2, fc3 = st.columns(3)
                
                    with fc1:
                        util_df = data.get('monthly_utilization', pd.DataFrame())
                        cols_chrono_cap  = _derive_month_range(util_df)
                        cols_chrono      = [f"{m} {y}" for m, y in cols_chrono_cap]
                        if not util_df.empty:
                            distinct_resources = util_df['RESOURCE_ID'].dropna().unique()
                            headcount = float(len(distinct_resources))
                            demand_list = []
                            capacity_list = []
                            for col_month in cols_chrono:
                                m, y = col_month.split(" ")
                                y = int(y)
                                m_rows = util_df[(util_df['MONTH'] == m) & (util_df['YEAR'] == y)]
                                m_demand = m_rows['UTILIZATION_PCT'].sum()
                                demand_list.append(m_demand)
                                capacity_list.append(headcount)
                            
                            fig_cap = go.Figure()
                            
                            fig_cap.add_trace(go.Scatter(
                                x=cols_chrono,
                                y=capacity_list,
                                mode='lines',
                                name='Total Available Capacity',
                                line=dict(color=COLORS["green"], width=2, dash='dash')
                            ))
                            fig_cap.add_trace(go.Scatter(
                                x=cols_chrono,
                                y=demand_list,
                                mode='lines+markers',
                                name='Projected Demand',
                                line=dict(color=COLORS["blue"], width=2)
                            ))
                            
                            overallocation_y = [max(c, d) for c, d in zip(capacity_list, demand_list)]
                            
                            fig_cap.add_trace(go.Scatter(
                                x=cols_chrono,
                                y=capacity_list,
                                mode='lines',
                                line=dict(color='rgba(0,0,0,0)', width=0),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
                            
                            fig_cap.add_trace(go.Scatter(
                                x=cols_chrono,
                                y=overallocation_y,
                                mode='lines',
                                fill='tonexty',
                                fillcolor='rgba(239, 68, 68, 0.25)',
                                line=dict(color='rgba(0,0,0,0)', width=0),
                                name='Overallocation Zone',
                                hoverinfo='skip'
                            ))
                            
                            fig_cap.update_layout(
                                xaxis_title="Timeline",
                                yaxis_title="FTE Units",
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                height=300,
                                margin=dict(t=8, b=8, l=0, r=0),
                                showlegend=True,
                                legend=dict(orientation="h", y=-0.25, x=0, font=dict(size=11)),
                                font=dict(family='Inter, sans-serif', color=COLORS["text_secondary"]),
                            )
                            fig_cap.update_yaxes(title_text="FTE Units", tickformat=".1f")
                            st.plotly_chart(fig_cap, use_container_width=True)
                        else:
                            st.info("No resource utilization data available for the selected scope.")
                        
                    with fc2:
                        if not resources.empty:
                            proj_alloc = resources.groupby('PROJECT_ID')['ALLOCATED_HOURS_WEEKLY'].sum().reset_index()
                            proj_alloc['MANAGER'] = proj_alloc['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
                            proj_alloc = proj_alloc.sort_values(by=['MANAGER', 'PROJECT_ID'])
                            fig = px.pie(proj_alloc, values='ALLOCATED_HOURS_WEEKLY', names='PROJECT_ID', hole=0.5,
                                         title="Allocation by Project (Current Month)")
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                        
                    with fc3:
                        milestones = data.get('milestones', pd.DataFrame())
                        if not milestones.empty:
                            milestones['PLANNED_DATE'] = pd.to_datetime(milestones['PLANNED_DATE'], errors='coerce')
                            future_ms = milestones[milestones['PLANNED_DATE'] > datetime.now()].copy()
                            future_ms['WEEK'] = future_ms['PLANNED_DATE'].dt.to_period('W').dt.start_time
                            demand = future_ms.groupby('WEEK').size().reset_index(name='EXPECTED_DEMAND_FTE')
                            # Multiplier = average team size per milestone (configurable via resources.fte_per_milestone)
                            try:
                                from integrations.config_helper import load_config as _lcfg
                                _fte_mult = float(_lcfg().get('resources', {}).get('fte_per_milestone', 5))
                            except Exception:
                                _fte_mult = 5.0
                            demand['EXPECTED_DEMAND_FTE'] = demand['EXPECTED_DEMAND_FTE'] * _fte_mult
                        
                            if not demand.empty:
                                fig = px.area(demand.head(8), x='WEEK', y='EXPECTED_DEMAND_FTE', 
                                              title="Demand Forecast (Upcoming Milestones)",
                                              color_discrete_sequence=['#8b5cf6'])
                                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No upcoming milestones for demand forecasting")
                        else:
                            st.info("No milestone data available")
                        
                    st.divider()

                    with st.expander("Import Resource Data"):
                        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"], key="resource_importer")
                        if uploaded_file is not None:
                            try:
                                if uploaded_file.name.endswith('.csv'):
                                    imported_df = pd.read_csv(uploaded_file)
                                else:
                                    imported_df = pd.read_excel(uploaded_file)

                                if 'TEAM_MEMBER' in imported_df.columns:
                                    imported_df.to_csv('data/resources/resource_allocation.csv', index=False)
                                    st.success("Resources imported. Click Refresh Data in the sidebar.")
                                else:
                                    st.error("Invalid format: Missing TEAM_MEMBER column")
                            except Exception as e:
                                st.error(f"Error importing file: {e}")

                    st.divider()

                    # ── Budget Burn Trend ────────────────────────────────────
                    st.markdown("#### Budget Burn Trend")
                    try:
                        _burn_proj_options = ["All"] + sorted(data.get('monthly_utilization', pd.DataFrame())['PROJECT_ID'].dropna().unique().tolist())
                        _burn_proj = st.selectbox("Select Project for Burn Trend", _burn_proj_options, key="burn_trend_proj")
                        _cost_rates_bt = pd.read_csv('data/resources/cost_rates.csv')
                        _util_bt       = data.get('monthly_utilization', pd.DataFrame()).copy()
                        _res_bt        = pd.read_csv('data/resources/resource_allocation.csv')
                        _role_cost_bt  = dict(zip(_cost_rates_bt['ROLE'].str.lower(), _cost_rates_bt['COST_RATE_MONTHLY']))
                        _res_role_bt   = dict(zip(_res_bt['TEAM_MEMBER'].str.lower(), _res_bt['ROLE']))

                        _bt_cols   = _derive_month_range(_util_bt if not _util_bt.empty else data.get('monthly_utilization', pd.DataFrame()))
                        _bt_labels = [f"{m[:3]} {str(y)[2:]}" for m, y in _bt_cols]

                        if _burn_proj != "All":
                            _util_bt = _util_bt[_util_bt['PROJECT_ID'] == _burn_proj]

                        _monthly_spend_bt = []
                        for m, y in _bt_cols:
                            _rows = _util_bt[(_util_bt['MONTH'] == m) & (_util_bt['YEAR'] == y)]
                            _ms   = 0.0
                            for _, _r in _rows.iterrows():
                                _role = _res_role_bt.get(str(_r['RESOURCE_ID']).lower(), 'Normal Worker')
                                _rate = _role_cost_bt.get(_role.lower(), 4000)
                                _ms  += float(_r['UTILIZATION_PCT']) * _rate
                            _monthly_spend_bt.append(_ms)

                        _cum_bt = []
                        _run    = 0.0
                        for _ms in _monthly_spend_bt:
                            _run += _ms
                            _cum_bt.append(_run)

                        # Fetch budget limit
                        _labor_bt = 0.0
                        if _burn_proj != "All":
                            try:
                                _bdf = pd.read_csv('data/projects/budget_tracking.csv')
                                _bdf = _bdf[_bdf['PROJECT_ID'] == _burn_proj]
                                _lrow = _bdf[_bdf['BUDGET_CATEGORY'].str.contains('Labor|Engineering', case=False, na=False)]
                                if not _lrow.empty:
                                    _labor_bt = float(_lrow.iloc[0]['PLANNED_AMOUNT'])
                                else:
                                    _nt = _bdf[~_bdf['BUDGET_CATEGORY'].str.contains('TOTAL', case=False, na=False)]
                                    _labor_bt = float(_nt['PLANNED_AMOUNT'].sum()) if not _nt.empty else 0.0
                            except Exception:
                                pass

                        _fig_bt = go.Figure()
                        _fig_bt.add_trace(go.Bar(
                            x=_bt_labels, y=_monthly_spend_bt, name='Monthly Spend',
                            marker_color='rgba(26,111,219,0.5)', yaxis='y'
                        ))
                        _fig_bt.add_trace(go.Scatter(
                            x=_bt_labels, y=_cum_bt, name='Cumulative Spend',
                            mode='lines+markers', line=dict(color='#1a6fdb', width=3), yaxis='y'
                        ))
                        if _labor_bt > 0:
                            _fig_bt.add_trace(go.Scatter(
                                x=_bt_labels, y=[_labor_bt]*len(_bt_labels), name='Budget Limit',
                                mode='lines', line=dict(color='#ef4444', width=2, dash='dash'), yaxis='y'
                            ))
                        _fig_bt.update_layout(
                            title=f"Budget Burn Trend — {_burn_proj}",
                            xaxis_title="Month", yaxis_title="Cost (€)",
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#f8fafc', height=320,
                            margin=dict(t=40,b=20,l=20,r=20),
                            legend=dict(orientation='h', y=1.1, x=0),
                            font=dict(color='#475569', family='Inter, sans-serif')
                        )
                        st.plotly_chart(_fig_bt, use_container_width=True)
                    except Exception as _e:
                        st.info(f"Budget Burn Trend unavailable: {_e}")

                    # ── Weekly Hours (demoted to expander) ────────────────────
                    with st.expander("Allocated vs Utilized Hours — Weekly Detail"):
                        resources_disp = resources.copy()
                        resources_disp['ALLOCATED_HOURS_WEEKLY'] = pd.to_numeric(resources_disp['ALLOCATED_HOURS_WEEKLY'], errors='coerce')
                        resources_disp['UTILIZED_HOURS_WEEKLY']  = pd.to_numeric(resources_disp['UTILIZED_HOURS_WEEKLY'],  errors='coerce')
                        resources_disp['MANAGER'] = resources_disp['TEAM_MEMBER'].str.lower().map(res_to_mgr).fillna("Unknown")
                        resources_disp = resources_disp.sort_values(by=['MANAGER','TEAM_MEMBER'])
                        fig_wh = px.bar(
                            resources_disp, x='TEAM_MEMBER',
                            y=['ALLOCATED_HOURS_WEEKLY','UTILIZED_HOURS_WEEKLY'],
                            barmode='group',
                            color_discrete_sequence=[COLORS["blue"], COLORS["amber"]],
                        )
                        fig_wh.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                            margin=dict(t=8, b=8, l=0, r=0),
                        )
                        st.plotly_chart(fig_wh, use_container_width=True)

                    st.divider()
                    
                    if st.toggle("Enable AI Resource Rebalancing Recommendations", key="ai_rebalance_toggle"):
                        st.markdown("#### AI Rebalancing Insights")
                        with st.spinner("Analyzing skill matrices and utilization loads..."):
                            cost_df = data.get('cost_rates', pd.DataFrame())
                            resources_df = resources.copy()
                            if not cost_df.empty and 'ROLE' in cost_df.columns:
                                resources_df = resources_df.merge(cost_df, on='ROLE', how='left')
                            else:
                                resources_df['COST_RATE_MONTHLY'] = 0
                            
                            util_df = data.get('monthly_utilization', pd.DataFrame())
                            if not util_df.empty:
                                monthly_sums = util_df.groupby(['RESOURCE_ID', 'MONTH', 'YEAR'])['UTILIZATION_PCT'].sum().reset_index()
                                avg_util = monthly_sums.groupby('RESOURCE_ID')['UTILIZATION_PCT'].mean().reset_index()
                                resources_df = resources_df.merge(avg_util, left_on='TEAM_MEMBER', right_on='RESOURCE_ID', how='left')
                                resources_df['UTIL_NUM'] = (resources_df['UTILIZATION_PCT_y'] * 100).fillna(
                                    pd.to_numeric(resources_df['UTILIZATION_PCT_x'].str.rstrip('%'), errors='coerce')
                                ).fillna(100.0)
                            else:
                                resources_df['UTIL_NUM'] = pd.to_numeric(resources_df['UTILIZATION_PCT'].str.rstrip('%'), errors='coerce').fillna(100.0)
                        
                            underutilized = resources_df[(resources_df['UTIL_NUM'] < 80.0) | (resources_df['ALLOCATION_STATUS'].isin(['COMPLETED', 'AVAILABLE']))].copy()
                            underutilized['MANAGER'] = underutilized['TEAM_MEMBER'].str.lower().map(res_to_mgr).fillna("Unknown")
                            underutilized = underutilized.sort_values(by=['MANAGER', 'TEAM_MEMBER'])
                            
                            overallocated = resources_df[(resources_df['UTIL_NUM'] > 100.0) | (resources_df['ALLOCATION_STATUS'] == 'OVERALLOCATED')].copy()
                            overallocated['MANAGER'] = overallocated['TEAM_MEMBER'].str.lower().map(res_to_mgr).fillna("Unknown")
                            overallocated = overallocated.sort_values(by=['MANAGER', 'TEAM_MEMBER'])
                        
                            if overallocated.empty:
                                st.success("No overallocated resources or bottlenecks detected! The team is perfectly balanced.")
                            elif underutilized.empty:
                                st.warning("Bottlenecks detected, but no underutilized resources are available to help. You may need to hire or defer work.")
                                st.dataframe(overallocated[['MANAGER', 'TEAM_MEMBER', 'ROLE', 'SKILL', 'UTIL_NUM', 'PROJECT_ID']], use_container_width=True, hide_index=True)
                            else:
                                import json
                                import re
                            
                                if "ai_rebalance_recs" not in st.session_state:
                                    cols_under = ['TEAM_MEMBER', 'ROLE', 'SKILL', 'UTIL_NUM', 'COST_RATE_MONTHLY']
                                    cols_over = ['TEAM_MEMBER', 'ROLE', 'SKILL', 'UTIL_NUM', 'PROJECT_ID', 'COST_RATE_MONTHLY']
                                    under_str = underutilized[[c for c in cols_under if c in underutilized.columns]].to_dict(orient='records')
                                    over_str = overallocated[[c for c in cols_over if c in overallocated.columns]].to_dict(orient='records')
                                
                                    prompt = f"""You are an expert Resource Manager. Analyze the following over-allocated bottlenecks and underutilized available personnel. 
        Match available personnel to bottlenecks based on matching or complementary 'SKILL' and 'ROLE'. 
        Underutilized (Available bandwidth): {json.dumps(under_str)}
        Overallocated (Needs help): {json.dumps(over_str)}
    
        Provide 1-3 highly specific recommendations. Balance both utilization and cost. Make cost the tiebreaker when utilization impact is roughly equal (e.g. choose the cheaper resource if both solve the bottleneck). Do not sacrifice significant utilization improvement for marginal cost savings.
        Return ONLY a valid JSON array of objects with the keys:
        "source_resource" (the underutilized person), "target_bottleneck" (the team/person needing help), 
        "rationale" (why they match, explicitly mentioning cost differences), "suggested_action" (e.g. "Move 10% allocation of X to assist Y"),
        "hours_transferred" (integer representing approximate % allocation transferred, e.g. 10), 
        "new_source_utilization" (predicted utilization % as string like '60%'), 
        "new_target_utilization" (predicted utilization % as string like '95%'),
        "estimated_cost_delta" (integer representing the estimated monthly cost difference in euros, e.g. -500 if saving money, 500 if costing more),
        "source_impact" (e.g. "Cost drops by €500, utilization drops to 60%"), 
        "target_impact" (e.g. "Utilization normalizes to 95%")"""
                                    response = get_completion(prompt, max_tokens=1500)
                                    st.session_state["ai_rebalance_recs"] = response

                                response = st.session_state["ai_rebalance_recs"]
                                try:
                                    match = re.search(r'\[.*\]', response, re.DOTALL)
                                    if match:
                                        recs = json.loads(match.group(0))
                                        for i, rec in enumerate(recs):
                                            with st.container():
                                                st.markdown(f"**Action:** {rec.get('suggested_action', '')}")
                                                st.markdown(f"**From:** `{rec.get('source_resource', '')}` — **To:** `{rec.get('target_bottleneck', '')}`")
                                                st.caption(f"Rationale: {rec.get('rationale', '')}")

                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric(f"Impact on {rec.get('source_resource', '')}",
                                                              rec.get('new_source_utilization', ''),
                                                              delta=f"+{rec.get('hours_transferred', 0)}% alloc", delta_color="normal")
                                                    st.caption(rec.get('source_impact', ''))
                                                with col2:
                                                    st.metric(f"Impact on {rec.get('target_bottleneck', '')}",
                                                              rec.get('new_target_utilization', ''),
                                                              delta=f"-{rec.get('hours_transferred', 0)}% alloc", delta_color="inverse")
                                                    st.caption(rec.get('target_impact', ''))
                                                with col3:
                                                    cost_delta = rec.get('estimated_cost_delta', 0)
                                                    st.metric("Estimated Cost Impact", f"€{cost_delta}", delta=f"€{cost_delta}", delta_color="inverse")

                                                btn_col1, btn_col2 = st.columns([1, 1])
                                                with btn_col1:
                                                    if st.button("Accept", key=f"accept_{i}", type="primary"):
                                                        df_audit = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                                                        new_audit = pd.DataFrame([{
                                                            'TIMESTAMP': datetime.now().isoformat(),
                                                            'SOURCE_RESOURCE': rec.get('source_resource', ''),
                                                            'TARGET_BOTTLENECK': rec.get('target_bottleneck', ''),
                                                            'HOURS_TRANSFERRED': rec.get('hours_transferred', 0),
                                                            'ESTIMATED_COST_DELTA': rec.get('estimated_cost_delta', 0),
                                                            'NEW_SOURCE_UTIL': rec.get('new_source_utilization', ''),
                                                            'NEW_TARGET_UTIL': rec.get('new_target_utilization', ''),
                                                            'DECISION': 'ACCEPTED',
                                                            'RATIONALE': 'Accepted AI Recommendation'
                                                        }])
                                                        pd.concat([df_audit, new_audit], ignore_index=True).to_csv('data/resources/rebalancing_audit_log.csv', index=False)
                                                        st.success("Decision logged to Governance Audit Trail.")
                                                        try:
                                                            from lib.notifications import notify
                                                            payload = {
                                                                "Source": rec.get('source_resource', ''),
                                                                "Target": rec.get('target_bottleneck', ''),
                                                                "Hours": rec.get('hours_transferred', 0)
                                                            }
                                                            src = rec.get('source_resource', '')
                                                            tgt = rec.get('target_bottleneck', '')
                                                            if src: notify(src, 'REBALANCE_ACCEPTED', payload, channel='Both')
                                                            if tgt: notify(tgt, 'REBALANCE_ACCEPTED', payload, channel='Both')
                                                        except Exception:
                                                            pass
                                                with btn_col2:
                                                    if st.button("Reject", key=f"reject_{i}"):
                                                        df_audit = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                                                        new_audit = pd.DataFrame([{
                                                            'TIMESTAMP': datetime.now().isoformat(),
                                                            'SOURCE_RESOURCE': rec.get('source_resource', ''),
                                                            'TARGET_BOTTLENECK': rec.get('target_bottleneck', ''),
                                                            'HOURS_TRANSFERRED': rec.get('hours_transferred', 0),
                                                            'NEW_SOURCE_UTIL': rec.get('new_source_utilization', ''),
                                                            'NEW_TARGET_UTIL': rec.get('new_target_utilization', ''),
                                                            'DECISION': 'REJECTED',
                                                            'RATIONALE': 'PM Overrode AI Recommendation'
                                                        }])
                                                        pd.concat([df_audit, new_audit], ignore_index=True).to_csv('data/resources/rebalancing_audit_log.csv', index=False)
                                                        st.info("Decision logged to Governance Audit Trail.")
                                    else:
                                        st.error("AI returned unparseable recommendations.")
                                except Exception as e:
                                    st.error(f"Failed to parse AI rebalancing data: {e}")
                                
                    st.divider()
                    st.markdown("#### Governance Audit Trail — Last 5 Decisions")
                    try:
                        audit_df = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                        if not audit_df.empty:
                            st.dataframe(audit_df.tail(5), use_container_width=True, hide_index=True)
                        else:
                            st.info("No rebalancing decisions have been logged yet.")
                    except Exception:
                        st.info("No rebalancing decisions have been logged yet.")
                    
                    st.dataframe(resources[['TEAM_MEMBER', 'ROLE', 'SKILL', 'ALLOCATION_STATUS', 'UTILIZATION_PCT', 'PROJECT_ID']], use_container_width=True, hide_index=True)
                else:
                    st.info("No resource allocation data found")

    elif "System Integrations" in selected:
        render_page_header(
            "System Integrations",
            "Local data files, configured integration endpoints, and sync controls.",
        )

        # Refresh control
        if st.button("Refresh data list"):
            st.rerun()

        data_dir = Path("data")
        files = list(data_dir.rglob("*.csv")) if data_dir.exists() else []
        if files:
            st.markdown("#### Local CSV Data Files")
            # Grid of 3 columns for files
            file_cols = st.columns(3)
            for idx, f in enumerate(sorted(files)):
                col = file_cols[idx % 3]
                try:
                    stat = f.stat()
                    size_kb = stat.st_size / 1024
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    size_kb = 0.0
                    modified = "n/a"
                
                with col:
                    with st.expander(f.name, expanded=False):
                        # Metadata on the left, Open File button on the right
                        mcol1, mcol2 = st.columns([4, 1])
                        with mcol1:
                            st.markdown(
                                f'<div class="data-card">'
                                f'<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);">'
                                f'<span><b>Size:</b> {size_kb:.1f} KB</span>'
                                f'<span><b>Modified:</b> {modified}</span>'
                                f'</div>'
                                f'<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">'
                                f'<b>Path:</b> <code>{f}</code>'
                                f'</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        with mcol2:
                            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                            if st.button("Open", key=f"open_file_{f.parent.name}_{f.name}"):
                                try:
                                    import os
                                    os.startfile(str(f.resolve()))
                                except Exception as e:
                                    st.error(f"Failed to open: {e}")
                        try:
                            df_full = pd.read_csv(f)

                            is_log_file = 'log' in f.name.lower()
                            is_manager  = st.session_state.get('user_role') == 'Manager'

                            if not is_log_file and is_manager:
                                st.markdown(f"**Edit Data** ({len(df_full)} rows)")
                                edited_df = st.data_editor(
                                    df_full,
                                    use_container_width=True,
                                    num_rows="dynamic",
                                    key=f"editor_{f.parent.name}_{f.name}",
                                )
                                scol1, scol2 = st.columns([4, 1])
                                with scol2:
                                    if st.button("Save Changes", key=f"save_{f.parent.name}_{f.name}", use_container_width=True):
                                        try:
                                            edited_df.to_csv(f, index=False)
                                            log_data_edit('Manager', str(f))
                                            st.cache_data.clear()
                                            st.success(f"Saved {f.name}")
                                        except Exception as e:
                                            st.error(f"Failed to save: {e}")
                            else:
                                if is_log_file:
                                    st.caption(f"{len(df_full)} rows — Audit Log (Read-Only)")
                                else:
                                    st.caption(f"{len(df_full)} rows — View-Only")
                                st.dataframe(df_full, use_container_width=True)

                        except Exception as e:
                            st.error(f"Cannot load file: {e}")
        else:
            st.info("No CSV data files found under the `data/` folder.")

        st.markdown("#### Configured Integrations")
        # Validation helpers
        from urllib.parse import urlparse
        import re

        def is_valid_url(u):
            try:
                p = urlparse(str(u))
                return all([p.scheme in ('http', 'https'), p.netloc])
            except Exception:
                return False

        def is_valid_email(e):
            if not e:
                return False
            pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
            return re.match(pattern, str(e)) is not None

        def is_valid_port(p):
            try:
                v = int(p)
                return 0 < v < 65536
            except Exception:
                return False

        try:
            cfg = IntegrationScheduler().config
        except Exception:
            cfg = None

        # Editing unlock: require password if set via env var
        import os, difflib
        from dotenv import load_dotenv
        load_dotenv()
        ui_pw = os.getenv('INTEGRATIONS_UI_PASSWORD')
        if 'integrations_unlocked' not in st.session_state:
            st.session_state['integrations_unlocked'] = False

        if not st.session_state['integrations_unlocked']:
            if ui_pw:
                entered = st.text_input('Enter integrations UI password to unlock editing', type='password', key='ui_pw_input')
                if st.button('Unlock'):
                    if entered == ui_pw:
                        st.session_state['integrations_unlocked'] = True
                        st.success('Integrations editing unlocked')
                    else:
                        st.error('Incorrect password')
            else:
                st.warning('No INTEGRATIONS_UI_PASSWORD set — editing is allowed but not protected. Set INTEGRATIONS_UI_PASSWORD to require a password.')
                if st.checkbox('Enable editing (unsafe)', key='allow_edit_no_pw'):
                    st.session_state['integrations_unlocked'] = True


        def _mask(v):
            if v is None:
                return None
            s = str(v)
            low = s.lower()
            if any(k in low for k in ['key', 'secret', 'password', 'token', 'api_key', 'client_id']):
                return 'REDACTED'
            # mask long values
            if len(s) > 60:
                return s[:20] + '...' + s[-20:]
            return s

        if cfg:
            # Editable config UI
            try:
                import yaml as _yaml
            except Exception:
                _yaml = None

            # Integration metadata for display titles
            integration_meta = {
                'codebeamer':       'Codebeamer ALM',
                'jira':             'Jira Software',
                'email':            'SMTP Email Notifications',
                'github':           'GitHub / GitLab',
                'teams':            'Microsoft Teams',
                'confluence':       'Confluence Wiki',
                'sharepoint':       'SharePoint Documents',
                'powerbi':          'Power BI Reports',
                'polarion_doors':   'Polarion & DOORS',
                'test_mgmt':        'Test Management (TestRail/Xray)',
                'outlook_calendar': 'Outlook Calendar',
                'kb_rag':           'AI Knowledge Base (RAG)',
                'slack':            'Slack Channel',
                'asana':            'Asana Project Board',
            }

            edited_cfg = {}
            integration_cols = st.columns(3)
            for idx, (section, conf) in enumerate(cfg.items()):
                col = integration_cols[idx % 3]
                title = integration_meta.get(section, section.replace('_', ' ').title())
                with col:
                    with st.expander(title, expanded=False):
                        st.markdown(f"#### {title} Config")
                        if section in ['jira', 'polarion_doors', 'codebeamer']:
                            st.info("🔌 Status: Connected - License Pending")
                        if isinstance(conf, dict):
                            section_updates = {}
                            section_errors = []
                            
                            # Separate fields into normal (short) and complex (long) fields
                            normal_fields = []
                            complex_fields = []
                            for k, v in conf.items():
                                if isinstance(v, (list, dict)) or any(tok in k.lower() for tok in ['url', 'query', 'payload', 'body', 'description', 'recipients', 'users']):
                                    complex_fields.append((k, v))
                                else:
                                    normal_fields.append((k, v))

                            def render_field(k, v):
                                label = k.replace('_', ' ').title()
                                key_name = f"cfg_{section}_{k}"
                                disabled = not st.session_state.get('integrations_unlocked', False)
                                
                                if any(tok in k.lower() for tok in ['password', 'secret', 'token', 'api_key', 'pat', 'key']) and not isinstance(v, bool):
                                    new_val = st.text_input(label, value=str(v) if v is not None else '', key=key_name, type='password', disabled=disabled)
                                elif isinstance(v, bool):
                                    new_val = st.checkbox(label, value=bool(v), key=key_name, disabled=disabled)
                                elif isinstance(v, int):
                                    try:
                                        new_val = st.number_input(label, value=int(v), key=key_name, disabled=disabled)
                                    except Exception:
                                        new_val = st.text_input(label, value=str(v), key=key_name, disabled=disabled)
                                elif isinstance(v, list) or isinstance(v, dict):
                                    txt_key = f"cfg_{section}_{k}_yaml"
                                    try:
                                        txt = _yaml.safe_dump(v) if _yaml else str(v)
                                    except Exception:
                                        txt = str(v)
                                    new_txt = st.text_area(label, value=txt, height=120, key=txt_key, disabled=disabled)
                                    if _yaml:
                                        try:
                                            new_val = _yaml.safe_load(new_txt)
                                        except Exception:
                                            new_val = v
                                    else:
                                        new_val = v
                                else:
                                    new_val = st.text_input(label, value=str(v) if v is not None else '', key=key_name, disabled=disabled)
                                
                                # Inline validation
                                try:
                                    lowk = k.lower()
                                    if ('url' in lowk or lowk == 'url') and new_val:
                                        if not is_valid_url(new_val):
                                            st.warning(f"Field '{label}' does not look like a valid URL.")
                                    if 'email' in lowk or 'sender_email' in lowk:
                                        if new_val and not is_valid_email(new_val):
                                            st.warning(f"Field '{label}' does not look like a valid email.")
                                    if 'port' in lowk or lowk in ('smtp_port',):
                                        if new_val and not is_valid_port(new_val):
                                            st.warning(f"Field '{label}' does not look like a valid port number.")
                                except Exception:
                                    pass
                                
                                return new_val

                            # Render all fields full width inside the narrow column
                            for k, v in normal_fields:
                                section_updates[k] = render_field(k, v)

                            for k, v in complex_fields:
                                section_updates[k] = render_field(k, v)

                            # Actions stacked in 2 rows of 2 columns
                            st.divider()
                            confirm_key = f"confirm_save_{section}"
                            confirm = st.checkbox("Confirm save changes", value=False, key=confirm_key)
                            
                            action_col1, action_col2 = st.columns(2)
                            with action_col1:
                                if st.button("Save", key=f"btn_save_{section}"):
                                    # validation blocking
                                    if section_errors:
                                        st.error('Cannot save — validation errors exist:')
                                        for err in section_errors:
                                            st.write(f"- {err}")
                                    elif not confirm:
                                        st.error('Please check the confirmation box before saving.')
                                    else:
                                        # write back edited section into config file
                                        try:
                                            config_path = Path('integrations') / 'config.yaml'
                                            if _yaml is None:
                                                st.error('PyYAML not available in the environment; cannot save config from UI.')
                                            else:
                                                # load existing file to preserve comments
                                                full = _yaml.safe_load(open(config_path, 'r')) or {}
                                                before_section = full.get(section, {})
                                                full[section] = section_updates
                                                with open(config_path, 'w') as f:
                                                    _yaml.safe_dump(full, f)
                                                # write detailed audit entry
                                                log_path = Path('logs') / 'config_changes.log'
                                                log_path.parent.mkdir(exist_ok=True)
                                                with open(log_path, 'a', encoding='utf-8') as lf:
                                                    lf.write(f"{datetime.now().isoformat()} - Saved section: {section}\n")
                                                    try:
                                                        lf.write('BEFORE:\n')
                                                        lf.write(_yaml.safe_dump(before_section))
                                                    except Exception:
                                                        lf.write(str(before_section) + '\n')
                                                    lf.write('AFTER:\n')
                                                    try:
                                                        lf.write(_yaml.safe_dump(section_updates))
                                                    except Exception:
                                                        lf.write(str(section_updates) + '\n')
                                                    lf.write('----\n')
                                                st.success(f"Saved {section} to integrations/config.yaml")
                                                # reload scheduler config if possible
                                                try:
                                                    IntegrationScheduler().config = load_config('integrations/config.yaml')
                                                except Exception:
                                                    pass
                                        except Exception as e:
                                            st.error(f"Failed to save config: {e}")

                            with action_col2:
                                if st.button("Test Auth", key=f"btn_test_{section}"):
                                    # perform lightweight auth test depending on section
                                    try:
                                        import requests as _requests
                                    except Exception:
                                        _requests = None

                                    result_msg = None
                                    try:
                                        sec_conf = section_updates
                                        if section == 'codebeamer':
                                            url = sec_conf.get('url')
                                            headers = {}
                                            token = sec_conf.get('api_token')
                                            if token:
                                                headers['Authorization'] = f'Bearer {token}'
                                            elif sec_conf.get('username') and sec_conf.get('password'):
                                                import base64 as _b64
                                                creds = _b64.b64encode(f"{sec_conf.get('username')}:{sec_conf.get('password')}".encode()).decode()
                                                headers['Authorization'] = f'Basic {creds}'
                                            if _requests and url:
                                                r = _requests.get(url, headers=headers, timeout=10)
                                                result_msg = f"Status {r.status_code}: {r.reason}"
                                            else:
                                                result_msg = "requests package not available or URL missing"
                                        elif section == 'jira':
                                            url = sec_conf.get('url')
                                            auth = None
                                            if sec_conf.get('username') and sec_conf.get('api_token'):
                                                auth = (sec_conf.get('username'), sec_conf.get('api_token'))
                                            if _requests and url:
                                                r = _requests.get(url, auth=auth, timeout=10)
                                                result_msg = f"Status {r.status_code}: {r.reason}"
                                            else:
                                                result_msg = "requests package not available or URL missing"
                                        elif section == 'email':
                                            import smtplib as _smtplib
                                            server = sec_conf.get('smtp_server')
                                            port = int(sec_conf.get('smtp_port') or 0)
                                            user = sec_conf.get('sender_email')
                                            pwd = sec_conf.get('sender_password')
                                            if not server or not port:
                                                result_msg = 'SMTP server/port missing'
                                            else:
                                                try:
                                                    smtp = _smtplib.SMTP(server, port, timeout=10)
                                                    smtp.ehlo()
                                                    if port == 587:
                                                        smtp.starttls()
                                                        smtp.ehlo()
                                                    if user and pwd:
                                                        smtp.login(user, pwd)
                                                    smtp.quit()
                                                    result_msg = 'SMTP connection and auth OK'
                                                except Exception as e:
                                                    result_msg = f'SMTP error: {e}'
                                        else:
                                            # generic test: try GET to provided url-like fields
                                            candidate = sec_conf.get('url') or sec_conf.get('organization') or sec_conf.get('api_key')
                                            if _requests and candidate:
                                                try:
                                                    r = _requests.get(candidate, timeout=10)
                                                    result_msg = f"Status {r.status_code}: {r.reason}"
                                                except Exception as e:
                                                    result_msg = f"Request error: {e}"
                                            else:
                                                result_msg = 'No standard test implemented for this integration, or requests not installed.'

                                    except Exception as e:
                                        result_msg = f"Test failed: {e}"

                                    st.info(result_msg)

                            action_col3, action_col4 = st.columns(2)
                            with action_col3:
                                if st.button("Pull Data", key=f"btn_pull_{section}"):
                                    # trigger a sync for the integration where possible
                                    try:
                                        sched = IntegrationScheduler()
                                        if section == 'codebeamer':
                                            ok = sched.sync_codebeamer()
                                        elif section == 'jira':
                                            ok = sched.sync_jira()
                                        elif section == 'azure_devops' and getattr(sched, 'azure_devops', None):
                                            ok = sched.azure_devops.sync_all()
                                        elif section == 'monday_com' and getattr(sched, 'monday', None):
                                            ok = sched.monday.sync_all()
                                        elif section == 'asana' and getattr(sched, 'asana', None):
                                            ok = sched.asana.sync_all()
                                        else:
                                            ok = False
                                        if ok:
                                            st.success(f"{section} sync completed")
                                        else:
                                            st.warning(f"{section} sync empty or disabled")
                                    except Exception as e:
                                        st.error(f"Sync failed: {e}")

                            with action_col4:
                                if st.button("Revert", key=f"btn_revert_{section}"):
                                    # remove session keys for this section
                                    keys_to_remove = [k for k in st.session_state.keys() if k.startswith(f'cfg_{section}_')]
                                    for kk in keys_to_remove:
                                        try:
                                            del st.session_state[kk]
                                        except Exception:
                                            pass
                                    st.rerun()

                            # store both updates and errors
                            edited_cfg[section] = {'updates': section_updates, 'errors': section_errors}
                        else:
                            st.write(conf)

            # Global actions: Save All, Test All, Pull All
            st.divider()
            confirm_all = st.checkbox('Confirm save all integrations', value=False, key='confirm_save_all')
            gcol1, gcol2, gcol3 = st.columns(3)
            with gcol1:
                if st.button("Save All Integrations"):
                    try:
                        import yaml as _yaml
                    except Exception:
                        _yaml = None
                    if _yaml is None:
                        st.error('PyYAML not available; cannot save config from UI.')
                    else:
                        if not confirm_all:
                            st.error('Please check Confirm save all integrations before saving.')
                        else:
                            try:
                                config_path = Path('integrations') / 'config.yaml'
                                full = _yaml.safe_load(open(config_path, 'r')) or {}
                                # merge edited_cfg into full and record diffs
                                log_path = Path('logs') / 'config_changes.log'
                                log_path.parent.mkdir(exist_ok=True)
                                with open(log_path, 'a', encoding='utf-8') as lf:
                                    lf.write(f"{datetime.now().isoformat()} - Saved integrations config via UI\n")
                                for s, data in edited_cfg.items():
                                    updates = data.get('updates') if isinstance(data, dict) else data
                                    errors = data.get('errors') if isinstance(data, dict) else []
                                    if errors:
                                        continue
                                    before = full.get(s, {})
                                    full[s] = updates
                                    with open(log_path, 'a', encoding='utf-8') as lf:
                                        lf.write(f"Section: {s}\n")
                                        try:
                                            lf.write('BEFORE:\n')
                                            lf.write(_yaml.safe_dump(before))
                                        except Exception:
                                            lf.write(str(before) + '\n')
                                        lf.write('AFTER:\n')
                                        try:
                                            lf.write(_yaml.safe_dump(updates))
                                        except Exception:
                                            lf.write(str(updates) + '\n')
                                        lf.write('----\n')
                                with open(config_path, 'w') as f:
                                    _yaml.safe_dump(full, f)
                                st.success('Saved integrations/config.yaml')
                            except Exception as e:
                                st.error(f'Failed to save: {e}')
                if st.button('Preview Changes'):
                    try:
                        import yaml as _yaml
                    except Exception:
                        _yaml = None
                    config_path = Path('integrations') / 'config.yaml'
                    try:
                        full = _yaml.safe_load(open(config_path, 'r')) if _yaml else {}
                    except Exception:
                        full = {}
                    diffs = []
                    for s, updates in edited_cfg.items():
                        before = full.get(s, {})
                        try:
                            before_txt = _yaml.safe_dump(before).splitlines() if _yaml else str(before).splitlines()
                            after_txt = _yaml.safe_dump(updates).splitlines() if _yaml else str(updates).splitlines()
                        except Exception:
                            before_txt = str(before).splitlines()
                            after_txt = str(updates).splitlines()
                        d = list(difflib.unified_diff(before_txt, after_txt, fromfile=f'{s} (before)', tofile=f'{s} (after)', lineterm=''))
                        diffs.append((s, '\n'.join(d) if d else 'No changes'))
                    for s, d in diffs:
                        st.subheader(f'Preview: {s}')
                        st.code(d if d else 'No changes')

            with gcol2:
                if st.button('Test All Authentications'):
                    results = {}
                    try:
                        import requests as _requests
                    except Exception:
                        _requests = None
                    for s, conf in cfg.items():
                        try:
                            # reuse per-section logic where possible
                            if s == 'email':
                                import smtplib as _smtplib
                                server = conf.get('smtp_server')
                                port = int(conf.get('smtp_port') or 0)
                                try:
                                    smtp = _smtplib.SMTP(server, port, timeout=10)
                                    smtp.ehlo()
                                    if port == 587:
                                        smtp.starttls(); smtp.ehlo()
                                    smtp.quit()
                                    results[s] = 'OK'
                                except Exception as e:
                                    results[s] = f'Error: {e}'
                            else:
                                candidate = conf.get('url') or conf.get('organization') or None
                                if _requests and candidate:
                                    try:
                                        r = _requests.get(candidate, timeout=10)
                                        results[s] = f'{r.status_code} {r.reason}'
                                    except Exception as e:
                                        results[s] = f'Error: {e}'
                                else:
                                    results[s] = 'Skipping (no requests or no URL)'
                        except Exception as e:
                            results[s] = f'Error: {e}'
                    st.json(results)

            with gcol3:
                if st.button('Pull Data For All Enabled'):
                    sched = IntegrationScheduler()
                    run_results = {}
                    try:
                        run_results['codebeamer'] = sched.sync_codebeamer()
                    except Exception as e:
                        run_results['codebeamer'] = f'Error: {e}'
                    try:
                        run_results['jira'] = sched.sync_jira()
                    except Exception as e:
                        run_results['jira'] = f'Error: {e}'
                    # optional integrations
                    try:
                        if getattr(sched, 'azure_devops', None):
                            run_results['azure_devops'] = sched.azure_devops.sync_all()
                    except Exception as e:
                        run_results['azure_devops'] = f'Error: {e}'
                    try:
                        if getattr(sched, 'monday', None):
                            run_results['monday_com'] = sched.monday.sync_all()
                    except Exception as e:
                        run_results['monday_com'] = f'Error: {e}'
                    try:
                        if getattr(sched, 'asana', None):
                            run_results['asana'] = sched.asana.sync_all()
                    except Exception as e:
                        run_results['asana'] = f'Error: {e}'

                    st.json(run_results)
        else:
            st.info("No integrations configured or unable to load integration settings.")

    # Insights View

    # Upload Center View
    elif "Data Upload" in selected:
        render_page_header(
            "Data Upload",
            "Upload updated CSV files to refresh metrics, requirements, commits, and defects.",
        )
        
        file_mapping = {
            'Projects Status (projects_status.csv)': ('projects', 'projects_status.csv'),
            'Milestones (milestones.csv)': ('projects', 'milestones.csv'),
            'Budget Tracking (budget_tracking.csv)': ('projects', 'budget_tracking.csv'),
            'Risk Register (risk_register.csv)': ('risks', 'risk_register.csv'),
            'Resource Allocation (resource_allocation.csv)': ('resources', 'resource_allocation.csv'),
            'Defects (defects.csv)': ('metrics', 'defects.csv'),
            'Test Cases (test_execution.csv)': ('metrics', 'test_execution.csv'),
            'Requirements (requirements.csv)': ('metrics', 'requirements.csv'),
            'Issues (issues.csv)': ('projects', 'issues.csv'),
            'Escalations (escalations.csv)': ('projects', 'escalations.csv'),
            'ASPICE Compliance (aspice_status.csv)': ('metrics', 'aspice_status.csv'),
            'Change Request / Ticket Analysis (ecrs.csv)': ('projects', 'ecrs.csv'),
            'Development Commits (development_metrics.csv)': ('metrics', 'development_metrics.csv')
        }
        
        selected_file_type = st.selectbox("Select CSV file to replace/upload", list(file_mapping.keys()))
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file is not None:
            folder, filename = file_mapping[selected_file_type]
            target_path = Path("data") / folder / filename
            
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                
                if target_path.exists():
                    existing_df = pd.read_csv(target_path)
                    uploaded_cols = set(uploaded_df.columns)
                    existing_cols = set(existing_df.columns)
                    
                    missing_cols = existing_cols - uploaded_cols
                    extra_cols = uploaded_cols - existing_cols
                    
                    if missing_cols:
                        st.error(f"Validation Failed! Uploaded file is missing required columns: {list(missing_cols)}")
                    else:
                        if extra_cols:
                            st.warning(f"Note: Uploaded file contains extra columns that will be added: {list(extra_cols)}")
                        
                        if st.button(f"Confirm & Overwrite {filename}"):
                            uploaded_df.to_csv(target_path, index=False)
                            st.success(f"Successfully uploaded and replaced {target_path}!")
                            st.cache_data.clear()
                else:
                    if st.button(f"Save as New File {filename}"):
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        uploaded_df.to_csv(target_path, index=False)
                        st.success(f"Successfully created and saved {target_path}!")
                        st.cache_data.clear()
            except Exception as e:
                st.error(f"Error validating file: {e}")

        st.divider()
        st.markdown("#### AI Data Segregation")
        st.caption("Upload unstructured documents to extract and segregate data by category.")
        
        uploaded_seg_doc = st.file_uploader("Choose a document to segregate", type=['pptx', 'xlsx', 'txt'], key="seg_doc")
        
        if uploaded_seg_doc is not None:
            doc_type = uploaded_seg_doc.name.split('.')[-1].lower()
            with st.spinner("Parsing document..."):
                from lib.doc_parser import extract_text_from_file
                doc_text = extract_text_from_file(uploaded_seg_doc, doc_type)
            
            with st.expander("Preview Extracted Text"):
                st.text(doc_text[:1000] + ("..." if len(doc_text) > 1000 else ""))
                
            if st.button("✨ Extract & Segregate Data"):
                with st.spinner("Analyzing and segregating data with AI..."):
                    prompt = f"""Analyze the following text and segregate it into relevant datasets. Focus on:
1. **issues**: (summary, description, severity, status)
2. **risks**: (risk_description, probability, impact, mitigation)
3. **requirements**: (requirement_text, priority, status)
4. **team**: (resource_name, role, project_id)
5. **kpis**: (metric_name, value, target, status)

Format the response as a JSON object with keys: "issues", "risks", "requirements", "team", "kpis". Each key should contain a list of objects. Return ONLY valid JSON without markdown formatting.
Text:
{doc_text[:10000]}"""
                    response = get_completion(prompt, max_tokens=1500)
                    
                    try:
                        import json
                        import re
                        match = re.search(r'\{.*\}', response, re.DOTALL)
                        if match:
                            extracted_data = json.loads(match.group(0))
                            st.session_state['segregated_data'] = extracted_data
                        else:
                            st.error("Failed to parse AI response.")
                    except Exception as e:
                        st.error(f"Error parsing AI response: {e}")
                        
        if st.session_state.get('segregated_data'):
            st.success("AI successfully extracted the following data:")
            
            data_map = {
                "issues": {"file": "projects/issues.csv", "cols": ["ISSUE_TITLE", "DESCRIPTION", "SEVERITY", "STATUS", "ISSUE_ID", "PROJECT_ID"]},
                "risks": {"file": "risks/risk_register.csv", "cols": ["RISK_DESCRIPTION", "PROBABILITY", "IMPACT", "MITIGATION", "RISK_ID", "PROJECT_ID"]},
                "requirements": {"file": "metrics/requirements.csv", "cols": ["REQUIREMENT_TEXT", "PRIORITY", "STATUS", "REQUIREMENT_ID", "PROJECT_ID"]},
                "team": {"file": "resources/resource_allocation.csv", "cols": ["RESOURCE_NAME", "ROLE", "PROJECT_ID"]},
                "kpis": {"file": "metrics/kpis.csv", "cols": ["METRIC_NAME", "VALUE", "TARGET", "STATUS", "PROJECT_ID"]}
            }
            
            for key, items in st.session_state['segregated_data'].items():
                if items:
                    st.write(f"### {key.title()} ({len(items)})")
                    df = pd.DataFrame(items)
                    st.dataframe(df, use_container_width=True)
            
            st.divider()
            apply_mode = st.radio("How would you like to apply this data?", ["Append to existing CSVs", "Overwrite existing CSVs"], horizontal=True)

            if st.button("Apply Data to CSVs", type="primary"):
                for key, items in st.session_state['segregated_data'].items():
                    if items and key in data_map:
                        target_file = Path("data") / data_map[key]["file"]
                        new_df = pd.DataFrame(items)
                        
                        # Convert columns to uppercase to match CSV format
                        new_df.columns = [c.upper() for c in new_df.columns]
                        
                        # Handle potential column name mapping issues
                        if 'SUMMARY' in new_df.columns and key == 'issues':
                            new_df.rename(columns={'SUMMARY': 'ISSUE_TITLE'}, inplace=True)
                            
                        # Ensure required cols exist
                        for col in data_map[key]["cols"]:
                            if col not in new_df.columns:
                                new_df[col] = "AI_GEN" if "ID" in col else "N/A"
                                
                        if target_file.exists():
                            existing_df = pd.read_csv(target_file)
                            if apply_mode.startswith("Append"):
                                final_df = pd.concat([existing_df, new_df], ignore_index=True)
                            else:
                                final_df = new_df
                        else:
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            final_df = new_df
                            
                        final_df.to_csv(target_file, index=False)
                        st.success(f"Saved {len(items)} {key} to {target_file.name}")
                
                st.session_state['segregated_data'] = None
                st.cache_data.clear()

        st.divider()
        st.markdown("#### Transcript & Minutes Parser")
        st.caption("Upload raw text transcripts, meeting minutes, or emails to extract commitments and flag missing Jira tickets.")
        
        uploaded_doc = st.file_uploader("Choose a document", type=['txt', 'eml', 'pptx', 'xlsx'])
        if uploaded_doc is not None:
            doc_type = uploaded_doc.name.split('.')[-1].lower()
            with st.spinner("Parsing document..."):
                from lib.doc_parser import extract_text_from_file
                doc_text = extract_text_from_file(uploaded_doc, doc_type)
            
            with st.expander("Preview Extracted Text"):
                st.text(doc_text[:1000] + ("..." if len(doc_text) > 1000 else ""))
                
            if st.button("✨ Extract Implicit Commitments"):
                with st.spinner("Analyzing with AI..."):
                    prompt = f"""Analyze the following meeting transcript/document. Extract any implicit commitments, action items, or promises made during this conversation. 
Return a JSON array of objects with keys: 'assignee' (who is doing it), 'task_description' (what they are doing), 'deadline' (when it's due, or 'TBD'), 'issue_type' (Task/Bug).
Ensure the response is ONLY valid JSON.
Text:
{doc_text[:10000]}"""
                    response = get_completion(prompt, max_tokens=1000)
                    
                    try:
                        import json
                        import re
                        match = re.search(r'\[.*\]', response, re.DOTALL)
                        if match:
                            commitments = json.loads(match.group(0))
                            
                            # Cross-reference with Jira tickets (issues)
                            issues_df = data.get('issues', pd.DataFrame())
                            unticketed = []
                            for comm in commitments:
                                assignee = comm.get('assignee', '')
                                task = comm.get('task_description', '')
                                
                                # Simple semantic check: is there an issue assigned to this person with similar words?
                                is_ticketed = False
                                if not issues_df.empty and assignee:
                                    person_issues = issues_df[issues_df['ASSIGNED_TO'].str.contains(assignee, case=False, na=False)]
                                    for _, row in person_issues.iterrows():
                                        title = str(row.get('ISSUE_TITLE', '')).lower()
                                        words = set(task.lower().split())
                                        title_words = set(title.split())
                                        if len(words.intersection(title_words)) > 2:
                                            is_ticketed = True
                                            break
                                            
                                if not is_ticketed:
                                    unticketed.append(comm)
                                    
                            st.session_state['unticketed_commitments'] = unticketed
                            if not unticketed:
                                st.success("All extracted commitments already seem to have Jira tickets!")
                        else:
                            st.error("Failed to parse AI response. Please try again.")
                    except Exception as e:
                        st.error(f"Error parsing AI response: {e}")
                        
        if st.session_state.get('unticketed_commitments'):
            st.warning(f"Found {len(st.session_state['unticketed_commitments'])} implicit commitments without Jira tickets!")
            for i, ticket in enumerate(st.session_state['unticketed_commitments']):
                with st.container():
                    st.write(f"**Assignee:** {ticket.get('assignee', 'Unassigned')} | **Deadline:** {ticket.get('deadline', 'TBD')}")
                    st.write(f"**Task:** {ticket.get('task_description', '')}")
                    
                    if st.button(f"Generate Ticket {i+1}", key=f"create_ticket_{i}"):
                        from integrations.jira_sync import JiraSync
                        jira = JiraSync()
                        # Derive the active project key from the currently scoped project, if set
                        _active_project = st.session_state.get('selected_project', 'All')
                        project_key = _active_project if _active_project and _active_project != 'All' else 'P001'
                        issue_id = jira.create_issue(project_key, ticket.get('task_description', '')[:50], ticket.get('task_description', ''), ticket.get('issue_type', 'Task'))
                        if issue_id:
                            st.success(f"Successfully created Jira ticket: {issue_id}")
                            
                            # Append to issues.csv for local dashboard state
                            csv_path = Path("data") / "projects" / "issues.csv"
                            if csv_path.exists():
                                df_csv = pd.read_csv(csv_path)
                                new_row = {
                                    'ISSUE_ID': issue_id,
                                    'PROJECT_ID': project_key,
                                    'ISSUE_TITLE': ticket.get('task_description', '')[:50],
                                    'DESCRIPTION': ticket.get('task_description', ''),
                                    'SEVERITY': 'MEDIUM',
                                    'STATUS': 'OPEN',
                                    'ASSIGNED_TO': ticket.get('assignee', 'Unassigned'),
                                    'CREATED_DATE': datetime.now().strftime("%Y-%m-%d"),
                                    'RESOLUTION_DATE': 'N/A'
                                }
                                df_csv = pd.concat([df_csv, pd.DataFrame([new_row])], ignore_index=True)
                                df_csv.to_csv(csv_path, index=False)
                        else:
                            st.error("Failed to create Jira ticket.")

    # Audit Trail View
    elif "Audit Trail" in selected:
        st.title("🔍 System Action Log & Audit Trail")
        st.markdown("Inspect synchronization logs, user configuration audits, and scheduler execution traces.")
        
        log_dir = Path("logs")
        log_files = list(log_dir.glob("*.log")) if log_dir.exists() else []
        
        if log_files:
            log_names = [f.name for f in log_files]
            selected_log = st.selectbox("Select log file to inspect", log_names)
            log_path = log_dir / selected_log
            
            if log_path.exists():
                stat = log_path.stat()
                st.text(f"File size: {round(stat.st_size / 1024, 1)} KB | Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
                
                num_lines = st.slider("Number of lines to read", min_value=10, max_value=200, value=50)
                search_term = st.text_input("Filter log entries (case-insensitive search)")
                
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as lf:
                        lines = lf.readlines()
                        
                    if search_term:
                        filtered = [l for l in lines if search_term.lower() in l.lower()]
                    else:
                        filtered = lines
                        
                    tail_lines = filtered[-num_lines:]
                    st.code("".join(tail_lines), language='text')
                except Exception as e:
                    st.error(f"Failed to read log file: {e}")
        else:
            st.info("No system log files found.")

    # Strategic Insights View
    elif "AI Insights" in selected:
        render_page_header(
            "AI Insights",
            "Governance traceability analysis, lessons learned lookup, and AI-powered program recommendations.",
        )

        # ── Live KPI summary (calculated from data, AI fallback) ─────────────
        _projects   = data.get('projects',  pd.DataFrame())
        _risks      = data.get('risks',     pd.DataFrame())
        _tests      = data.get('tests',     pd.DataFrame())
        _resources  = data.get('resources', pd.DataFrame())
        _aspice     = data.get('aspice',    pd.DataFrame())

        # Portfolio health (reuse already-computed kpis)
        ph_score    = round(kpis.get('portfolio_health', 0), 1)
        otd_score   = round(kpis.get('on_time_delivery', 0), 1)
        tpr_score   = round(kpis.get('test_pass_rate', 0), 1)
        crit_risks  = int(kpis.get('critical_risks', 0))

        ph_status   = "HEALTHY" if ph_score >= 75 else ("WATCHLIST" if ph_score >= 60 else "CRITICAL")

        # Resource bottlenecks: any resource >= 110 % utilisation?
        bottlenecks = []
        if not _resources.empty and 'UTILIZATION_PCT' in _resources.columns:
            try:
                _res = _resources.copy()
                _res['_util'] = _res['UTILIZATION_PCT'].astype(str).str.rstrip('%').astype(float)
                _over = _res[_res['_util'] >= 110]
                for _, row in _over.iterrows():
                    name = row.get('TEAM_MEMBER') or row.get('RESOURCE_ID') or 'Unknown'
                    util = row['_util']
                    proj = row.get('PROJECT_ID', '')
                    bottlenecks.append(f"{name} at {util:.0f}% ({proj})")
            except Exception:
                pass

        # Build observation bullets from live data
        obs_lines = [
            f"**Portfolio Health:** {ph_score}% — status: **{ph_status}**",
            f"**On-Time Delivery:** {otd_score}%",
            f"**Test Pass Rate:** {tpr_score}%",
            f"**Critical Risks Open:** {crit_risks}",
        ]
        if bottlenecks:
            obs_lines.append(f"**Resource Bottlenecks:** {'; '.join(bottlenecks[:3])}")

        # Static fallback action plan (data-driven model not yet wired)
        action_lines = []
        if ph_score < 60:
            action_lines.append("Portfolio is CRITICAL — schedule an emergency steering committee review.")
        elif ph_score < 75:
            action_lines.append("Portfolio is in WATCHLIST — prioritise top-3 risks for mitigation this sprint.")
        if otd_score < 80:
            action_lines.append(f"On-time delivery ({otd_score}%) is below 80% — review milestone plans for slipping projects.")
        if tpr_score < 80:
            action_lines.append(f"Test pass rate ({tpr_score}%) is below 80% — run regression review and close critical defects first.")
        if crit_risks > 0:
            action_lines.append(f"{crit_risks} critical risk(s) require immediate owner assignment and mitigation action.")
        if not action_lines:
            action_lines.append("All key KPIs are on track. Continue current execution cadence.")

        obs_md   = "\n".join(f"{i+1}. {l}" for i, l in enumerate(obs_lines))
        act_md   = "\n".join(f"- {l}" for l in action_lines)

        st.info(f"**Key Observations (live data):**\n\n{obs_md}\n\n**Recommended Actions:**\n\n{act_md}")

        # Optional: AI narrative enhancement
        with st.expander("✨ Generate AI Narrative for these observations"):
            if st.button("Generate AI Insights Narrative"):
                with st.spinner("Generating AI narrative..."):
                    ai_prompt = (
                        f"You are an automotive engineering PMO advisor. Based on these live KPI observations, "
                        f"provide a 4-6 bullet executive narrative with specific, actionable next steps:\n\n"
                        f"{obs_md}\n\n{act_md}\n\n"
                        f"Keep it concise, factual, and suitable for a steering committee."
                    )
                    ai_narrative = get_completion(ai_prompt)
                if ai_narrative:
                    st.markdown(ai_narrative)
                else:
                    st.warning("AI narrative unavailable — ensure OPENAI_API_KEY is set.")
        
        st.divider()
        st.markdown("#### Governance & Traceability Analysis")
        
        with st.spinner("Analyzing traceability gaps..."):
            from lib.governance_agent import GovernanceAnalyzer
            gov_analyzer = GovernanceAnalyzer()
            gov_results = gov_analyzer.analyze_traceability(data)
            
            st.metric("Overall Traceability Score", f"{gov_results['score']:.1f}%")
            
            if gov_results['gaps']:
                st.warning(f"Detected {len(gov_results['gaps'])} governance gaps. Review required.")
                for gap in gov_results['gaps']:
                    st.error(f"**{gap['type']} ({gap['item']}):** {gap['description']}")
            else:
                st.success("No governance gaps detected. Traceability is 100%.")

        st.divider()
        st.markdown("#### Lessons Learned & Standards Lookup")
        
        rag_databases = [
            "All Databases (Federated Search)",
            "Automotive Lessons Learned (Internal - Project Histories)",
            "ISO 26262 Functional Safety Standards & Guidelines",
            "STRIDE Threat Modeling Definitions & Examples",
            "CFD & Thermal Simulation Best Practices"
        ]
        selected_rag = st.selectbox("Select Knowledge Base to Query:", options=rag_databases)
        
        # Simple local search lookup simulating RAG
        search_query = st.text_input("Search knowledge base for keywords (e.g., safety, CFD, security)")
        if search_query:
            st.markdown(f"**Search results for: *{search_query}***")
            
            results = []
            if "safety" in search_query.lower() or "iso" in search_query.lower() or "asil" in search_query.lower():
                results.append({
                    "Source": "Lessons Learned (Project P003)",
                    "Content": "ASIL decomposition from ASIL-D to ASIL-B(D) and ASIL-A(D) should be baselined at Change Request stage to avoid safety validation blockages during late-stage execution."
                })
                results.append({
                    "Source": "ISO 26262-6 Standard Reference",
                    "Content": "Part 6 details requirements for software development, verification, and compliance matrices corresponding to respective ASIL target levels."
                })
            elif "cfd" in search_query.lower() or "resource" in search_query.lower() or "thermal" in search_query.lower():
                results.append({
                    "Source": "Lessons Learned (Project P001)",
                    "Content": "CFD thermal analysis resource constraints can block prototype gates. Recommend scheduling backup engineering consultants at least 4 weeks in advance of design reviews."
                })
            elif "cyber" in search_query.lower() or "stride" in search_query.lower() or "security" in search_query.lower():
                results.append({
                    "Source": "Standards Reference (ISO 21434)",
                    "Content": "Requires STRIDE-based threat analysis and risk assessment (TARA) to establish cybersecurity requirement baselines for gateway modules."
                })
            else:
                results.append({
                    "Source": "KPI Hub general RAG database",
                    "Content": f"No direct standards match for '{search_query}'. Showing general lesson: Ensure daily/weekly commits and reviews are synced before steering committee audit."
                })
                
            for res in results:
                with st.expander(res['Source']):
                    st.write(res['Content'])

    # Copilot rendered directly in button callback now

if __name__ == "__main__":
    main()
