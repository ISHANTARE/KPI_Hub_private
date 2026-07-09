"""Data loading for KPI Hub MVP"""
import streamlit as st
import pandas as pd
from pathlib import Path


@st.cache_data
def load_data():
    """Load sample data from CSV files"""
    data_dir = Path(__file__).parent.parent / "data"
    
    data = {}
    
    # Load projects
    projects_file = data_dir / "projects.csv"
    if projects_file.exists():
        data['projects'] = pd.read_csv(projects_file)
    else:
        data['projects'] = pd.DataFrame()
    
    # Load tests
    tests_file = data_dir / "tests.csv"
    if tests_file.exists():
        data['tests'] = pd.read_csv(tests_file)
    else:
        data['tests'] = pd.DataFrame()
    
    # Load defects
    defects_file = data_dir / "defects.csv"
    if defects_file.exists():
        data['defects'] = pd.read_csv(defects_file)
    else:
        data['defects'] = pd.DataFrame()
    
    # Load resources
    resources_file = data_dir / "resources.csv"
    if resources_file.exists():
        data['resources'] = pd.read_csv(resources_file)
    else:
        data['resources'] = pd.DataFrame()
    
    # Load milestones
    milestones_file = data_dir / "milestones.csv"
    if milestones_file.exists():
        data['milestones'] = pd.read_csv(milestones_file)
    else:
        data['milestones'] = pd.DataFrame()
    
    return data
