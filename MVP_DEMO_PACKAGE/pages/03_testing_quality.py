"""Page 3: Testing & Quality Metrics"""
import streamlit as st
import pandas as pd
import plotly.express as px
from lib.data_loader import load_data

st.title("🧪 Testing & Quality")
st.markdown("Test execution and defect tracking metrics")
st.divider()

data = load_data()
tests = data['tests']
defects = data['defects']

if tests.empty and defects.empty:
    st.error("❌ No testing or defect data found")
    st.stop()

# Test metrics
st.subheader("📊 Test Execution Summary")

if not tests.empty:
    total_tests = len(tests)
    passed = len(tests[tests['STATUS'] == 'PASSED'])
    failed = len(tests[tests['STATUS'] == 'FAILED'])
    blocked = len(tests[tests['STATUS'] == 'BLOCKED'])
    not_run = len(tests[tests['STATUS'] == 'NOT_RUN'])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Tests", total_tests)
    with col2:
        st.metric("Passed", passed, f"{passed/total_tests*100:.1f}%")
    with col3:
        st.metric("Failed", failed, f"{failed/total_tests*100:.1f}%")
    with col4:
        st.metric("Blocked", blocked)
    with col5:
        st.metric("Not Run", not_run)
    
    st.divider()
    
    # Test status distribution
    col1, col2 = st.columns([1, 1])
    
    with col1:
        status_counts = tests['STATUS'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Test Status Distribution",
            color_discrete_map={
                "PASSED": "#10B981",
                "FAILED": "#EF4444",
                "BLOCKED": "#F59E0B",
                "NOT_RUN": "#9CA3AF"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pass rate trend
        test_categories = tests['TEST_CATEGORY'].unique() if 'TEST_CATEGORY' in tests.columns else ['All']
        category_pass_rates = []
        for cat in test_categories:
            if cat != 'All':
                cat_tests = tests[tests['TEST_CATEGORY'] == cat]
            else:
                cat_tests = tests
            
            if len(cat_tests) > 0:
                pass_rate = (len(cat_tests[cat_tests['STATUS'] == 'PASSED']) / len(cat_tests)) * 100
                category_pass_rates.append({'Category': cat, 'Pass Rate': pass_rate})
        
        if category_pass_rates:
            fig = px.bar(
                category_pass_rates,
                x='Category',
                y='Pass Rate',
                title="Pass Rate by Test Category",
                labels={'Pass Rate': 'Pass Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)

st.divider()

# Defect metrics
st.subheader("🐛 Defect Tracking")

if not defects.empty:
    total_defects = len(defects)
    open_defects = len(defects[defects['STATUS'] == 'OPEN'])
    closed_defects = len(defects[defects['STATUS'] == 'CLOSED'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Defects", total_defects)
    with col2:
        st.metric("Open", open_defects)
    with col3:
        st.metric("Closed", closed_defects)
    
    st.divider()
    
    # Defect severity
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if 'SEVERITY' in defects.columns:
            severity_counts = defects['SEVERITY'].value_counts()
            fig = px.pie(
                values=severity_counts.values,
                names=severity_counts.index,
                title="Defect Severity Distribution",
                color_discrete_map={
                    "CRITICAL": "#EF4444",
                    "HIGH": "#F97316",
                    "MEDIUM": "#F59E0B",
                    "LOW": "#22C55E"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Defect by status
        status_dist = defects['STATUS'].value_counts()
        fig = px.bar(
            x=status_dist.index,
            y=status_dist.values,
            title="Defects by Status",
            color_discrete_sequence=["#EF4444", "#10B981"]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Defects table
    st.subheader("📋 Recent Defects")
    
    defects_display = defects[['DEFECT_ID', 'TITLE', 'SEVERITY', 'STATUS', 'CREATED_DATE']].head(10)
    st.dataframe(defects_display, use_container_width=True, hide_index=True)

st.info(
    "💡 **About Testing & Quality:**\n"
    "- Test Pass Rate = Passed Tests / Total Tests\n"
    "- Defect Severity indicates impact (Critical = Blocks release, High = Major feature affected)\n"
    "- Open defects tracked for resolution"
)
