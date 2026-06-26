# =============================================================================
# lib/sidebar.py — KPI Hub shared sidebar chrome
# =============================================================================

import logging
import base64
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
    ("Portfolio Overview",   "pages/01_portfolio_overview.py"),
    ("Project Health",       "pages/02_project_health.py"),
    ("Dev Operations",       "pages/03_dev_operations.py"),
    ("Testing & Quality",    "pages/04_testing_quality.py"),
    ("Resource Utilization", "pages/05_resource_utilization.py"),
    ("System Integrations",  "pages/06_system_integrations.py"),
    ("Data Upload",          "pages/07_data_upload.py"),
    ("AI Insights",          "pages/08_ai_insights.py"),
]


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


def bootstrap_sidebar() -> None:
    """
    Sidebar layout (top to bottom):
      1. Logo — centered
      2. KPI Hub title
      3. Navigation (8 pages only, Streamlit built-in nav hidden)
      4. Scope expander
      5. Refresh Data button
    Light themed.
    """
    import yaml, os

    # Session state defaults
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "Manager"

    # YAML config validity check
    if os.path.exists("integrations/config.yaml"):
        try:
            with open("integrations/config.yaml", "r") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as exc:
            st.error(f"config.yaml is malformed:\n```\n{exc}\n```")
            st.stop()

    # ── Hide Streamlit's built-in nav + style our buttons as nav items ───────
    st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }

/* Smooth fade-in to reduce sidebar flash on page transitions */
[data-testid="stSidebar"] {
    animation: sidebar-fadein 0.18s ease-in;
}
@keyframes sidebar-fadein {
    from { opacity: 0.3; }
    to   { opacity: 1;   }
}

div[data-testid="stSidebar"] div.stButton > button {
    background: transparent !important;
    border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 6px 6px 0 !important;
    color: #1F2937 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    text-align: left !important;
    padding: 7px 14px 7px 12px !important;
    width: 100% !important;
    box-shadow: none !important;
    margin: 1px 0 !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stSidebar"] div.stButton > button:hover {
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    border-left-color: #93C5FD !important;
}
</style>
""", unsafe_allow_html=True)

    # ── Logo ─────────────────────────────────────────────────────────────────
    b64 = _get_logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{b64}" '
        f'style="width:130px;display:block;margin:0 auto;" '
        f'alt="Engineering PMO"/>'
    ) if b64 else ""

    # ── Logo + KPI Hub title ──────────────────────────────────────────────────
    st.sidebar.markdown(f"""
<div style="text-align:center;padding:18px 10px 14px 10px;">
    {logo_html}
    <div style="font-size:20px;font-weight:700;color:#0F1923;
                letter-spacing:0.3px;margin-top:10px;
                font-family:Inter,sans-serif;">KPI Hub</div>
    <div style="font-size:11px;color:#64748B;margin-top:2px;
                font-family:Inter,sans-serif;">
        Engineering PMO &middot; KPI Hub
    </div>
</div>
""", unsafe_allow_html=True)

    st.sidebar.divider()

    # ── Navigation buttons ───────────────────────────────────────────────────
    for label, page_path in _NAV_ITEMS:
        slug = Path(page_path).stem
        if st.sidebar.button(label, key=f"nav_{slug}", use_container_width=True):
            st.switch_page(page_path)

    st.sidebar.divider()

    # ── Scope expander ────────────────────────────────────────────────────────
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

    # ── Refresh Data ──────────────────────────────────────────────────────────
    if st.sidebar.button("Refresh Data", key="refresh_data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


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
