"""
lib/tenancy.py
--------------
Multi-Tenancy context isolation helper for KPI Hub.
Manages tenant identification, organization context, and data filtering across multi-tenant deployments.
"""

import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd

DEFAULT_TENANT_ID = "tenant_default"

def get_current_tenant_id() -> str:
    """Retrieve the active tenant ID from session state or environment."""
    if "tenant_id" not in st.session_state:
        st.session_state["tenant_id"] = DEFAULT_TENANT_ID
    return st.session_state["tenant_id"]

def set_tenant_context(tenant_id: str) -> None:
    """Set active tenant context."""
    st.session_state["tenant_id"] = tenant_id

def filter_dataframe_by_tenant(df: pd.DataFrame, tenant_column: str = "TENANT_ID") -> pd.DataFrame:
    """
    Filters a DataFrame by the active tenant ID if the tenant_column exists.
    If tenant_column is absent, returns the original DataFrame (backwards compatibility).
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    if tenant_column in df.columns:
        active_tenant = get_current_tenant_id()
        return df[df[tenant_column] == active_tenant].reset_index(drop=True)
    
    return df
