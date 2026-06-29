"""
pages/04_testing_quality.py
---------------------------
Testing & Quality page for KPI Hub.
Extracted from web_app.py as part of the project-restructure refactor.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import lib.sidebar as sidebar
import lib.data_loader as data_loader
import lib.kpi_engine as kpi_engine
import lib.charts as charts
from lib.styling import render_page_header, COLORS, STATUS_COLORS
from lib.sidebar import apply_scope_filter

# ── Sidebar ───────────────────────────────────────────────────────────────────
sidebar.bootstrap_sidebar()

# ── Data ──────────────────────────────────────────────────────────────────────
data = data_loader.load_data()
if data is None:
    st.error("Could not load data.")
    st.stop()

# Scope filter
org_df = data.get('org_mapping', pd.DataFrame())
data = apply_scope_filter(
    data,
    st.session_state.get('current_manager', 'All'),
    st.session_state.get('current_project', 'All'),
    org_df,
)

kpis = kpi_engine.calculate_kpis(data)

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header(
    "Testing & Quality",
    "Test execution pass rates, defect severity distribution, and defect trends.",
)

defects = data.get('defects', pd.DataFrame())
tests = data.get('tests', pd.DataFrame())

# ── Quality KPI Summary Row ───────────────────────────────────────────────────
qc1, qc2, qc3, qc4 = st.columns(4)
with qc1:
    st.metric("Quality Score", f"{kpis.get('quality_score', 0):.0f} / 100", help="Computed inverse defect density metric")
with qc2:
    st.metric("Test Pass Rate", f"{kpis.get('test_pass_rate', 0):.1f}%")
with qc3:
    crit_def = len(defects[defects['SEVERITY'] == 'CRITICAL']) if not defects.empty and 'SEVERITY' in defects.columns else 0
    st.metric("Critical Defects", crit_def, delta=crit_def, delta_color="inverse")
with qc4:
    st.metric("Total Executed Tests", len(tests) if not tests.empty else 0)

st.divider()

# ── Weekly Defect Trend ───────────────────────────────────────────────────────
st.markdown("#### Weekly Defect Trend")
defect_trends = data.get('defect_trends', pd.DataFrame())
if not defect_trends.empty:
    trend_sum = defect_trends.groupby('WEEK')['OPEN_DEFECTS'].sum().reset_index()
    fig_trend = px.line(
        trend_sum,
        x='WEEK',
        y='OPEN_DEFECTS',
        markers=True,
        title="8-Week Open Defect Trend",
        color_discrete_sequence=['#ef4444'],
    )
    fig_trend.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#f8fafc',
        height=250,
        margin=dict(t=30, b=10, l=10, r=10),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No defect trend data available")

st.divider()

# ── Defect severity + Test execution pie charts ───────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Defect Severity Distribution")
    if not defects.empty and 'SEVERITY' in defects.columns:
        defect_sev = defects['SEVERITY'].value_counts()
        fig = px.pie(
            names=defect_sev.index,
            values=defect_sev.values,
            color=defect_sev.index,
            color_discrete_map={
                k: STATUS_COLORS.get(k, COLORS["text_muted"]) for k in defect_sev.index
            },
            hole=0.6,
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
            margin=dict(t=8, b=8, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.plotly_chart(
            charts.build_defect_severity_chart(defects), use_container_width=True
        )

with col2:
    st.markdown("#### Test Execution Status")
    if not tests.empty and 'STATUS' in tests.columns:
        test_status = tests['STATUS'].value_counts()
        fig = px.pie(
            names=test_status.index,
            values=test_status.values,
            color=test_status.index,
            color_discrete_map={
                k: STATUS_COLORS.get(k, COLORS["text_muted"]) for k in test_status.index
            },
            hole=0.6,
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
            margin=dict(t=8, b=8, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.plotly_chart(
            charts.build_test_execution_chart(tests), use_container_width=True
        )

# ── ASPICE Compliance ─────────────────────────────────────────────────────────
st.divider()
st.markdown("#### ASPICE Compliance")

aspice_df = data.get('aspice', pd.DataFrame())
fig_aspice = charts.build_aspice_radar_chart(aspice_df)
st.plotly_chart(fig_aspice, use_container_width=True)

# ── Traceability Heatmap ──────────────────────────────────────────────────────
st.divider()
st.markdown("#### Requirements Traceability Heatmap")

traceability_df = data.get('traceability_insights', pd.DataFrame())
fig_trace = charts.build_traceability_heatmap_chart(traceability_df)
st.plotly_chart(fig_trace, use_container_width=True)

# ── Functional Safety Requirements ───────────────────────────────────────────
st.divider()
st.markdown("#### Functional Safety Requirements")
st.caption(
    "ISO 26262 safety requirements with ASIL classification, verification method, "
    "and validation status."
)

from pathlib import Path as _Path
_safety_path = _Path('data/metrics/functional_safety_requirements.csv')
if _safety_path.exists():
    try:
        safety_df = pd.read_csv(_safety_path)
        if not safety_df.empty:
            # Summary metrics
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Total Safety Reqs", len(safety_df))

            if 'STATUS' in safety_df.columns:
                approved = len(safety_df[safety_df['STATUS'].str.upper() == 'APPROVED'])
                s2.metric("Approved", approved)

            if 'VALIDATION_STATUS' in safety_df.columns:
                verified = len(
                    safety_df[
                        safety_df['VALIDATION_STATUS'].str.upper().isin(
                            ['VERIFIED', 'PASSED', 'COMPLETED']
                        )
                    ]
                )
                s3.metric("Verified", verified)

            if 'ASIL_LEVEL' in safety_df.columns:
                asil_d = len(safety_df[safety_df['ASIL_LEVEL'].str.upper() == 'D'])
                s4.metric("ASIL-D Count", asil_d)

            # Full table
            desired_cols = [
                'SAFETY_REQ_ID', 'PROJECT_ID', 'SAFETY_REQUIREMENT', 'ASIL_LEVEL',
                'CATEGORY', 'STATUS', 'VERIFICATION_METHOD', 'VALIDATION_STATUS',
            ]
            disp_cols = [c for c in desired_cols if c in safety_df.columns]
            st.dataframe(safety_df[disp_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No functional safety requirements records found.")
    except Exception as e:
        st.error(f"Could not load functional safety requirements: {e}")
else:
    st.info(
        "Functional safety requirements file not found. "
        "Upload data/metrics/functional_safety_requirements.csv to populate."
    )
