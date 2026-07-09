"""Authentication module for KPI Hub MVP Demo"""
import streamlit as st
from pathlib import Path

# Demo credentials
DEMO_USERS = {
    "admin": {"password": "demo123", "role": "Admin", "name": "Admin User"},
    "viewer": {"password": "demo123", "role": "Viewer", "name": "Viewer User"},
}


def init_session_defaults():
    """Initialize session state defaults"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = "Viewer"


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def login_form():
    """Display login form"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""<h1 style='text-align: center;'>📊 KPI Hub MVP</h1>""", unsafe_allow_html=True)
        st.markdown("""<p style='text-align: center; font-size: 18px;'>Engineering Project Monitoring Dashboard</p>""", unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("### 🔐 Demo Login")
        
        username = st.text_input(
            "Username",
            placeholder="admin or viewer",
            key="login_username"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="demo123",
            key="login_password"
        )
        
        if st.button("Login", use_container_width=True, type="primary"):
            if username in DEMO_USERS and DEMO_USERS[username]["password"] == password:
                st.session_state.authenticated = True
                st.session_state.user_name = DEMO_USERS[username]["name"]
                st.session_state.user_role = DEMO_USERS[username]["role"]
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        
        st.divider()
        st.markdown("### 📝 Demo Credentials")
        st.info(
            "**Admin Account:**\n"
            "- Username: `admin`\n"
            "- Password: `demo123`\n\n"
            "**Viewer Account:**\n"
            "- Username: `viewer`\n"
            "- Password: `demo123`"
        )
        
        st.divider()
        st.markdown(
            "<p style='text-align: center; font-size: 12px; color: #666;'>KPI Hub MVP v1.0 | First Review Demo</p>",
            unsafe_allow_html=True
        )


def get_accessible_projects():
    """Get projects accessible by current user"""
    user_role = st.session_state.get("user_role", "Viewer")
    
    # For MVP, all users see all projects
    # In Phase 2, implement role-based access
    return ["P001", "P002", "P003"]
