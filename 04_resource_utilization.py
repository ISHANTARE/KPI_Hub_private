"""Page 4: Resource Utilization & Team Capacity"""
import streamlit as st
import pandas as pd
import plotly.express as px
from lib.data_loader import load_data

st.title("👥 Resource Utilization")
st.markdown("Team workload and capacity management")
st.divider()

data = load_data()
resources = data['resources']
projects = data['projects']

if resources.empty:
    st.error("❌ No resource data found")
    st.stop()

# Resource metrics
st.subheader("📊 Team Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Team Members", len(resources))

with col2:
    avg_util = resources['UTILIZATION_PCT'].mean() if 'UTILIZATION_PCT' in resources.columns else 0
    st.metric("Average Utilization", f"{avg_util:.1f}%")

with col3:
    overallocated = len(resources[resources['UTILIZATION_PCT'] > 100]) if 'UTILIZATION_PCT' in resources.columns else 0
    st.metric("Over-Allocated Members", overallocated, delta="⚠️" if overallocated > 0 else "✓")

st.divider()

# Utilization distribution
st.subheader("📈 Utilization Distribution")

col1, col2 = st.columns([1.5, 1])

with col1:
    fig = px.histogram(
        resources,
        x='UTILIZATION_PCT',
        nbins=10,
        title="Resource Utilization Distribution",
        labels={'UTILIZATION_PCT': 'Utilization (%)', 'count': 'Number of Resources'},
        color_discrete_sequence=["#3B82F6"]
    )
    fig.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="100% Capacity")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Capacity status
    underutil = len(resources[resources['UTILIZATION_PCT'] < 80])
    normal = len(resources[(resources['UTILIZATION_PCT'] >= 80) & (resources['UTILIZATION_PCT'] <= 100)])
    overutil = len(resources[resources['UTILIZATION_PCT'] > 100])
    
    capacity_status = {
        'Underutilized (<80%)': underutil,
        'Normal (80-100%)': normal,
        'Over-allocated (>100%)': overutil
    }
    
    fig = px.pie(
        values=list(capacity_status.values()),
        names=list(capacity_status.keys()),
        title="Capacity Status",
        color_discrete_map={
            'Underutilized (<80%)': '#9CA3AF',
            'Normal (80-100%)': '#10B981',
            'Over-allocated (>100%)': '#EF4444'
        }
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Team by role
st.subheader("👨‍💼 Team Members by Role")

if 'ROLE' in resources.columns:
    role_counts = resources['ROLE'].value_counts()
    fig = px.bar(
        x=role_counts.index,
        y=role_counts.values,
        title="Team Composition",
        labels={'x': 'Role', 'y': 'Count'},
        color_discrete_sequence=["#667eea"]
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Resources table
st.subheader("📋 Team Members Detail")

resources_display = resources[['RESOURCE_ID', 'ROLE', 'PROJECT_ID', 'UTILIZATION_PCT']].copy()
resources_display.columns = ['Name', 'Role', 'Project', 'Utilization %']

# Add color coding
resources_display_styled = resources_display.copy()
resources_display_styled['Utilization Status'] = resources_display['Utilization %'].apply(
    lambda x: '🟢 Normal' if 80 <= x <= 100 else '🔴 Over-allocated' if x > 100 else '🟡 Under-utilized'
)

st.dataframe(
    resources_display_styled,
    use_container_width=True,
    hide_index=True
)

# Alerts for over-allocation
if overallocated > 0:
    st.warning(
        f"⚠️ **{overallocated} team member(s) are over-allocated (>100% utilization).**\n\n"
        "Consider rebalancing work or hiring additional resources."
    )

st.info(
    "💡 **About Resource Utilization:**\n"
    "- Utilization % = (Allocated Hours / Available Hours) × 100\n"
    "- Normal: 80-100% (balanced workload)\n"
    "- Over-allocated: >100% (at risk of burnout)\n"
    "- Under-utilized: <80% (spare capacity available)"
)
