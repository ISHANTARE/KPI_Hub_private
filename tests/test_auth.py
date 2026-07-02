import pytest
import streamlit as st
import pandas as pd
from lib.auth import init_session_defaults, is_authenticated, get_accessible_projects, require_role
from lib.data_loader import load_data

def test_auth_defaults():
    # Setup
    st.session_state.clear()
    init_session_defaults()
    
    assert st.session_state["authenticated"] is False
    assert st.session_state["user_role"] == "Viewer"
    assert is_authenticated() is False

def test_accessible_projects_manager():
    # Setup
    st.session_state.clear()
    init_session_defaults()
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = "Manager"
    
    assert get_accessible_projects() is None

def test_accessible_projects_viewer_explicit():
    # Setup
    st.session_state.clear()
    init_session_defaults()
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = "Viewer"
    st.session_state["_user_projects"] = ["P001", "P002"]
    
    assert get_accessible_projects() == ["P001", "P002"]

def test_require_role_allowed():
    # Setup
    st.session_state.clear()
    init_session_defaults()
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = "Manager"
    
    # Should not raise exception or call st.stop
    require_role(["Manager"])

def test_require_role_denied(monkeypatch):
    # Setup
    st.session_state.clear()
    init_session_defaults()
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = "Viewer"
    
    stopped = False
    def mock_stop():
        nonlocal stopped
        stopped = True
        raise Exception("Streamlit stopped execution")
        
    monkeypatch.setattr(st, "stop", mock_stop)
    monkeypatch.setattr(st, "error", lambda x: None)
    
    with pytest.raises(Exception, match="Streamlit stopped execution"):
        require_role(["Manager"])
    assert stopped is True
