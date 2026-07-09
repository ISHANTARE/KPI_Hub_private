# =============================================================================
# KPI Hub MVP Demo - Main Entry Point
# =============================================================================
# This is a simplified, standalone version showing 10-20% of full KPI Hub
# Perfect for first review / MVP demo

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.auth import init_session_defaults, is_authenticated, login_form
from lib.styling import load_css

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="KPI Hub MVP — Engineering PMO",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
load_css()

# Initialize session state
init_session_defaults()

# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATION GATE
# ═══════════════════════════════════════════════════════════════════════════

if not is_authenticated():
    login_form()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATED - SHOW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

# Show MVP badge
st.markdown(
    """
    <div style='background-color: #FFF3CD; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
        <h3 style='margin: 0;'>🎬 MVP DEMO - First Review (10-20% Scope)</h3>
        <p style='margin: 5px 0 0 0; font-size: 14px;'>Using sample data for demonstration</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar navigation
st.sidebar.title("📊 KPI Hub MVP")
st.sidebar.markdown("---")

user_name = st.session_state.get("user_name", "User")
user_role = st.session_state.get("user_role", "Viewer")
st.sidebar.write(f"**Logged in as:** {user_name}")
st.sidebar.write(f"**Role:** {user_role}")
st.sidebar.markdown("---")

# Navigation pages
pages = {
    "📊 Portfolio Overview": "pages/01_portfolio_overview.py",
    "❤️ Project Health": "pages/02_project_health.py",
    "🧪 Testing & Quality": "pages/03_testing_quality.py",
    "👥 Resource Utilization": "pages/04_resource_utilization.py",
    "🔌 API Documentation": "pages/05_api_documentation.py",
}

selected_page = st.sidebar.radio(
    "Navigate:",
    list(pages.keys()),
    key="page_selector"
)

st.sidebar.markdown("---")
st.sidebar.info(
    "📌 **MVP Features:**\n"
    "- Portfolio dashboard\n"
    "- Project health tracking\n"
    "- Test & quality metrics\n"
    "- Resource utilization\n"
    "- REST API showcase\n\n"
    "**Phase 2 will add:**\n"
    "- AI predictions\n"
    "- System integrations\n"
    "- ASPICE compliance\n"
    "- Advanced forecasting"
)

if st.sidebar.button("🚪 Logout", key="logout_btn"):
    st.session_state.authenticated = False
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# LOAD AND RUN SELECTED PAGE
# ═══════════════════════════════════════════════════════════════════════════

page_file = pages[selected_page]

try:
    with open(page_file, encoding="utf-8") as f:
        page_code = f.read()
        exec(page_code)
except FileNotFoundError:
    st.error(f"❌ Page not found: {page_file}")
except Exception as e:
    st.error(f"❌ Error loading page: {str(e)}")
