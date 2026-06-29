"""
lib/user_preferences.py
------------------------
User preferences and session settings helper for KPI Hub.
Manages persistent filter selections, theme preferences, and user state.
"""

import streamlit as st
from typing import Dict, Any, Optional

DEFAULT_PREFERENCES = {
    "theme": "light",
    "favorite_project": "P001",
    "items_per_page": 25,
    "show_ai_tips": True
}

def get_user_preferences() -> Dict[str, Any]:
    """Retrieve current session user preferences."""
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = DEFAULT_PREFERENCES.copy()
    return st.session_state["user_preferences"]

def update_user_preference(key: str, value: Any) -> None:
    """Update a specific user preference setting."""
    prefs = get_user_preferences()
    prefs[key] = value
    st.session_state["user_preferences"] = prefs
