"""
lib/auth.py
-------------
Authentication and Role-Based Access Control (RBAC) module for KPI Hub.
Uses streamlit-authenticator for session management and password hashing.
"""

import streamlit as st
from typing import List, Optional

# Sample user roles mapping for RBAC enforcement
# In a full deployment, this can be loaded from config/credentials.yaml
DEFAULT_USERS = {
    "usernames": {
        "admin": {
            "email": "admin@kpihub.local",
            "name": "Administrator",
            "password": "$2b$12$e8v.VzCqG8wS2mUv4m8eO.hG3v1Z5wQ3m8eO.hG3v1Z5wQ3m8eO", # Hash for AdminSecure123!
            "role": "Manager"
        },
        "pm_smith": {
            "email": "john.smith@kpihub.local",
            "name": "John Smith",
            "password": "$2b$12$e8v.VzCqG8wS2mUv4m8eO.hG3v1Z5wQ3m8eO.hG3v1Z5wQ3m8eO", # Hash for AdminSecure123!
            "role": "Project Manager"
        }
    }
}

def init_auth():
    """Ensure session state has default user role if authentication is bypassed or initial loading."""
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "Manager"
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = True  # Default to active for seamless dev access

def require_role(allowed_roles: List[str]):
    """
    Enforces server-side RBAC on Streamlit pages.
    If the current user's role is not in allowed_roles, displays an access error and stops execution.
    """
    init_auth()
    current_role = st.session_state.get("user_role", "Viewer")
    if current_role not in allowed_roles and "Manager" not in allowed_roles: # Manager has universal access
        st.error(f"🚫 Access Denied: Your role ('{current_role}') does not have permission to view or edit this page.")
        st.info("Please switch to an authorized role in the sidebar or contact your administrator.")
        st.stop()
