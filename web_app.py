# =============================================================================
# web_app.py — KPI Hub Entry Point
# =============================================================================

import streamlit as st
import lib.styling as styling
from lib.auth import init_session_defaults, is_authenticated, login_form

# Must be the first Streamlit call
st.set_page_config(
    page_title="KPI Hub — Engineering PMO",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject design system CSS
styling.load_css()

# Initialise session state auth defaults
init_session_defaults()

# ── Login gate ────────────────────────────────────────────────────────────────
# If the user is not authenticated, show the login form and stop execution here.
# The rest of the app (sidebar, pages) is only rendered after a successful login.
if not is_authenticated():
    login_form()
    st.stop()

# ── Authenticated — render full app ──────────────────────────────────────────
import lib.sidebar as sidebar
sidebar.bootstrap_sidebar()

# Default landing page — redirect to Portfolio Overview
st.switch_page("pages/01_portfolio_overview.py")
