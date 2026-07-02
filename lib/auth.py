"""
lib/auth.py
-----------
Authentication and Role-Based Access Control (RBAC) module for KPI Hub.

Two roles are supported:
  Manager — full access to all projects, budgets, and admin pages.
  Viewer  — read-only, scoped to assigned projects; budget data hidden.

User credentials are stored in config/users.yaml with bcrypt-hashed passwords.
"""

import logging
from pathlib import Path
from typing import List, Optional

import streamlit as st

logger = logging.getLogger(__name__)

# Page-level access restrictions: only Managers may visit these.
MANAGER_ONLY_PAGES = {"06_system_integrations", "07_data_upload"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_users() -> dict:
    """Load users from config/users.yaml. Returns empty dict on any error."""
    try:
        import yaml
        users_path = Path("config/users.yaml")
        if not users_path.exists():
            logger.warning("config/users.yaml not found — falling back to no-auth mode.")
            return {}
        with open(users_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("users", {})
    except Exception as e:
        logger.error(f"Failed to load users.yaml: {e}")
        return {}


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        import bcrypt
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_session_defaults() -> None:
    """Initialise auth-related session state keys."""
    defaults = {
        "authenticated": False,
        "username": None,
        "display_name": None,
        "user_role": "Viewer",
        "current_pm": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_authenticated() -> bool:
    """Return True if the current session has a verified user."""
    return bool(st.session_state.get("authenticated", False))


def login_form() -> None:
    """
    Render a centred login card and process credential submission.
    Sets session_state on success; shows an error banner on failure.
    """
    st.markdown(
        """
        <style>
        .login-wrapper {
            max-width: 420px;
            margin: 80px auto 0 auto;
            padding: 2.5rem 2rem;
            border-radius: 16px;
            background: var(--surface, #1e293b);
            border: 1px solid var(--border, #334155);
            box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        }
        .login-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--text-primary, #f1f5f9);
            text-align: center;
            margin-bottom: 0.25rem;
        }
        .login-sub {
            font-size: 0.85rem;
            color: var(--text-muted, #64748b);
            text-align: center;
            margin-bottom: 1.8rem;
        }
        </style>
        <div class="login-wrapper">
            <div class="login-title">🔐 KPI Hub</div>
            <div class="login-sub">Engineering PMO — Sign In</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="e.g. admin")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            users = _load_users()
            user_record = users.get(username.strip().lower())
            if user_record and _verify_password(password, user_record.get("password_hash", "")):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username.strip().lower()
                st.session_state["display_name"] = user_record.get("display_name", username)
                st.session_state["user_role"] = user_record.get("role", "Viewer")
                # Store explicitly scoped projects for Viewer accounts
                st.session_state["_user_projects"] = user_record.get("projects", [])
                logger.info(f"User '{username}' authenticated as {st.session_state['user_role']}.")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")


def logout() -> None:
    """Clear authentication state and force re-render to the login screen."""
    keys_to_clear = [
        "authenticated", "username", "display_name", "user_role",
        "current_pm", "_user_projects",
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
    st.cache_data.clear()
    st.rerun()


def get_accessible_projects(username: Optional[str] = None) -> Optional[List[str]]:
    """
    Return the list of PROJECT_IDs the current user may see.
    Returns None if the user is a Manager (unrestricted access).
    Returns a list (possibly empty) for Viewers.
    """
    role = st.session_state.get("user_role", "Viewer")
    if role == "Manager":
        return None  # Unrestricted

    # Explicit project list stored at login time
    explicit = st.session_state.get("_user_projects", [])
    if explicit:
        return [str(p) for p in explicit]

    # Fall back: derive from org_mapping.csv using display_name as MANAGER_NAME
    try:
        import pandas as pd
        org_df = pd.read_csv("data/resources/org_mapping.csv")
        display_name = st.session_state.get("display_name", "")
        scoped = (
            org_df[org_df["MANAGER_NAME"] == display_name]["PROJECT_ID"]
            .dropna()
            .unique()
            .tolist()
        )
        return [str(p) for p in scoped]
    except Exception:
        return []


def require_role(allowed_roles: List[str]) -> None:
    """
    Page-level RBAC guard. Call at the top of any page that has access restrictions.
    Stops execution and shows a friendly error if the current role is not permitted.
    """
    init_session_defaults()
    current_role = st.session_state.get("user_role", "Viewer")
    if current_role not in allowed_roles:
        st.error(
            f"🚫 **Access Denied** — Your role (*{current_role}*) does not have "
            f"permission to view this page."
        )
        st.info("Please contact your KPI Hub administrator to request access.")
        st.stop()
