"""
pages/03_dev_operations.py
--------------------------
Development Operations page for KPI Hub.
Extracted from web_app.py as part of the project-restructure refactor.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

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

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header(
    "Development Operations",
    "Commit trends, PR cycle times, code reviews, design reviews, and change requests.",
)

# ── Dev metrics charts ────────────────────────────────────────────────────────
dev_metrics = data.get('dev_metrics', pd.DataFrame())
design_rev = data.get('design_reviews', pd.DataFrame())

if len(dev_metrics) > 0:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Weekly Commit Count Trends")
        fig = px.line(
            dev_metrics,
            x='WEEK_START',
            y='COMMITS_COUNT',
            color='PROJECT_ID',
            markers=True,
            color_discrete_sequence=[
                COLORS["blue"], COLORS["green"], COLORS["amber"],
                COLORS["red"], COLORS["text_secondary"],
            ],
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
            margin=dict(t=8, b=8, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Average PR Cycle Time by Project")
        pr_summary = (
            dev_metrics.groupby('PROJECT_ID')['PR_CYCLE_TIME_HOURS']
            .mean()
            .reset_index()
        )
        fig = px.bar(
            pr_summary,
            x='PROJECT_ID',
            y='PR_CYCLE_TIME_HOURS',
            color='PR_CYCLE_TIME_HOURS',
            color_continuous_scale=[
                [0, COLORS["green"]],
                [0.5, COLORS["amber"]],
                [1, COLORS["red"]],
            ],
            labels={'PR_CYCLE_TIME_HOURS': 'PR Cycle Time (Hours)'},
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
            margin=dict(t=8, b=8, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info(
        "No development metrics data found. "
        "Configure GitHub/GitLab integration to pull code statistics."
    )

# ── Jira Ticket Analysis ──────────────────────────────────────────────────────
st.divider()
st.markdown("#### Jira Ticket Analysis: Planned vs Actual Hours")
st.caption(
    "Compare the estimated effort against actual logged hours. "
    "Requires active Jira API credentials to sync live data."
)

issues_log = data.get('issues', pd.DataFrame())
if (
    not issues_log.empty
    and 'PLANNED_HOURS' in issues_log.columns
    and 'ACTUAL_HOURS' in issues_log.columns
):
    _iss = issues_log.copy()
    _iss['PLANNED_HOURS'] = pd.to_numeric(_iss['PLANNED_HOURS'], errors='coerce')
    _iss['ACTUAL_HOURS'] = pd.to_numeric(_iss['ACTUAL_HOURS'], errors='coerce')
    _iss = _iss.dropna(subset=['PLANNED_HOURS', 'ACTUAL_HOURS'])

    if not _iss.empty:
        hover_cols = [c for c in ['ISSUE_ID', 'ISSUE_TITLE', 'ASSIGNED_TO'] if c in _iss.columns]
        fig = px.scatter(
            _iss,
            x='PLANNED_HOURS',
            y='ACTUAL_HOURS',
            color='STATUS',
            hover_data=hover_cols,
            labels={
                'PLANNED_HOURS': 'Planned Hours',
                'ACTUAL_HOURS': 'Actual Hours Logged',
            },
            color_discrete_map={
                k: STATUS_COLORS.get(k, COLORS["blue"])
                for k in _iss['STATUS'].unique()
            },
        )
        # Perfect-estimation reference line (y = x)
        max_val = max(_iss['PLANNED_HOURS'].max(), _iss['ACTUAL_HOURS'].max())
        fig.add_shape(
            type="line",
            line=dict(dash="dash", color="#94a3b8"),
            x0=0, y0=0, x1=max_val, y1=max_val,
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='#f8fafc',
            font=dict(color='#475569', family='Inter, sans-serif'),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No issues with both planned and actual hours recorded yet.")
else:
    st.info(
        "PLANNED_HOURS / ACTUAL_HOURS columns not found in issues data. "
        "Sync from Jira to populate."
    )

# ── Design & Code Architecture Reviews ───────────────────────────────────────
st.divider()
st.markdown("#### Design & Code Architecture Reviews")

if len(design_rev) > 0:
    disp_cols = [
        c for c in
        ['DESIGN_REVIEW_ID', 'PROJECT_ID', 'REVIEW_TYPE', 'REVIEW_DATE',
         'DESIGN_PHASE', 'STATUS', 'ACTION_COMPLETION_PCT']
        if c in design_rev.columns
    ]
    st.dataframe(design_rev[disp_cols], use_container_width=True, hide_index=True)
else:
    st.info("No design reviews data available.")

# ── Change Request Analysis ───────────────────────────────────────────────────
st.divider()
st.markdown("#### Change Request Analysis")
st.caption(
    "Formal governance trail for all ASIL deviations and architecture changes."
)

ecr_path = Path('data/projects/ecrs.csv')
if ecr_path.exists():
    try:
        ecrs = pd.read_csv(ecr_path)

        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Total Change Requests", len(ecrs))
        ec2.metric(
            "Pending Approval",
            len(ecrs[ecrs['STATUS'].str.upper() == 'PENDING']),
        )
        ec3.metric(
            "Total Cost Impact",
            f"€{ecrs['IMPACT_COST'].sum():,.0f}",
        )

        disp_ecr_cols = [
            c for c in
            ['ECR_ID', 'TITLE', 'STATUS', 'CHANGE_TYPE', 'IMPACT_SCHEDULE_DAYS',
             'IMPACT_COST', 'LINKED_REQUIREMENT', 'APPROVAL_DATE', 'DECISION_REASON']
            if c in ecrs.columns
        ]
        st.dataframe(ecrs[disp_ecr_cols], use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not load change requests: {e}")
else:
    st.info("No Engineering Change Requests found in database.")
