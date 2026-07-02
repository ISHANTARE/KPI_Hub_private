# =============================================================================
# lib/sidebar.py — KPI Hub shared sidebar chrome
# =============================================================================

import logging
import base64
import os
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

_SCOPE_FILTERED_KEYS = [
    "projects", "milestones", "budget", "risks", "resources",
    "monthly_utilization", "defects", "tests", "requirements",
    "issues", "escalations", "aspice", "ecrs", "dev_metrics",
    "design_reviews", "verification",
]

_NAV_ITEMS = [
    ("Portfolio Overview",   "pages/01_portfolio_overview.py",  None),
    ("Project Health",       "pages/02_project_health.py",      None),
    ("Dev Operations",       "pages/03_dev_operations.py",      None),
    ("Testing & Quality",    "pages/04_testing_quality.py",     None),
    ("Resource Utilization", "pages/05_resource_utilization.py",None),
    ("System Integrations",  "pages/06_system_integrations.py", "Manager"),
    ("Data Upload",          "pages/07_data_upload.py",         "Manager"),
    ("AI Insights",          "pages/08_ai_insights.py",         None),
    ("Scenario Simulation",  "pages/09_scenario_simulation.py", None),
]
# Third element = minimum required role (None = any authenticated user)


@st.cache_data
def _get_logo_b64() -> str:
    """Cache the logo base64 string so it's only encoded once per session."""
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        try:
            return base64.b64encode(logo_path.read_bytes()).decode()
        except Exception:
            pass
    return ""


def _current_page_stem() -> str:
    """
    Return the stem (filename without extension) of the page currently being
    executed, e.g. '01_portfolio_overview'.
    """
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    if ctx and hasattr(ctx, 'pages_manager') and ctx.pages_manager:
        pages = ctx.pages_manager.get_pages()
        page_info = pages.get(ctx.page_script_hash, {})
        script_path = page_info.get("script_path")
        if script_path:
            return Path(script_path).stem

    # Fallback to call stack inspection
    import inspect
    for frame_info in inspect.stack():
        fp = Path(frame_info.filename)
        if fp.parent.name == "pages":
            return fp.stem
    return ""


def bootstrap_sidebar() -> None:
    """
    Sidebar layout (top to bottom):
      1. Logo + KPI Hub title
      2. Logged-in user identity panel
      3. Navigation (filtered by role)
      4. Scope expander
      5. Refresh Data + Logout buttons
    """
    import yaml
    from lib.styling import load_css
    from lib.auth import logout, init_session_defaults

    # CSS is loaded once here; idempotent because Streamlit de-dupes <style> tags
    load_css()

    # Session state defaults
    init_session_defaults()

    # YAML config validity check
    if os.path.exists("integrations/config.yaml"):
        try:
            with open("integrations/config.yaml", "r") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as exc:
            st.error(f"config.yaml is malformed:\n```\n{exc}\n```")
            st.stop()

    # ── Detect current page for active-nav highlight ──────────────────────────
    active_stem = _current_page_stem()
    active_style = ""
    if active_stem:
        active_style = f"""
<style>
[data-testid="stSidebar"] div[class*="st-key-nav_{active_stem}"] button {{
    background:        var(--sidebar-hover) !important;
    color:             var(--sidebar-active) !important;
    border-left-color: var(--sidebar-accent) !important;
    font-weight:       600 !important;
}}
</style>"""

    # ── Logo + KPI Hub title ──────────────────────────────────────────────────
    b64 = _get_logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{b64}" '
        f'class="sidebar-logo" alt="Engineering PMO"/>'
    ) if b64 else ""

    st.sidebar.markdown(f"""
<div class="sidebar-brand">
    {logo_html}
    <div class="sidebar-brand-name">KPI Hub</div>
    <div class="sidebar-brand-sub">Engineering PMO &middot; KPI Hub</div>
</div>
{active_style}
""", unsafe_allow_html=True)
    st.sidebar.divider()

    # ── User identity panel ───────────────────────────────────────────────────
    current_role = st.session_state.get("user_role", "Viewer")
    display_name = st.session_state.get("display_name", "User")
    role_icon = "👑" if current_role == "Manager" else "👤"
    st.sidebar.markdown(
        f"""
<div style="padding:0.6rem 0.8rem;background:var(--surface-2,#1e293b);
            border-radius:10px;border:1px solid var(--border,#334155);
            margin-bottom:0.5rem;">
  <span style="font-weight:600;color:var(--text-primary,#f1f5f9);">
    {role_icon} {display_name}
  </span><br/>
  <span style="font-size:0.75rem;color:var(--text-muted,#64748b);">
    {current_role}
  </span>
</div>""",
        unsafe_allow_html=True,
    )

    # ── Navigation buttons (filtered by role) ────────────────────────────────
    for label, page_path, required_role in _NAV_ITEMS:
        # Hide Manager-only pages from Viewers
        if required_role == "Manager" and current_role != "Manager":
            continue
        slug = Path(page_path).stem
        if st.sidebar.button(label, key=f"nav_{slug}", width='stretch'):
            st.switch_page(page_path)

    st.sidebar.divider()

    # ── Scope expander ─────────────────────────────────────────────────────────
    with st.sidebar.expander("Scope", expanded=False):
        org_df_scope = pd.DataFrame()
        manager_options = ["All"]
        try:
            org_df_scope = pd.read_csv("data/resources/org_mapping.csv")
            if (st.session_state.get("user_role") == "Project Manager"
                    and st.session_state.get("current_pm")):
                manager_options = [st.session_state["current_pm"]]
            else:
                manager_options = ["All"] + sorted(
                    org_df_scope["MANAGER_NAME"].dropna().unique().tolist()
                )
        except Exception:
            pass

        selected_manager = st.selectbox(
            "Manager", options=manager_options, index=0, key="scope_manager"
        )

        proj_to_prog: dict = {}
        project_options = ["All"]
        try:
            raw_p = pd.read_csv("data/projects/projects_status.csv")
            if "PROJECT_ID" in raw_p.columns and "PROGRAM" in raw_p.columns:
                proj_to_prog = dict(zip(raw_p["PROJECT_ID"], raw_p["PROGRAM"]))
            if selected_manager != "All" and not org_df_scope.empty:
                mgr_projs = (
                    org_df_scope[org_df_scope["MANAGER_NAME"] == selected_manager]
                    ["PROJECT_ID"].dropna().unique().tolist()
                )
                project_options = ["All"] + sorted(mgr_projs)
        except Exception:
            pass

        selected_project = st.selectbox(
            "Project",
            options=project_options,
            index=0,
            key="scope_project",
            format_func=lambda x: f"{x} — {proj_to_prog.get(x, x)}" if x != "All" else "All",
        )

    st.session_state["current_manager"] = selected_manager
    st.session_state["current_project"] = selected_project

    # ── Refresh Data + Logout ─────────────────────────────────────────────────
    if st.sidebar.button("🔄 Refresh Data", key="refresh_data", width='stretch'):
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("🚪 Logout", key="logout_btn", width='stretch'):
        logout()


def apply_scope_filter(
    data: dict,
    selected_manager: str,
    selected_project: str,
    org_df: pd.DataFrame,
) -> dict:
    """Narrow the 16 PROJECT_ID-keyed DataFrames to the selected scope."""
    if not data:
        return data

    projects_df = data.get("projects", pd.DataFrame())
    valid_ids = set(projects_df["PROJECT_ID"].tolist()) if not projects_df.empty else set()

    if selected_manager != "All":
        if selected_project != "All":
            scoped = {selected_project}
        else:
            scoped = (
                set(org_df[org_df["MANAGER_NAME"] == selected_manager]["PROJECT_ID"].tolist())
                if not org_df.empty and "MANAGER_NAME" in org_df.columns
                else set()
            )
        valid_ids = valid_ids.intersection(scoped)

    valid_list = list(valid_ids)
    filtered = dict(data)
    for key in _SCOPE_FILTERED_KEYS:
        df = data.get(key)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            if "PROJECT_ID" in df.columns:
                filtered[key] = df[df["PROJECT_ID"].isin(valid_list)].reset_index(drop=True)

    return filtered
