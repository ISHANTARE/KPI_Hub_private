"""
tests/conftest.py
-----------------
Global pytest configuration for the project-restructure test suite.

Two responsibilities:
1.  Patch Streamlit symbols at *collection time* (module level) so that
    importing lib.* modules outside a running Streamlit server never raises
    AttributeError / RuntimeError.
2.  Provide the ``minimal_data`` session-scoped fixture that returns a
    22-key dict of empty DataFrames, each with the correct column schema
    from DATA_DICTIONARY.md.
"""

import sys
import types
import functools
import pytest
import pandas as pd

# ---------------------------------------------------------------------------
# 1.  Streamlit patching — applied at module import time
#     These are installed into sys.modules so every subsequent
#     ``import streamlit`` / ``import streamlit as st`` gets the stub.
# ---------------------------------------------------------------------------

def _identity_decorator(func=None, **kwargs):
    """Replacement for st.cache_data: acts as a no-op identity decorator."""
    if func is not None:
        # Called as @st.cache_data (without parens)
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        return wrapper
    else:
        # Called as @st.cache_data(...) with keyword args
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kw):
                return f(*args, **kw)
            return wrapper
        return decorator

# Give cache_data a .clear() no-op so sidebar code can call it
_identity_decorator.clear = lambda: None


def _noop(*args, **kwargs):
    """Generic no-op for st.error, st.warning, st.stop, etc."""
    pass


# Build a minimal streamlit stub module
_st_stub = types.ModuleType("streamlit")
_st_stub.cache_data = _identity_decorator
_st_stub.error = _noop
_st_stub.warning = _noop
_st_stub.stop = _noop
_st_stub.info = _noop
_st_stub.success = _noop
_st_stub.write = _noop
_st_stub.markdown = _noop
_st_stub.columns = lambda *a, **kw: [types.SimpleNamespace(
    markdown=_noop, metric=_noop, write=_noop,
    plotly_chart=_noop, dataframe=_noop, button=lambda *a, **kw: False,
    selectbox=lambda *a, **kw: None, expander=lambda *a, **kw: _NullCtx(),
    checkbox=lambda *a, **kw: False,
)]
_st_stub.expander = lambda *a, **kw: _NullCtx()
_st_stub.sidebar = types.SimpleNamespace(
    image=_noop, markdown=_noop, write=_noop,
    button=lambda *a, **kw: False,
    selectbox=lambda *a, **kw: None,
    expander=lambda *a, **kw: _NullCtx(),
)
_st_stub.session_state = {}
_st_stub.rerun = _noop
_st_stub.set_page_config = _noop
_st_stub.plotly_chart = _noop
_st_stub.dataframe = _noop
_st_stub.button = lambda *a, **kw: False
_st_stub.selectbox = lambda *a, **kw: None
_st_stub.text_input = lambda *a, **kw: ""
_st_stub.number_input = lambda *a, **kw: 0
_st_stub.date_input = lambda *a, **kw: None
_st_stub.radio = lambda *a, **kw: None
_st_stub.multiselect = lambda *a, **kw: []
_st_stub.checkbox = lambda *a, **kw: False
_st_stub.file_uploader = lambda *a, **kw: None
_st_stub.spinner = lambda *a, **kw: _NullCtx()
_st_stub.empty = lambda: types.SimpleNamespace(markdown=_noop, write=_noop)
_st_stub.tabs = lambda labels: [_NullCtx() for _ in labels]
_st_stub.metric = _noop
_st_stub.divider = _noop
_st_stub.caption = _noop
_st_stub.subheader = _noop
_st_stub.header = _noop
_st_stub.title = _noop
_st_stub.image = _noop
_st_stub.dialog = lambda *a, **kw: (lambda f: f)  # decorator no-op


class _NullCtx:
    """Context manager that swallows all attribute access and does nothing."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def __getattr__(self, name):
        return _noop


# Install stub before any lib module is imported
sys.modules.setdefault("streamlit", _st_stub)

# ---------------------------------------------------------------------------
# 2.  minimal_data fixture
#     Returns a 22-key dict of empty DataFrames with correct column schemas.
# ---------------------------------------------------------------------------

_SCHEMAS: dict[str, list[str]] = {
    "projects": [
        "PROJECT_ID", "PROJECT_NAME", "PROGRAM", "RELEASE", "PRODUCT_LINE",
        "STATUS", "PLANNED_END_DATE", "ACTUAL_END_DATE", "BASELINE_SCHEDULE",
        "CURRENT_SCHEDULE", "SCHEDULE_STATUS", "BUDGET_PLANNED", "BUDGET_SPENT",
        "BUDGET_STATUS", "RESOURCE_ALLOCATED", "RESOURCE_UTILIZED",
        "HEALTH_STATUS", "HEALTH_SCORE", "DELIVERY_CONFIDENCE", "NOTES",
    ],
    "milestones": [
        "MILESTONE_ID", "PROJECT_ID", "MILESTONE_NAME", "PLANNED_DATE",
        "ACTUAL_DATE", "BASELINE_DATE", "STATUS", "COMPLETION_PCT", "OWNER",
        "CRITICAL_PATH", "DEPENDENCIES", "NOTES",
    ],
    "budget": [
        "BUDGET_ID", "PROJECT_ID", "BUDGET_CATEGORY", "BUDGET_PERIOD",
        "PLANNED_AMOUNT", "COMMITTED_AMOUNT", "SPENT_AMOUNT",
        "VARIANCE_AMOUNT", "VARIANCE_PCT", "STATUS", "NOTES",
    ],
    "risks": [
        "RISK_ID", "PROJECT_ID", "RISK_TITLE", "DESCRIPTION", "IMPACT",
        "PROBABILITY", "EXPOSURE_SCORE", "SEVERITY", "STATUS", "OWNER",
        "MITIGATION_PLAN", "DUE_DATE", "CREATED_DATE", "DAYS_OPEN",
    ],
    "resources": [
        "PROJECT_ID", "TEAM_MEMBER", "ROLE", "SKILL",
        "ALLOCATED_HOURS_WEEKLY", "UTILIZED_HOURS_WEEKLY", "UTILIZATION_PCT",
        "DEPARTMENT", "START_DATE", "END_DATE", "ALLOCATION_STATUS", "NOTES",
    ],
    "monthly_utilization": [
        "RESOURCE_ID", "PROJECT_ID", "MONTH", "YEAR", "UTILIZATION_PCT",
    ],
    "cost_rates": [
        "ROLE", "COST_RATE_MONTHLY",
    ],
    "defects": [
        "DEFECT_ID", "PROJECT_ID", "TITLE", "DESCRIPTION", "SEVERITY",
        "STATUS", "FOUND_DATE", "FIXED_DATE", "DAYS_OPEN", "ROOT_CAUSE",
        "ASSIGNED_TO", "COMPONENT", "VERIFICATION_STATUS",
    ],
    "tests": [
        "TEST_ID", "PROJECT_ID", "TEST_SUITE", "TEST_CASE_NAME", "STATUS",
        "EXECUTION_DATE", "PASS_DATE", "FAIL_DATE", "DEFECT_ID",
        "AUTOMATION_STATUS", "TEST_CATEGORY", "COMPONENT", "ENVIRONMENT",
        "EXECUTIONS", "PASS_COUNT", "FAIL_COUNT",
    ],
    "requirements": [
        "REQUIREMENT_ID", "PROJECT_ID", "REQUIREMENT_TEXT", "CATEGORY",
        "PRIORITY", "STATUS", "APPROVED_DATE", "LAST_CHANGED", "CHANGE_COUNT",
        "TRACE_TEST_CASE", "TRACE_DESIGN", "VERIFICATION_STATUS", "ASIL_LEVEL",
    ],
    "issues": [
        "ISSUE_ID", "PROJECT_ID", "ISSUE_TITLE", "DESCRIPTION", "SEVERITY",
        "STATUS", "CREATED_DATE", "RESOLUTION_DATE", "DAYS_OPEN",
        "ASSIGNED_TO", "RELATED_RISK", "ESCALATION_LEVEL", "ROOT_CAUSE",
        "IMPACT",
    ],
    "escalations": [
        "ESCALATION_ID", "PROJECT_ID", "ESCALATION_TITLE", "ESCALATION_TYPE",
        "SEVERITY", "STATUS", "CREATED_DATE", "RESOLVED_DATE", "ESCALATED_TO",
        "ROOT_CAUSE", "BUSINESS_IMPACT", "RESOLUTION", "DAYS_OPEN",
    ],
    "aspice": [
        "ASPICE_PROCESS", "PROJECT_ID", "PROCESS_AREA", "TARGET_LEVEL",
        "CURRENT_LEVEL", "COMPLETION_PCT", "WORK_PRODUCTS_PLANNED",
        "WORK_PRODUCTS_COMPLETED", "REVIEWS_PLANNED", "REVIEWS_COMPLETED",
        "STATUS", "ASSESSMENT_READINESS", "COMMENTS",
    ],
    "ecrs": [
        "ECR_ID", "PROJECT_ID", "TITLE", "STATUS", "CHANGE_TYPE",
        "IMPACT_SCHEDULE_DAYS", "IMPACT_COST",
    ],
    "dev_metrics": [
        "PROJECT_ID", "WEEK_START", "COMMITS_COUNT", "PR_CYCLE_TIME_HOURS",
        "CODE_REVIEWS_PENDING", "CODE_REVIEWS_APPROVED", "DEVELOPMENT_VELOCITY",
    ],
    "design_reviews": [
        "PROJECT_ID", "REVIEW_ID", "STATUS", "CRITICAL_ISSUES",
        "ACTION_COMPLETION_PCT",
    ],
    "verification": [
        "VERIFICATION_ID", "PROJECT_ID", "STATUS", "RESULT",
    ],
    "traceability_insights": [
        "REQUIREMENT_ID", "TEST_ID", "PROJECT_ID", "CATEGORY",
        "ISSUE_CATEGORY", "ISSUE_TYPE", "DETAILS",
    ],
    # Empty-schema keys — no columns defined
    "forecast": [],
    "audit_log": [],
    "decisions": [
        "DECISION_ID", "PROJECT_ID", "TYPE", "TITLE",
        "APPROVAL_STATUS", "DUE_DATE", "OWNER",
    ],
    "defect_trends": [],
    "org_mapping": [
        "MANAGER_NAME", "PROJECT_ID", "TEAM_MEMBER", "ROLE", "EMAIL", "TEAMS_ID",
    ],
    "actions": [
        "ACTION_ID", "PROJECT_ID", "DESCRIPTION", "STATUS", "OWNER", "DUE_DATE",
    ],
}

assert len(_SCHEMAS) == 24, (
    f"Expected 24 keys in _SCHEMAS, got {len(_SCHEMAS)}: {sorted(_SCHEMAS)}"
)


@pytest.fixture(scope="session")
def minimal_data() -> dict[str, pd.DataFrame]:
    """
    22-key dict of empty DataFrames, each carrying the correct column schema
    from DATA_DICTIONARY.md.  Session-scoped so it is built once per test run.
    """
    return {
        key: pd.DataFrame(columns=cols)
        for key, cols in _SCHEMAS.items()
    }
