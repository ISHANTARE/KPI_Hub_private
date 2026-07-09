"""Page 1: Portfolio Overview - Executive Summary"""
import streamlit as st
import pandas as pd
import plotly.express as px
from lib.data_loader import load_data
from lib.kpi_engine import calculate_portfolio_kpis, get_status_label
from lib.styling import get_status_color, get_schedule_status_color

st.title("📊 Portfolio Overview")
st.markdown("Executive summary of all engineering projects")
st.divider()

# Load data
data = load_data()
projects = data['projects']
tests = data['tests']
defects = data['defects']

if projects.empty:
    st.error("❌ No project data found")
    st.stop()

# Calculate KPIs
kpis = calculate_portfolio_kpis(projects, tests, defects)

# Display KPI cards
st.subheader("📈 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Portfolio Health",
        f"{kpis['portfolio_health']}/100",
        delta=f"{get_status_label(kpis['portfolio_health'])}"
    )

with col2:
    st.metric(
        "On-Time Delivery",
        f"{kpis['on_time_delivery']}%",
        delta=None
    )

with col3:
    st.metric(
        "Quality Score",
        f"{kpis['quality_score']}/100",
        delta=None
    )

with col4:
    st.metric(
        "Test Pass Rate",
        f"{kpis['test_pass_rate']}%",
        delta=None
    )

st.divider()

# Project Status Distribution
st.subheader("🎯 Project Status Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    # Status chart
    status_counts = projects['SCHEDULE_STATUS'].value_counts()
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        color_discrete_map={"GREEN": "#10B981", "YELLOW": "#F59E0B", "RED": "#EF4444"},
        title="Schedule Status Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("Active Projects", len(projects))
    st.metric("Total Milestones", data['milestones'].shape[0] if not data['milestones'].empty else 0)
    st.metric("Total Tests", len(tests))
    st.metric("Open Defects", len(defects[defects['STATUS'] == 'OPEN']) if not defects.empty else 0)

st.divider()

# Project Health Scores
st.subheader("📊 Individual Project Health Scores")

projects_display = projects[['PROJECT_ID', 'PROJECT_NAME', 'STATUS', 'HEALTH_SCORE', 'SCHEDULE_STATUS']].copy()
projects_display.columns = ['Project ID', 'Project Name', 'Status', 'Health Score', 'Schedule']

fig = px.bar(
    projects,
    x='PROJECT_NAME',
    y='HEALTH_SCORE',
    color='SCHEDULE_STATUS',
    color_discrete_map={"GREEN": "#10B981", "YELLOW": "#F59E0B", "RED": "#EF4444"},
    title="Project Health Scores",
    labels={'HEALTH_SCORE': 'Health Score (0-100)', 'PROJECT_NAME': 'Project'}
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Projects table
st.subheader("📋 Projects Summary")
st.dataframe(
    projects_display,
    use_container_width=True,
    hide_index=True
)

st.info(
    "💡 **About Portfolio Overview:**\n"
    "- Shows aggregate metrics across all projects\n"
    "- Health scores calculated from schedule, budget, quality, and resources\n"
    "- Traffic lights indicate project status (Green=On Track, Yellow=At Risk, Red=Off Track)"
)
