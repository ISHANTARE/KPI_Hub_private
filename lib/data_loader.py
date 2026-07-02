# =============================================================================
# lib/data_loader.py
# -----------------------------------------------------------------------------
# Data loading and initialization utilities for the KPI Hub application.
# Extracted from web_app.py as part of the project-restructure refactor.
#
# Functions in this module:
#   - init_resource_cost_data(): Initialise cost_rates.csv and
#       monthly_utilization.csv when either file is absent.
#   - compute_traceability_insights(): (added in task 2.2)
#   - load_data(): (added in task 2.3)
# =============================================================================

import os
import logging
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def init_resource_cost_data():
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

    # 1b. Initialize action_log.csv if missing
    action_file = data_dir / "projects" / "action_log.csv"
    if not action_file.exists():
        action_file.parent.mkdir(parents=True, exist_ok=True)
        default_actions = [
            {"ACTION_ID": "ACT-001", "PROJECT_ID": "P001", "DESCRIPTION": "Review thermal simulation results", "STATUS": "Completed", "OWNER": "Engineering Manager", "DUE_DATE": "2026-05-15"},
            {"ACTION_ID": "ACT-002", "PROJECT_ID": "P001", "DESCRIPTION": "Update safety case baseline", "STATUS": "Done", "OWNER": "Safety Engineer", "DUE_DATE": "2026-06-01"},
            {"ACTION_ID": "ACT-003", "PROJECT_ID": "P002", "DESCRIPTION": "Validate motor controller firmware v2.1", "STATUS": "Open", "OWNER": "Controls Engineer", "DUE_DATE": "2026-07-10"},
            {"ACTION_ID": "ACT-004", "PROJECT_ID": "P003", "DESCRIPTION": "Complete cybersecurity TARA audit", "STATUS": "Completed", "OWNER": "Security Architect", "DUE_DATE": "2026-06-20"},
            {"ACTION_ID": "ACT-005", "PROJECT_ID": "P004", "DESCRIPTION": "Calibrate sensor fusion algorithm", "STATUS": "In Progress", "OWNER": "Senior Design Engineer", "DUE_DATE": "2026-07-30"}
        ]
        pd.DataFrame(default_actions).to_csv(action_file, index=False)

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

                start_date_str = r.get("START_DATE")
                end_date_str = r.get("END_DATE")
                try:
                    start_dt = pd.to_datetime(start_date_str) if pd.notna(start_date_str) else None
                    end_dt = pd.to_datetime(end_date_str) if pd.notna(end_date_str) else None
                except Exception:
                    start_dt = None
                    end_dt = None

                for month_name, year in months_list:
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


def compute_traceability_insights(requirements_df: pd.DataFrame, tests_df: pd.DataFrame) -> pd.DataFrame:
    if requirements_df.empty or tests_df.empty:
        return pd.DataFrame(columns=['REQUIREMENT_ID', 'TEST_ID', 'PROJECT_ID', 'CATEGORY', 'ISSUE_CATEGORY', 'ISSUE_TYPE', 'DETAILS'])

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
    except yaml.YAMLError as e:
        logger.warning(f"config.yaml YAML error: {e}. Proceeding with empty valid_mappings.")
    except Exception as e:
        logger.warning(f"Could not load config.yaml: {e}. Proceeding with empty valid_mappings.")

    for _, row in requirements_df.iterrows():
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


# =============================================================================
# Month helpers (used by sidebar/pages for month-range selectors)
# =============================================================================

_MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def _derive_month_range(util_df):
    """
    Return sorted list of (month_name, year) tuples from monthly_utilization.
    Falls back to rolling 12-month window if empty or malformed.
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
    from datetime import date
    today = date.today()
    out = []
    for i in range(12):
        m_idx = (today.month - 1 + i) % 12
        yr    = today.year + (today.month - 1 + i) // 12
        out.append((_MONTH_ORDER[m_idx], yr))
    return out


# =============================================================================
# Primary data loader
# =============================================================================

@st.cache_data
def load_data():
    data_dir = Path("data")

    try:
        init_resource_cost_data()
        
        # Hydrate DB from CSVs if DB tables don't exist
        from lib.database import sync_all_csvs_to_db, load_dataframe_from_db
        sync_all_csvs_to_db(force=False)

        projects = load_dataframe_from_db("projects")
        if projects.empty and (data_dir / "projects" / "projects_status.csv").exists():
            projects = pd.read_csv(data_dir / "projects" / "projects_status.csv")

        milestones = load_dataframe_from_db("milestones")
        budget = load_dataframe_from_db("budget")
        risks = load_dataframe_from_db("risks")
        resources = load_dataframe_from_db("resources")
        monthly_utilization = load_dataframe_from_db("monthly_utilization")
        cost_rates = load_dataframe_from_db("cost_rates")
        defects = load_dataframe_from_db("defects")
        tests = load_dataframe_from_db("tests")
        requirements = load_dataframe_from_db("requirements")
        issues = load_dataframe_from_db("issues")
        escalations = load_dataframe_from_db("escalations")
        aspice = load_dataframe_from_db("aspice")
        ecrs = load_dataframe_from_db("ecrs")
        forecast = load_dataframe_from_db("forecast")
        audit_log = load_dataframe_from_db("audit_log")
        decisions = load_dataframe_from_db("decisions")
        defect_trends = load_dataframe_from_db("defect_trends")
        dev_metrics = load_dataframe_from_db("dev_metrics")
        design_reviews = load_dataframe_from_db("design_reviews")
        verification = load_dataframe_from_db("verification")
        org_mapping = load_dataframe_from_db("org_mapping")
        actions = load_dataframe_from_db("actions")
        evm_history = load_dataframe_from_db("evm_history")
        subcontractors = load_dataframe_from_db("subcontractors")

        if ecrs.empty:
            ecrs = pd.DataFrame(columns=['ECR_ID', 'PROJECT_ID', 'TITLE', 'STATUS', 'CHANGE_TYPE', 'IMPACT_SCHEDULE_DAYS', 'IMPACT_COST'])
        if decisions.empty:
            decisions = pd.DataFrame(columns=['DECISION_ID', 'PROJECT_ID', 'TYPE', 'TITLE', 'APPROVAL_STATUS', 'DUE_DATE', 'OWNER'])
        if dev_metrics.empty:
            dev_metrics = pd.DataFrame(columns=['PROJECT_ID', 'WEEK_START', 'COMMITS_COUNT', 'PR_CYCLE_TIME_HOURS', 'CODE_REVIEWS_PENDING', 'CODE_REVIEWS_APPROVED', 'DEVELOPMENT_VELOCITY'])
        if design_reviews.empty:
            design_reviews = pd.DataFrame(columns=['PROJECT_ID', 'REVIEW_ID', 'STATUS', 'CRITICAL_ISSUES', 'ACTION_COMPLETION_PCT'])
        if verification.empty:
            verification = pd.DataFrame(columns=['VERIFICATION_ID', 'PROJECT_ID', 'STATUS', 'RESULT'])
        if actions.empty and (data_dir / "projects" / "action_log.csv").exists():
            actions = pd.read_csv(data_dir / "projects" / "action_log.csv")
        if evm_history.empty and (data_dir / "projects" / "evm_history.csv").exists():
            evm_history = pd.read_csv(data_dir / "projects" / "evm_history.csv")
        if subcontractors.empty and (data_dir / "resources" / "subcontractor_rates.csv").exists():
            subcontractors = pd.read_csv(data_dir / "resources" / "subcontractor_rates.csv")

        traceability_insights = compute_traceability_insights(requirements, tests)

        loaded_data = {
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
            'defect_trends': defect_trends,
            'org_mapping': org_mapping,
            'actions': actions,
            'evm_history': evm_history,
            'subcontractors': subcontractors,
        }

        # Apply role-based partitioning and budget confidentiality filtering
        from lib.auth import get_accessible_projects
        user_role = st.session_state.get("user_role", "Viewer")
        if user_role == "Viewer":
            accessible_projs = get_accessible_projects()
            if accessible_projs is not None:
                # Filter out projects they shouldn't see
                for key, df in loaded_data.items():
                    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                        if "PROJECT_ID" in df.columns:
                            loaded_data[key] = df[df["PROJECT_ID"].isin(accessible_projs)].reset_index(drop=True)
            
            # Hide budget and forecast tables entirely from Viewers
            if "budget" in loaded_data:
                loaded_data["budget"] = pd.DataFrame(columns=loaded_data["budget"].columns)
            if "forecast" in loaded_data:
                loaded_data["forecast"] = pd.DataFrame(columns=loaded_data["forecast"].columns)

        return loaded_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None
