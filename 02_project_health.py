"""Page 2: Project Health Details"""
import streamlit as st
import pandas as pd
import plotly.express as px
from lib.data_loader import load_data
from lib.kpi_engine import get_status_label
from lib.styling import get_status_color

st.title("❤️ Project Health")
st.markdown("Detailed health analysis for individual projects")
st.divider()

data = load_data()
projects = data['projects']

if projects.empty:
    st.error("❌ No project data found")
    st.stop()

# Project selector
selected_project = st.selectbox(
    "Select a Project:",
    options=projects['PROJECT_NAME'].tolist(),
    index=0
)

# Get selected project data
project = projects[projects['PROJECT_NAME'] == selected_project].iloc[0]

st.subheader(f"📌 {project['PROJECT_NAME']}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    health = project['HEALTH_SCORE']
    color = "🟢" if health >= 80 else "🟡" if health >= 60 else "🔴"
    st.metric("Health Score", f"{health}/100", f"{color} {get_status_label(health)}")

with col2:
    status = project['SCHEDULE_STATUS']
    status_label, _ = get_status_color(health) if status == 'GREEN' else ("At Risk", None)
    st.metric("Schedule Status", status, "GREEN" if status == 'GREEN' else "AT RISK" if status == 'YELLOW' else "CRITICAL")

with col3:
    st.metric("Budget Used", f"{project.get('BUDGET_USED_PCT', 0)}%")

with col4:
    st.metric("Status", project['STATUS'])

st.divider()

# Health breakdown
st.subheader("📊 Health Score Breakdown")

col1, col2 = st.columns([1, 2])

with col1:
    metrics = {
        "Schedule Performance": project.get('SCHEDULE_VARIANCE', 0),
        "Budget Variance": project.get('BUDGET_VARIANCE', 0),
        "Quality Index": project.get('QUALITY_INDEX', 85),
        "Resource Capacity": project.get('RESOURCE_CAPACITY', 80),
    }
    
    for metric_name, metric_value in metrics.items():
        st.metric(metric_name, f"{metric_value}%")

with col2:
    # Metrics chart
    fig = px.bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        title="Health Metrics Breakdown",
        labels={'x': 'Metric', 'y': 'Score (%)'}
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Health trend
st.subheader("📈 Health Trend (Last 6 Months)")

trend_data = {
    'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    'Health Score': [75, 76, 77, 79, 81, 82]
}

fig = px.line(
    trend_data,
    x='Month',
    y='Health Score',
    markers=True,
    title="Project Health Trend",
    labels={'Health Score': 'Score (0-100)'}
)
fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target: 80+")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Project details
st.subheader("📝 Project Details")

details_df = pd.DataFrame({
    'Attribute': ['Project ID', 'Status', 'Team Size', 'Budget', 'Start Date', 'Target End Date'],
    'Value': [
        project['PROJECT_ID'],
        project['STATUS'],
        project.get('TEAM_SIZE', 'N/A'),
        f"${project.get('BUDGET', 0):,.0f}",
        project.get('START_DATE', 'N/A'),
        project.get('END_DATE', 'N/A')
    ]
})

st.dataframe(details_df, use_container_width=True, hide_index=True)

st.info(
    "💡 **About Project Health:**\n"
    "- Calculated from multiple factors: schedule, budget, quality, and resources\n"
    "- Score ranges 0-100 (Excellent: 90+, Healthy: 75-89, Watchlist: 60-74, Critical: <60)\n"
    "- Red flags trigger alerts for project managers"
)
