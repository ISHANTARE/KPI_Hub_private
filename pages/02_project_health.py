"""
pages/02_project_health.py
--------------------------
Project Health & Schedule page for KPI Hub.
Extracted from web_app.py as part of the project-restructure refactor.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime

import lib.sidebar as sidebar
import lib.data_loader as data_loader
import lib.kpi_engine as kpi_engine
import lib.charts as charts
from lib.styling import render_page_header, badge, severity_badge, COLORS, STATUS_COLORS
from lib.sidebar import apply_scope_filter


def _log_data_edit(role: str, file_path: str) -> None:
    """Append one audit row to data/resources/data_edit_log.csv."""
    log_file = Path('data/resources/data_edit_log.csv')
    if not log_file.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("TIMESTAMP,ROLE,FILE_EDITED,ACTION\n")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{role},{file_path},File Saved\n"
        )


# ── Sidebar ───────────────────────────────────────────────────────────────────
sidebar.bootstrap_sidebar()

# ── Data ──────────────────────────────────────────────────────────────────────
data = data_loader.load_data()
if data is None:
    st.error("Could not load data.")
    st.stop()

# Role-based budget visibility
if st.session_state.get('user_role') != 'Manager':
    if st.session_state.get('user_role') == 'Project Manager' and st.session_state.get('current_pm'):
        try:
            org_f = pd.read_csv('data/resources/org_mapping.csv')
            pm_projs = (
                org_f[org_f['MANAGER_NAME'] == st.session_state['current_pm']]['PROJECT_ID']
                .dropna()
                .unique()
                .tolist()
            )
            data['budget'] = (
                data['budget'][data['budget']['PROJECT_ID'].isin(pm_projs)]
                .reset_index(drop=True)
            )
        except Exception:
            pass
    else:
        data['budget'] = pd.DataFrame(columns=data.get('budget', pd.DataFrame()).columns)

# Scope filter
org_df = pd.DataFrame()
try:
    org_df = pd.read_csv('data/resources/org_mapping.csv')
except Exception:
    pass
data = apply_scope_filter(
    data,
    st.session_state.get('current_manager', 'All'),
    st.session_state.get('current_project', 'All'),
    org_df,
)

kpis = kpi_engine.calculate_kpis(data)
pm_kpis = kpi_engine.compute_pm_kpis(data)

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header(
    "Project Health & Schedule",
    "Milestone status, budget tracking, change requests, and decision register.",
)

# ── PM KPIs metrics row ───────────────────────────────────────────────────────
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

with kpi_c1:
    val = pm_kpis.get('milestone_achievement_pct')
    st.metric(
        "Milestone Achievement",
        f"{val:.1f}%" if val is not None else "N/A",
    )
with kpi_c2:
    val = pm_kpis.get('avg_schedule_variance_days')
    st.metric(
        "Avg Schedule Variance",
        f"{val:+.1f} d" if val is not None else "N/A",
        delta=None if val is None else val,
        delta_color="inverse",
    )
with kpi_c3:
    val = pm_kpis.get('action_closure_rate_pct')
    st.metric(
        "Action Closure Rate",
        f"{val:.1f}%" if val is not None else "N/A",
    )
with kpi_c4:
    val = pm_kpis.get('budget_variance_pct')
    st.metric(
        "Budget Variance",
        f"{val:+.1f}%" if val is not None else "N/A",
        delta=None if val is None else val,
        delta_color="inverse",
    )

st.divider()

# ── Org mapping lookup ────────────────────────────────────────────────────────
try:
    org_df_raw = pd.read_csv('data/resources/org_mapping.csv')
    proj_to_mgr = dict(zip(org_df_raw['PROJECT_ID'], org_df_raw['MANAGER_NAME']))
except Exception:
    proj_to_mgr = {}

# ── Milestones + Budget columns ───────────────────────────────────────────────
milestones = data.get('milestones', pd.DataFrame())
budget = data.get('budget', pd.DataFrame())
ecrs = data.get('ecrs', pd.DataFrame())
projects = data.get('projects', pd.DataFrame())

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Upcoming Milestones & Status")
    if len(milestones) > 0:
        ms_df = milestones.copy()
        ms_df['PROJECT_MANAGER'] = ms_df['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
        ms_df['PLANNED_DATE'] = pd.to_datetime(ms_df['PLANNED_DATE'], errors='coerce')
        ms_df = ms_df.sort_values(
            by=['PROJECT_MANAGER', 'PROJECT_ID', 'PLANNED_DATE'], na_position='last'
        )
        disp_cols = [
            c for c in
            ['PROJECT_MANAGER', 'PROJECT_ID', 'MILESTONE_NAME', 'PLANNED_DATE',
             'BASELINE_DATE', 'STATUS', 'OWNER']
            if c in ms_df.columns
        ]
        st.dataframe(ms_df[disp_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No milestone records available")

with col2:
    st.markdown("#### Interactive Budget Allocation")
    st.caption("Select a project to review and manage category budgets.")

    if len(budget) > 0 and not projects.empty:
        # Project selector (sorted by manager then project)
        proj_list = sorted(
            projects['PROJECT_ID'].unique().tolist(),
            key=lambda p: (proj_to_mgr.get(p, "Unknown"), p),
        )
        if 'budget_selected_proj' not in st.session_state:
            st.session_state['budget_selected_proj'] = proj_list[0] if proj_list else None

        selected_proj = st.selectbox(
            "Select Project:",
            options=proj_list,
            index=(
                proj_list.index(st.session_state['budget_selected_proj'])
                if st.session_state['budget_selected_proj'] in proj_list
                else 0
            ),
            key="budget_proj_select",
        )
        st.session_state['budget_selected_proj'] = selected_proj

        proj_budget = budget[budget['PROJECT_ID'] == selected_proj].copy()

        if len(proj_budget) > 0:
            is_manager = st.session_state.get('user_role') == 'Manager'

            st.markdown(f"**{selected_proj} Allocations**")

            # Column configuration
            col_config = {
                "BUDGET_ID": st.column_config.TextColumn(disabled=True),
                "PROJECT_ID": st.column_config.TextColumn(disabled=True),
                "BUDGET_PERIOD": st.column_config.TextColumn(disabled=not is_manager),
                "SPENT_AMOUNT": st.column_config.NumberColumn(
                    "SPENT_AMOUNT (Read-Only)", disabled=True, format="€%.0f"
                ),
                "COMMITTED_AMOUNT": st.column_config.NumberColumn(disabled=True, format="€%.0f"),
                "VARIANCE_AMOUNT": st.column_config.NumberColumn(disabled=True),
                "VARIANCE_PCT": st.column_config.TextColumn(disabled=True),
                "NOTES": st.column_config.TextColumn(disabled=not is_manager),
            }
            if is_manager:
                col_config["PLANNED_AMOUNT"] = st.column_config.NumberColumn(format="€%.0f")
                col_config["BUDGET_CATEGORY"] = st.column_config.TextColumn()
                col_config["STATUS"] = st.column_config.SelectboxColumn(
                    options=["ON_TRACK", "UNDERSPEND", "OVERSPEND", "AT_RISK"]
                )
            else:
                col_config["PLANNED_AMOUNT"] = st.column_config.NumberColumn(
                    disabled=True, format="€%.0f"
                )
                col_config["BUDGET_CATEGORY"] = st.column_config.TextColumn(disabled=True)
                col_config["STATUS"] = st.column_config.TextColumn(disabled=True)

            edited_budget = st.data_editor(
                proj_budget,
                use_container_width=True,
                hide_index=True,
                column_config=col_config,
                key=f"budget_editor_{selected_proj}",
                disabled=not is_manager,
            )

            # Save logic (Manager only)
            if is_manager:
                if st.button("Save Budget Allocations", use_container_width=True, type="primary"):
                    try:
                        # Re-calculate variances before saving
                        for idx, row in edited_budget.iterrows():
                            planned = float(row.get('PLANNED_AMOUNT', 0))
                            spent = float(row.get('SPENT_AMOUNT', 0))
                            var_amt = planned - spent
                            var_pct = f"{(var_amt / planned * 100):.1f}%" if planned > 0 else "0%"
                            edited_budget.at[idx, 'VARIANCE_AMOUNT'] = var_amt
                            edited_budget.at[idx, 'VARIANCE_PCT'] = var_pct

                        # Merge edits back into the full budget DataFrame
                        budget.update(edited_budget)

                        # Persist to CSV
                        budget_file_path = Path("data") / "projects" / "budget_tracking.csv"
                        budget.to_csv(budget_file_path, index=False)

                        # Audit log
                        _log_data_edit('Manager', str(budget_file_path))

                        st.cache_data.clear()
                        st.success("Allocations updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save allocations: {e}")
            else:
                st.info("Log in as Manager to edit Planned Amounts and Classifications.")
        else:
            st.warning(f"No budget items found for {selected_proj}")
    else:
        st.info("No budget data available")

# ── ECR / Change Request Analysis ─────────────────────────────────────────────
st.divider()
st.markdown("#### Change Request Analysis")

if len(ecrs) > 0:
    ecr_col1, ecr_col2 = st.columns([2, 1])
    with ecr_col1:
        ecrs_df = ecrs.copy()
        ecrs_df['PROJECT_MANAGER'] = ecrs_df['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
        ecrs_df = ecrs_df.sort_values(by=['PROJECT_MANAGER', 'PROJECT_ID'])
        disp_ecr_cols = [
            c for c in
            ['PROJECT_MANAGER', 'PROJECT_ID', 'ECR_ID', 'TITLE', 'STATUS',
             'CHANGE_TYPE', 'IMPACT_SCHEDULE_DAYS', 'IMPACT_COST']
            if c in ecrs_df.columns
        ]
        st.dataframe(ecrs_df[disp_ecr_cols], use_container_width=True, hide_index=True)
    with ecr_col2:
        ecr_status_counts = ecrs['STATUS'].value_counts()
        fig_ecr = px.pie(
            names=ecr_status_counts.index,
            values=ecr_status_counts.values,
            color_discrete_sequence=['#16a34a', '#1a6fdb', '#f59e0b', '#dc2626'],
            hole=0.4,
        )
        fig_ecr.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#475569', family='Inter, sans-serif'),
            height=250,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_ecr, use_container_width=True)
else:
    st.info("No change request data available.")

# ── Decision & Risk Register ──────────────────────────────────────────────────
st.divider()
st.markdown("#### Decision & Risk Register")

decisions_df = data.get('decisions', pd.DataFrame())
if not decisions_df.empty:
    decisions_df_copy = decisions_df.copy()
    decisions_df_copy['PROJECT_MANAGER'] = (
        decisions_df_copy['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
    )
    decisions_df_copy = decisions_df_copy.sort_values(by=['PROJECT_MANAGER', 'PROJECT_ID'])
    desired_cols = [
        'PROJECT_MANAGER', 'PROJECT_ID', 'DECISION_ID', 'TYPE', 'TITLE',
        'IMPACT', 'OWNER', 'DUE_DATE', 'APPROVAL_STATUS',
    ]
    disp_cols = [c for c in desired_cols if c in decisions_df_copy.columns]
    st.dataframe(decisions_df_copy[disp_cols], use_container_width=True, hide_index=True)
else:
    st.info("No decisions or assumptions logged yet.")
