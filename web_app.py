# =============================================================================
# web_app.py — KPI Hub Entry Point
# =============================================================================

import streamlit as st
import lib.styling as styling
import lib.sidebar as sidebar

# Must be the first Streamlit call
st.set_page_config(
    page_title="KPI Hub — Engineering PMO",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject design system CSS
styling.load_css()

# Session state defaults
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Manager"
if "current_pm" not in st.session_state:
    st.session_state["current_pm"] = None

# Sidebar chrome
sidebar.bootstrap_sidebar()

# Default landing page — redirect to Portfolio Overview
st.switch_page("pages/01_portfolio_overview.py")
