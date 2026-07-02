"""
pages/05_resource_utilization.py
Team allocation, utilization rates, cost planning matrix, and capacity forecasting.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

import lib.sidebar as sidebar
import lib.data_loader as data_loader
import lib.kpi_engine as kpi_engine
from lib.styling import render_page_header, COLORS, STATUS_COLORS
from lib.sidebar import apply_scope_filter
from lib.data_loader import _derive_month_range, _MONTH_ORDER

# ── Module-level constant ───────────────────────────────────────────────────
_MONTH_ABBR = {m: m[:3] for m in _MONTH_ORDER}

# ── Bootstrap & load ────────────────────────────────────────────────────────
sidebar.bootstrap_sidebar()
data = data_loader.load_data()
if data is None:
    st.error("Could not load data.")
    st.stop()

# Scope filter
org_df = pd.DataFrame()
try:
    org_df = pd.read_csv('data/resources/org_mapping.csv')
except Exception:
    pass

selected_manager = st.session_state.get('current_manager', 'All')
selected_project = st.session_state.get('current_project', 'All')
data = apply_scope_filter(data, selected_manager, selected_project, org_df)

kpis = kpi_engine.calculate_kpis(data)

render_page_header(
    "Resource Utilization",
    "Team allocation, utilization rates, cost planning matrix, and capacity forecasting.",
)

# ── Build org lookup dicts ───────────────────────────────────────────────────
proj_to_mgr = {}
res_to_mgr  = {}
try:
    _org = pd.read_csv('data/resources/org_mapping.csv')
    proj_to_mgr = dict(zip(_org['PROJECT_ID'].dropna(), _org['MANAGER_NAME'].dropna()))
    res_to_mgr  = dict(zip(_org['TEAM_MEMBER'].dropna().str.lower(), _org['MANAGER_NAME'].dropna()))
except Exception:
    pass

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_cap, tab_rost, tab_sub = st.tabs(["Capacity & Load", "Team Roster", "Subcontractor Burn"])


# ═══════════════════════════════════════════════════════════════
# TEAM ROSTER TAB
# ═══════════════════════════════════════════════════════════════
with tab_rost:
    try:
        roster_df = pd.read_csv('data/resources/org_mapping.csv')

        if selected_manager != "All":
            roster_df = roster_df[roster_df['MANAGER_NAME'] == selected_manager]
        if selected_project != "All":
            roster_df = roster_df[roster_df['PROJECT_ID'] == selected_project]

        if roster_df.empty:
            st.info("No roster data available for the selected scope.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Headcount", len(roster_df))
            with col2:
                st.metric("Projects Covered", len(roster_df['PROJECT_ID'].unique()))

            st.markdown("### Organizational Mapping")
            roster_df = roster_df.sort_values(by=['MANAGER_NAME', 'TEAM_MEMBER'])
            st.dataframe(roster_df, width='stretch')
    except Exception as e:
        st.error(f"Could not load organization mapping: {e}")

# ═══════════════════════════════════════════════════════════════
# CAPACITY & LOAD TAB
# ═══════════════════════════════════════════════════════════════
with tab_cap:
    subtab_matrix, subtab_charts = st.tabs(["Resource-Cost Matrix", "Capacity Charts"])

    # ───────────────────────────────────────────────────────────
    # RESOURCE-COST MATRIX SUB-TAB
    # ───────────────────────────────────────────────────────────
    with subtab_matrix:
        st.markdown("#### Resource-Cost Planning Matrix")
        st.caption("Month-by-month utilization planning with live budget guard rails and cost forecasting.")

        try:
            full_util = data.get('monthly_utilization', pd.DataFrame()).copy()
            if full_util.empty:
                full_util = pd.read_csv('data/resources/monthly_utilization.csv')
            cost_rates_df   = pd.read_csv('data/resources/cost_rates.csv')
            resources_alloc = pd.read_csv('data/resources/resource_allocation.csv')
        except Exception as e:
            st.error(f"Error loading matrix files: {e}")
            full_util       = pd.DataFrame()
            cost_rates_df   = pd.DataFrame()
            resources_alloc = pd.DataFrame()

        if not full_util.empty:
            # ── Filters ──────────────────────────────────────────────
            col_p, col_r = st.columns(2)
            with col_p:
                matrix_projects = ["All"] + sorted(full_util['PROJECT_ID'].dropna().unique().tolist())
                selected_proj_matrix = st.selectbox("Filter by Project", options=matrix_projects, index=0, key="matrix_proj_filter")
            with col_r:
                matrix_resources = sorted(full_util['RESOURCE_ID'].dropna().unique().tolist())
                selected_res_matrix = st.multiselect("Filter by Resource", options=matrix_resources, default=[], key="matrix_res_filter")

            # ── Simulation Mode ───────────────────────────────────────
            sim_mode = st.toggle("Simulation Mode — edits are temporary until you apply", key="sim_mode_toggle")
            if sim_mode:
                st.info("Simulation Mode ON — Changes below are temporary. Use Apply to Live Data to commit, or Discard to revert.")

            # ── Build lookup dicts ────────────────────────────────────
            role_to_cost = dict(zip(cost_rates_df['ROLE'].str.lower(), cost_rates_df['COST_RATE_MONTHLY']))
            res_to_role  = dict(zip(resources_alloc['TEAM_MEMBER'].str.lower(), resources_alloc['ROLE']))

            # ── Short month labels ────────────────────────────────────
            month_abbr       = _MONTH_ABBR
            cols_chrono_full = _derive_month_range(full_util)
            cols_chrono      = [f"{m} {y}" for m, y in cols_chrono_full]
            cols_short       = [f"{month_abbr[m]} {str(y)[2:]}" for m, y in cols_chrono_full]
            long_to_short    = dict(zip(cols_chrono, cols_short))
            short_to_long    = dict(zip(cols_short, cols_chrono))

            # ── Apply local filters ───────────────────────────────────
            df_mat = full_util.copy()
            if selected_proj_matrix != "All":
                df_mat = df_mat[df_mat['PROJECT_ID'] == selected_proj_matrix]
            if selected_res_matrix:
                df_mat = df_mat[df_mat['RESOURCE_ID'].isin(selected_res_matrix)]

            # Enrich with role / cost
            roles, rates = [], []
            for _, r in df_mat.iterrows():
                res_name = str(r['RESOURCE_ID']).lower()
                role = res_to_role.get(res_name, "Normal Worker")
                rate = role_to_cost.get(role.lower(), 4000)
                roles.append(role)
                rates.append(rate)
            df_mat['ROLE']              = roles
            df_mat['COST_RATE_MONTHLY'] = rates
            df_mat['MONTH_YEAR']        = df_mat['MONTH'] + " " + df_mat['YEAR'].astype(str)

            # ── Pivot to wide format ──────────────────────────────────
            try:
                pivot_mat = df_mat.pivot_table(
                    index=['RESOURCE_ID', 'ROLE', 'PROJECT_ID', 'COST_RATE_MONTHLY'],
                    columns='MONTH_YEAR',
                    values='UTILIZATION_PCT',
                    aggfunc='first'
                ).reset_index()
                for c in cols_chrono:
                    if c not in pivot_mat.columns:
                        pivot_mat[c] = 0.0
                pivot_mat = pivot_mat[['RESOURCE_ID', 'ROLE', 'PROJECT_ID', 'COST_RATE_MONTHLY'] + cols_chrono]
                pivot_mat.rename(columns=long_to_short, inplace=True)

                total_costs = []
                for _, row in pivot_mat.iterrows():
                    rate = row['COST_RATE_MONTHLY']
                    total_costs.append(sum(float(row[s]) for s in cols_short) * rate)
                pivot_mat['PROJECTED_COST'] = total_costs

                pivot_mat['MANAGER'] = pivot_mat['RESOURCE_ID'].str.lower().map(res_to_mgr).fillna("Unknown")
                display_cols  = ['MANAGER', 'RESOURCE_ID', 'ROLE', 'PROJECT_ID', 'COST_RATE_MONTHLY', 'PROJECTED_COST'] + cols_short
                pivot_mat     = pivot_mat[display_cols].sort_values(by=['MANAGER', 'RESOURCE_ID'])

                def _util_status(row):
                    vals = [float(row[s]) for s in cols_short]
                    peak = max(vals) if vals else 0.0
                    if peak > 1.0:   return "Over"
                    if peak >= 0.96: return "Full"
                    if peak >= 0.31: return "OK"
                    return "Under"

                pivot_mat.insert(4, 'STATUS', pivot_mat.apply(_util_status, axis=1))

                col_configs = {
                    "MANAGER":           st.column_config.TextColumn("Manager",     width="medium"),
                    "RESOURCE_ID":       st.column_config.TextColumn("Resource",    width="medium"),
                    "ROLE":              st.column_config.TextColumn("Role",        width="medium"),
                    "PROJECT_ID":        st.column_config.TextColumn("Project",     width="small"),
                    "STATUS":            st.column_config.TextColumn("Status",      width="small"),
                    "COST_RATE_MONTHLY": st.column_config.NumberColumn("Rate/Mo",   format="€%.0f", width="small"),
                    "PROJECTED_COST":    st.column_config.NumberColumn("Proj. Cost", format="€%.0f", width="medium"),
                }
                for s in cols_short:
                    col_configs[s] = st.column_config.NumberColumn(s, format="%.2f", min_value=0.0, max_value=2.0, width="small")

                frozen_cols   = ['MANAGER', 'RESOURCE_ID', 'ROLE', 'PROJECT_ID', 'STATUS']
                pivot_display = pivot_mat.copy()

            except Exception as e:
                st.warning(f"No matrix records matched the filters: {e}")
                pivot_mat     = pd.DataFrame()
                pivot_display = pd.DataFrame()

            # ── Budget Guard Rail helper ──────────────────────────────
            def _compute_budget_panel(pivot_df, proj_id, labor_budget):
                monthly_spend = []
                proj_rows = pivot_df[pivot_df['PROJECT_ID'] == proj_id] if not pivot_df.empty else pd.DataFrame()
                for s in cols_short:
                    month_total = 0.0
                    for _, row in proj_rows.iterrows():
                        month_total += float(row[s]) * float(row['COST_RATE_MONTHLY'])
                    monthly_spend.append(month_total)
                cumulative = []
                running = 0.0
                for ms in monthly_spend:
                    running += ms
                    cumulative.append(running)
                total_proj  = running
                remaining   = labor_budget - total_proj
                avg_monthly = total_proj / len(cols_short) if cols_short else 0
                exhaust_idx = -1
                for idx, cv in enumerate(cumulative):
                    if cv >= labor_budget:
                        exhaust_idx = idx
                        break
                return monthly_spend, cumulative, total_proj, remaining, avg_monthly, exhaust_idx

            # ── Budget Guard Rail display ─────────────────────────────
            if selected_proj_matrix != "All":
                is_budget_allowed = True
                if st.session_state.get('user_role') == 'Project Manager' and st.session_state.get('current_pm'):
                    try:
                        _org_sec = pd.read_csv('data/resources/org_mapping.csv')
                        pm_projs = _org_sec[_org_sec['MANAGER_NAME'] == st.session_state['current_pm']]['PROJECT_ID'].dropna().unique().tolist()
                        if selected_proj_matrix not in pm_projs:
                            is_budget_allowed = False
                    except Exception:
                        is_budget_allowed = False

                if is_budget_allowed:
                    try:
                        budget_df      = pd.read_csv('data/projects/budget_tracking.csv')
                        proj_budget_df = budget_df[budget_df['PROJECT_ID'] == selected_proj_matrix]
                        labor_row      = proj_budget_df[proj_budget_df['BUDGET_CATEGORY'].str.contains('Labor|Engineering', case=False, na=False)]
                        if not labor_row.empty:
                            labor_budget = float(labor_row.iloc[0]['PLANNED_AMOUNT'])
                        else:
                            non_total    = proj_budget_df[~proj_budget_df['BUDGET_CATEGORY'].str.contains('TOTAL', case=False, na=False)]
                            labor_budget = float(non_total['PLANNED_AMOUNT'].sum()) if not non_total.empty else 0.0
                    except Exception:
                        labor_budget = 0.0

                    if labor_budget > 0.0 and not pivot_mat.empty:
                        _ms, _cum, _total, _rem, _avg, _ei = _compute_budget_panel(pivot_mat, selected_proj_matrix, labor_budget)
                        used_pct = (_total / labor_budget * 100) if labor_budget else 0

                        if _cum and _cum[0] >= labor_budget:
                            _guard_cls    = "red"
                            _guard_status = "OVER BUDGET"
                            _guard_msg    = "Already over budget at current allocations."
                        elif _ei != -1:
                            _guard_cls    = "amber"
                            _guard_status = "AT RISK"
                            months_left   = _ei
                            _guard_msg    = f"Budget exhausted by {cols_chrono[_ei]} — {months_left} month{'s' if months_left != 1 else ''} from now."
                        else:
                            _guard_cls    = "green"
                            _guard_status = "ON TRACK"
                            _guard_msg    = f"Budget sufficient through {cols_chrono[-1]}."

                        _rem_cls = "green" if _rem >= 0 else "red"
                        st.markdown(f"""
<div class="guard-rail {_guard_cls}">
  <div class="guard-rail-header">
    <span class="guard-rail-title">Budget Guard Rail — {selected_proj_matrix}</span>
    <span class="guard-rail-badge {_guard_cls}">{_guard_status}</span>
  </div>
  <div class="guard-rail-grid">
    <div>
      <div class="guard-rail-stat-label">Labor Budget</div>
      <div class="guard-rail-stat-value">€{labor_budget:,.0f}</div>
    </div>
    <div>
      <div class="guard-rail-stat-label">Projected Spend</div>
      <div class="guard-rail-stat-value">€{_total:,.0f} <span class="guard-rail-stat-label">({used_pct:.0f}%)</span></div>
    </div>
    <div>
      <div class="guard-rail-stat-label">Remaining</div>
      <div class="guard-rail-stat-value {_rem_cls}">€{_rem:,.0f}</div>
    </div>
    <div>
      <div class="guard-rail-stat-label">Avg Burn Rate</div>
      <div class="guard-rail-stat-value">€{_avg:,.0f}<span class="guard-rail-stat-label">/mo</span></div>
    </div>
  </div>
  <div class="guard-rail-msg">{_guard_msg}</div>
</div>
""", unsafe_allow_html=True)
                    elif labor_budget <= 0.0:
                        st.warning("No labor budget configured for this project in budget_tracking.csv.")
                else:
                    st.info("Budget visibility restricted — resource cost rates are visible for cross-team negotiation, but budget envelopes for other PMs' projects are hidden.")

            st.divider()

            # ── Matrix Data Editor ────────────────────────────────────
            st.markdown("#### Consolidated Matrix — Edit in Place")
            st.caption("Enter utilization as decimal: 0.8 = 80%, 1.0 = 100%. Status column updates after applying changes.")

            if not pivot_display.empty:
                edited_pivot = st.data_editor(
                    pivot_display,
                    width='stretch',
                    hide_index=True,
                    column_config=col_configs,
                    disabled=frozen_cols,
                    key="pivot_editor"
                )

                # Re-compute budget guard rail from editor output
                if selected_proj_matrix != "All":
                    try:
                        if 'labor_budget' in dir() and labor_budget > 0.0 and 'is_budget_allowed' in dir() and is_budget_allowed:
                            _ms2, _cum2, _total2, _rem2, _avg2, _ei2 = _compute_budget_panel(edited_pivot, selected_proj_matrix, labor_budget)
                            if _total2 != _total:
                                used2 = (_total2 / labor_budget * 100)
                                _delta_str = f"€{_total2 - _total:+,.0f} vs baseline"
                                if _ei2 != -1:
                                    st.warning(f"Live Update: Projected spend now €{_total2:,.0f} ({used2:.0f}%) — exhaustion at {cols_chrono[_ei2]} — {_delta_str}")
                                elif _cum2 and _cum2[0] >= labor_budget:
                                    st.error(f"Live Update: Already over budget — €{_total2:,.0f} — {_delta_str}")
                                else:
                                    st.success(f"Live Update: Projected spend €{_total2:,.0f} — budget healthy — {_delta_str}")
                    except Exception:
                        pass

                m_col1, m_col2, m_col3 = st.columns(3)
                sim_label  = "Apply to Live Data" if sim_mode else "Save Matrix Changes"
                disc_label = "Discard Simulation" if sim_mode else None

                with m_col1:
                    if st.button(sim_label, type="primary", width='stretch', key="save_matrix_btn"):
                        try:
                            disk_util     = pd.read_csv('data/resources/monthly_utilization.csv')
                            melt_cols     = [c for c in edited_pivot.columns if c in cols_short]
                            melted        = edited_pivot.melt(id_vars=['RESOURCE_ID', 'PROJECT_ID'], value_vars=melt_cols,
                                                              var_name='MONTH_SHORT', value_name='UTILIZATION_PCT')
                            melted['MONTH'] = melted['MONTH_SHORT'].map({v: k.split()[0] for k, v in long_to_short.items()})
                            melted['YEAR']  = melted['MONTH_SHORT'].map({v: int(k.split()[1]) for k, v in long_to_short.items()})
                            melted          = melted.drop(columns=['MONTH_SHORT'])
                            melted.set_index(['RESOURCE_ID', 'PROJECT_ID', 'MONTH', 'YEAR'], inplace=True)
                            disk_util.set_index(['RESOURCE_ID', 'PROJECT_ID', 'MONTH', 'YEAR'], inplace=True)
                            disk_util.update(melted)
                            disk_util.reset_index(inplace=True)
                            disk_util.to_csv('data/resources/monthly_utilization.csv', index=False)

                            try:
                                old_cost = sum(float(r['COST_RATE_MONTHLY']) * sum(float(r[s]) for s in cols_short)
                                               for _, r in pivot_display.iterrows()) if not pivot_display.empty else 0
                                new_cost = sum(float(r['COST_RATE_MONTHLY']) * sum(float(r[s]) for s in cols_short)
                                               for _, r in edited_pivot.iterrows()) if not edited_pivot.empty else 0
                                cost_delta = round(new_cost - old_cost)
                                df_audit   = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                                new_entry  = pd.DataFrame([{
                                    'TIMESTAMP':            datetime.now().isoformat(),
                                    'SOURCE_RESOURCE':      st.session_state.get('user_role', 'Manager'),
                                    'TARGET_BOTTLENECK':    selected_proj_matrix if selected_proj_matrix != "All" else "All Projects",
                                    'HOURS_TRANSFERRED':    0,
                                    'ESTIMATED_COST_DELTA': cost_delta,
                                    'NEW_SOURCE_UTIL':      'N/A',
                                    'NEW_TARGET_UTIL':      'N/A',
                                    'DECISION':             'MANUAL_OVERRIDE',
                                    'RATIONALE':            f'PM manually updated utilization matrix. Cost delta: €{cost_delta:+,}'
                                }])
                                pd.concat([df_audit, new_entry], ignore_index=True).to_csv('data/resources/rebalancing_audit_log.csv', index=False)
                            except Exception:
                                pass

                            st.cache_data.clear()
                            if sim_mode:
                                st.success("Simulation applied to live data and logged to Governance Audit Trail.")
                            else:
                                st.success("Matrix saved successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving matrix: {e}")

                if sim_mode and disc_label:
                    with m_col2:
                        if st.button(disc_label, width='stretch', key="discard_sim_btn"):
                            st.cache_data.clear()
                            st.rerun()

                with m_col3:
                    try:
                        import io
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            pivot_display.copy().to_excel(writer, index=False, sheet_name='Planning_Matrix')
                        st.download_button(
                            label="Export to Excel",
                            data=buffer.getvalue(),
                            file_name="planning_matrix_export.xlsx",
                            mime="application/vnd.ms-excel",
                            width='stretch'
                        )
                    except Exception:
                        pass

    # ───────────────────────────────────────────────────────────
    # CAPACITY CHARTS SUB-TAB
    # ───────────────────────────────────────────────────────────
    with subtab_charts:
        resources = data.get('resources', pd.DataFrame())

        if len(resources) > 0:
            st.markdown("#### Capacity & Demand Forecasting")
            fc1, fc2, fc3 = st.columns(3)

            with fc1:
                util_df = data.get('monthly_utilization', pd.DataFrame())
                cols_chrono_cap = _derive_month_range(util_df)
                cols_chrono     = [f"{m} {y}" for m, y in cols_chrono_cap]

                if not util_df.empty:
                    distinct_resources = util_df['RESOURCE_ID'].dropna().unique()
                    headcount          = float(len(distinct_resources))
                    demand_list        = []
                    capacity_list      = []
                    for col_month in cols_chrono:
                        m, y = col_month.split(" ")
                        y    = int(y)
                        m_rows  = util_df[(util_df['MONTH'] == m) & (util_df['YEAR'] == y)]
                        m_demand = m_rows['UTILIZATION_PCT'].sum()
                        demand_list.append(m_demand)
                        capacity_list.append(headcount)

                    fig_cap = go.Figure()
                    fig_cap.add_trace(go.Scatter(
                        x=cols_chrono, y=capacity_list, mode='lines',
                        name='Total Available Capacity',
                        line=dict(color=COLORS["green"], width=2, dash='dash')
                    ))
                    fig_cap.add_trace(go.Scatter(
                        x=cols_chrono, y=demand_list, mode='lines+markers',
                        name='Projected Demand',
                        line=dict(color=COLORS["blue"], width=2)
                    ))
                    overallocation_y = [max(c, d) for c, d in zip(capacity_list, demand_list)]
                    fig_cap.add_trace(go.Scatter(
                        x=cols_chrono, y=capacity_list, mode='lines',
                        line=dict(color='rgba(0,0,0,0)', width=0),
                        showlegend=False, hoverinfo='skip'
                    ))
                    fig_cap.add_trace(go.Scatter(
                        x=cols_chrono, y=overallocation_y, mode='lines',
                        fill='tonexty', fillcolor='rgba(239, 68, 68, 0.25)',
                        line=dict(color='rgba(0,0,0,0)', width=0),
                        name='Overallocation Zone', hoverinfo='skip'
                    ))
                    fig_cap.update_layout(
                        xaxis_title="Timeline", yaxis_title="FTE Units",
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=300, margin=dict(t=8, b=8, l=0, r=0),
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.25, x=0, font=dict(size=11)),
                        font=dict(family='Inter, sans-serif', color=COLORS["text_secondary"]),
                    )
                    fig_cap.update_yaxes(title_text="FTE Units", tickformat=".1f")
                    st.plotly_chart(fig_cap, width='stretch')
                else:
                    st.info("No resource utilization data available for the selected scope.")

            with fc2:
                if not resources.empty:
                    proj_alloc = resources.groupby('PROJECT_ID')['ALLOCATED_HOURS_WEEKLY'].sum().reset_index()
                    proj_alloc['MANAGER'] = proj_alloc['PROJECT_ID'].map(proj_to_mgr).fillna("Unknown")
                    proj_alloc = proj_alloc.sort_values(by=['MANAGER', 'PROJECT_ID'])
                    fig = px.pie(proj_alloc, values='ALLOCATED_HOURS_WEEKLY', names='PROJECT_ID', hole=0.5,
                                 title="Allocation by Project (Current Month)")
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig, width='stretch')

            with fc3:
                milestones = data.get('milestones', pd.DataFrame())
                if not milestones.empty:
                    milestones['PLANNED_DATE'] = pd.to_datetime(milestones['PLANNED_DATE'], errors='coerce')
                    future_ms = milestones[milestones['PLANNED_DATE'] > datetime.now()].copy()
                    future_ms['WEEK'] = future_ms['PLANNED_DATE'].dt.to_period('W').dt.start_time
                    demand = future_ms.groupby('WEEK').size().reset_index(name='EXPECTED_DEMAND_FTE')
                    try:
                        from integrations.config_helper import load_config as _lcfg
                        _fte_mult = float(_lcfg().get('resources', {}).get('fte_per_milestone', 5))
                    except Exception:
                        _fte_mult = 5.0
                    demand['EXPECTED_DEMAND_FTE'] = demand['EXPECTED_DEMAND_FTE'] * _fte_mult
                    if not demand.empty:
                        fig = px.area(demand.head(8), x='WEEK', y='EXPECTED_DEMAND_FTE',
                                      title="Demand Forecast (Upcoming Milestones)",
                                      color_discrete_sequence=['#8b5cf6'])
                        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, width='stretch')
                    else:
                        st.info("No upcoming milestones for demand forecasting")
                else:
                    st.info("No milestone data available")

            st.divider()

            with st.expander("Import Resource Data"):
                uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"], key="resource_importer")
                if uploaded_file is not None:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            imported_df = pd.read_csv(uploaded_file)
                        else:
                            imported_df = pd.read_excel(uploaded_file)
                        if 'TEAM_MEMBER' in imported_df.columns:
                            imported_df.to_csv('data/resources/resource_allocation.csv', index=False)
                            st.success("Resources imported. Click Refresh Data in the sidebar.")
                        else:
                            st.error("Invalid format: Missing TEAM_MEMBER column")
                    except Exception as e:
                        st.error(f"Error importing file: {e}")

            st.divider()

            # ── Budget Burn Trend ─────────────────────────────────────
            st.markdown("#### Budget Burn Trend")
            try:
                _burn_proj_options = ["All"] + sorted(data.get('monthly_utilization', pd.DataFrame())['PROJECT_ID'].dropna().unique().tolist())
                _burn_proj    = st.selectbox("Select Project for Burn Trend", _burn_proj_options, key="burn_trend_proj")
                _cost_rates_bt = pd.read_csv('data/resources/cost_rates.csv')
                _util_bt       = data.get('monthly_utilization', pd.DataFrame()).copy()
                _res_bt        = pd.read_csv('data/resources/resource_allocation.csv')
                _role_cost_bt  = dict(zip(_cost_rates_bt['ROLE'].str.lower(), _cost_rates_bt['COST_RATE_MONTHLY']))
                _res_role_bt   = dict(zip(_res_bt['TEAM_MEMBER'].str.lower(), _res_bt['ROLE']))
                _bt_cols       = _derive_month_range(_util_bt if not _util_bt.empty else data.get('monthly_utilization', pd.DataFrame()))
                _bt_labels     = [f"{m[:3]} {str(y)[2:]}" for m, y in _bt_cols]

                if _burn_proj != "All":
                    _util_bt = _util_bt[_util_bt['PROJECT_ID'] == _burn_proj]

                _monthly_spend_bt = []
                for m, y in _bt_cols:
                    _rows = _util_bt[(_util_bt['MONTH'] == m) & (_util_bt['YEAR'] == y)]
                    _ms   = 0.0
                    for _, _r in _rows.iterrows():
                        _role = _res_role_bt.get(str(_r['RESOURCE_ID']).lower(), 'Normal Worker')
                        _rate = _role_cost_bt.get(_role.lower(), 4000)
                        _ms  += float(_r['UTILIZATION_PCT']) * _rate
                    _monthly_spend_bt.append(_ms)

                _cum_bt = []
                _run    = 0.0
                for _ms in _monthly_spend_bt:
                    _run += _ms
                    _cum_bt.append(_run)

                _labor_bt = 0.0
                if _burn_proj != "All":
                    try:
                        _bdf  = pd.read_csv('data/projects/budget_tracking.csv')
                        _bdf  = _bdf[_bdf['PROJECT_ID'] == _burn_proj]
                        _lrow = _bdf[_bdf['BUDGET_CATEGORY'].str.contains('Labor|Engineering', case=False, na=False)]
                        if not _lrow.empty:
                            _labor_bt = float(_lrow.iloc[0]['PLANNED_AMOUNT'])
                        else:
                            _nt = _bdf[~_bdf['BUDGET_CATEGORY'].str.contains('TOTAL', case=False, na=False)]
                            _labor_bt = float(_nt['PLANNED_AMOUNT'].sum()) if not _nt.empty else 0.0
                    except Exception:
                        pass

                _fig_bt = go.Figure()
                _fig_bt.add_trace(go.Bar(x=_bt_labels, y=_monthly_spend_bt, name='Monthly Spend',
                                         marker_color='rgba(26,111,219,0.5)', yaxis='y'))
                _fig_bt.add_trace(go.Scatter(x=_bt_labels, y=_cum_bt, name='Cumulative Spend',
                                             mode='lines+markers', line=dict(color='#1a6fdb', width=3), yaxis='y'))
                if _labor_bt > 0:
                    _fig_bt.add_trace(go.Scatter(x=_bt_labels, y=[_labor_bt]*len(_bt_labels), name='Budget Limit',
                                                 mode='lines', line=dict(color='#ef4444', width=2, dash='dash'), yaxis='y'))
                _fig_bt.update_layout(
                    title=f"Budget Burn Trend — {_burn_proj}",
                    xaxis_title="Month", yaxis_title="Cost (€)",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#f8fafc', height=320,
                    margin=dict(t=40, b=20, l=20, r=20),
                    legend=dict(orientation='h', y=1.1, x=0),
                    font=dict(color='#475569', family='Inter, sans-serif')
                )
                st.plotly_chart(_fig_bt, width='stretch')
            except Exception as _e:
                st.info(f"Budget Burn Trend unavailable: {_e}")

            # ── Weekly Hours (expander) ───────────────────────────────
            with st.expander("Allocated vs Utilized Hours — Weekly Detail"):
                resources_disp = resources.copy()
                resources_disp['ALLOCATED_HOURS_WEEKLY'] = pd.to_numeric(resources_disp['ALLOCATED_HOURS_WEEKLY'], errors='coerce')
                resources_disp['UTILIZED_HOURS_WEEKLY']  = pd.to_numeric(resources_disp['UTILIZED_HOURS_WEEKLY'],  errors='coerce')
                resources_disp['MANAGER'] = resources_disp['TEAM_MEMBER'].str.lower().map(res_to_mgr).fillna("Unknown")
                resources_disp = resources_disp.sort_values(by=['MANAGER', 'TEAM_MEMBER'])
                fig_wh = px.bar(
                    resources_disp, x='TEAM_MEMBER',
                    y=['ALLOCATED_HOURS_WEEKLY', 'UTILIZED_HOURS_WEEKLY'],
                    barmode='group',
                    color_discrete_sequence=[COLORS["blue"], COLORS["amber"]],
                )
                fig_wh.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=COLORS["text_secondary"], family='Inter, sans-serif'),
                    margin=dict(t=8, b=8, l=0, r=0),
                )
                st.plotly_chart(fig_wh, width='stretch')

            st.divider()

            # ── AI Resource Rebalancing ───────────────────────────────
            if st.toggle("Enable AI Resource Rebalancing Recommendations", key="ai_rebalance_toggle"):
                st.markdown("#### AI Rebalancing Insights")
                with st.spinner("Analyzing skill matrices and utilization loads..."):
                    cost_df      = data.get('cost_rates', pd.DataFrame())
                    resources_df = resources.copy()
                    if not cost_df.empty and 'ROLE' in cost_df.columns:
                        resources_df = resources_df.merge(cost_df, on='ROLE', how='left')
                    else:
                        resources_df['COST_RATE_MONTHLY'] = 0

                    util_df_ai = data.get('monthly_utilization', pd.DataFrame())
                    if not util_df_ai.empty:
                        monthly_sums = util_df_ai.groupby(['RESOURCE_ID', 'MONTH', 'YEAR'])['UTILIZATION_PCT'].sum().reset_index()
                        avg_util     = monthly_sums.groupby('RESOURCE_ID')['UTILIZATION_PCT'].mean().reset_index()
                        resources_df = resources_df.merge(avg_util, left_on='TEAM_MEMBER', right_on='RESOURCE_ID', how='left')
                        resources_df['UTIL_NUM'] = (resources_df['UTILIZATION_PCT_y'] * 100).fillna(
                            pd.to_numeric(resources_df['UTILIZATION_PCT_x'].str.rstrip('%'), errors='coerce')
                        ).fillna(100.0)
                    else:
                        resources_df['UTIL_NUM'] = pd.to_numeric(resources_df['UTILIZATION_PCT'].str.rstrip('%'), errors='coerce').fillna(100.0)

                    underutilized = resources_df[(resources_df['UTIL_NUM'] < 80.0) | (resources_df['ALLOCATION_STATUS'].isin(['COMPLETED', 'AVAILABLE']))].copy()
                    underutilized['MANAGER'] = underutilized['TEAM_MEMBER'].str.lower().map(res_to_mgr).fillna("Unknown")
                    underutilized = underutilized.sort_values(by=['MANAGER', 'TEAM_MEMBER'])

                    overallocated = resources_df[(resources_df['UTIL_NUM'] > 100.0) | (resources_df['ALLOCATION_STATUS'] == 'OVERALLOCATED')].copy()
                    overallocated['MANAGER'] = overallocated['TEAM_MEMBER'].str.lower().map(res_to_mgr).fillna("Unknown")
                    overallocated = overallocated.sort_values(by=['MANAGER', 'TEAM_MEMBER'])

                    if overallocated.empty:
                        st.success("No overallocated resources or bottlenecks detected! The team is perfectly balanced.")
                    elif underutilized.empty:
                        st.warning("Bottlenecks detected, but no underutilized resources are available to help. You may need to hire or defer work.")
                        st.dataframe(overallocated[['MANAGER', 'TEAM_MEMBER', 'ROLE', 'SKILL', 'UTIL_NUM', 'PROJECT_ID']], width='stretch', hide_index=True)
                    else:
                        import json
                        import re
                        from integrations.openai_client import get_completion

                        if "ai_rebalance_recs" not in st.session_state:
                            cols_under = ['TEAM_MEMBER', 'ROLE', 'SKILL', 'UTIL_NUM', 'COST_RATE_MONTHLY']
                            cols_over  = ['TEAM_MEMBER', 'ROLE', 'SKILL', 'UTIL_NUM', 'PROJECT_ID', 'COST_RATE_MONTHLY']
                            under_str  = underutilized[[c for c in cols_under if c in underutilized.columns]].to_dict(orient='records')
                            over_str   = overallocated[[c for c in cols_over  if c in overallocated.columns]].to_dict(orient='records')

                            prompt = f"""You are an expert Resource Manager. Analyze the following over-allocated bottlenecks and underutilized available personnel. 
Match available personnel to bottlenecks based on matching or complementary 'SKILL' and 'ROLE'. 
Underutilized (Available bandwidth): {json.dumps(under_str)}
Overallocated (Needs help): {json.dumps(over_str)}

Provide 1-3 highly specific recommendations. Balance both utilization and cost. Make cost the tiebreaker when utilization impact is roughly equal. 
Return ONLY a valid JSON array of objects with the keys:
"source_resource", "target_bottleneck", "rationale", "suggested_action",
"hours_transferred", "new_source_utilization", "new_target_utilization",
"estimated_cost_delta", "source_impact", "target_impact\""""
                            response = get_completion(prompt, max_tokens=1500)
                            st.session_state["ai_rebalance_recs"] = response

                        response = st.session_state["ai_rebalance_recs"]
                        try:
                            match = re.search(r'\[.*\]', response, re.DOTALL)
                            if match:
                                recs = json.loads(match.group(0))
                                for i, rec in enumerate(recs):
                                    with st.container():
                                        st.markdown(f"**Action:** {rec.get('suggested_action', '')}")
                                        st.markdown(f"**From:** `{rec.get('source_resource', '')}` — **To:** `{rec.get('target_bottleneck', '')}`")
                                        st.caption(f"Rationale: {rec.get('rationale', '')}")
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric(f"Impact on {rec.get('source_resource', '')}",
                                                      rec.get('new_source_utilization', ''),
                                                      delta=f"+{rec.get('hours_transferred', 0)}% alloc")
                                            st.caption(rec.get('source_impact', ''))
                                        with col2:
                                            st.metric(f"Impact on {rec.get('target_bottleneck', '')}",
                                                      rec.get('new_target_utilization', ''),
                                                      delta=f"-{rec.get('hours_transferred', 0)}% alloc", delta_color="inverse")
                                            st.caption(rec.get('target_impact', ''))
                                        with col3:
                                            cost_delta = rec.get('estimated_cost_delta', 0)
                                            st.metric("Estimated Cost Impact", f"€{cost_delta}", delta=f"€{cost_delta}", delta_color="inverse")

                                        btn_col1, btn_col2 = st.columns([1, 1])
                                        with btn_col1:
                                            if st.button("Accept", key=f"accept_{i}", type="primary"):
                                                df_audit  = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                                                new_audit = pd.DataFrame([{
                                                    'TIMESTAMP':            datetime.now().isoformat(),
                                                    'SOURCE_RESOURCE':      rec.get('source_resource', ''),
                                                    'TARGET_BOTTLENECK':    rec.get('target_bottleneck', ''),
                                                    'HOURS_TRANSFERRED':    rec.get('hours_transferred', 0),
                                                    'ESTIMATED_COST_DELTA': rec.get('estimated_cost_delta', 0),
                                                    'NEW_SOURCE_UTIL':      rec.get('new_source_utilization', ''),
                                                    'NEW_TARGET_UTIL':      rec.get('new_target_utilization', ''),
                                                    'DECISION':             'ACCEPTED',
                                                    'RATIONALE':            'Accepted AI Recommendation'
                                                }])
                                                pd.concat([df_audit, new_audit], ignore_index=True).to_csv('data/resources/rebalancing_audit_log.csv', index=False)
                                                st.success("Decision logged to Governance Audit Trail.")
                                                try:
                                                    from lib.notifications import notify
                                                    payload = {"Source": rec.get('source_resource', ''), "Target": rec.get('target_bottleneck', ''), "Hours": rec.get('hours_transferred', 0)}
                                                    src = rec.get('source_resource', '')
                                                    tgt = rec.get('target_bottleneck', '')
                                                    if src: notify(src, 'REBALANCE_ACCEPTED', payload, channel='Both')
                                                    if tgt: notify(tgt, 'REBALANCE_ACCEPTED', payload, channel='Both')
                                                except Exception:
                                                    pass
                                        with btn_col2:
                                            if st.button("Reject", key=f"reject_{i}"):
                                                df_audit  = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                                                new_audit = pd.DataFrame([{
                                                    'TIMESTAMP':         datetime.now().isoformat(),
                                                    'SOURCE_RESOURCE':   rec.get('source_resource', ''),
                                                    'TARGET_BOTTLENECK': rec.get('target_bottleneck', ''),
                                                    'HOURS_TRANSFERRED': rec.get('hours_transferred', 0),
                                                    'NEW_SOURCE_UTIL':   rec.get('new_source_utilization', ''),
                                                    'NEW_TARGET_UTIL':   rec.get('new_target_utilization', ''),
                                                    'DECISION':          'REJECTED',
                                                    'RATIONALE':         'PM Overrode AI Recommendation'
                                                }])
                                                pd.concat([df_audit, new_audit], ignore_index=True).to_csv('data/resources/rebalancing_audit_log.csv', index=False)
                                                st.info("Decision logged to Governance Audit Trail.")
                            else:
                                st.error("AI returned unparseable recommendations.")
                        except Exception as e:
                            st.error(f"Failed to parse AI rebalancing data: {e}")

            st.divider()

            # ── Governance Audit Trail ────────────────────────────────
            st.markdown("#### Governance Audit Trail — Last 5 Decisions")
            try:
                audit_df = pd.read_csv('data/resources/rebalancing_audit_log.csv')
                if not audit_df.empty:
                    st.dataframe(audit_df.tail(5), width='stretch', hide_index=True)
                else:
                    st.info("No rebalancing decisions have been logged yet.")
            except Exception:
                st.info("No rebalancing decisions have been logged yet.")

            st.dataframe(
                resources[['TEAM_MEMBER', 'ROLE', 'SKILL', 'ALLOCATION_STATUS', 'UTILIZATION_PCT', 'PROJECT_ID']],
                width='stretch',
                hide_index=True
            )
        else:
            st.info("No resource allocation data found")

# ═══════════════════════════════════════════════════════════════
# SUBCONTRACTOR BURN TAB
# ═══════════════════════════════════════════════════════════════
with tab_sub:
    st.markdown("### Subcontractor Burn Rate Tracking")
    sub_df = data.get('subcontractors', pd.DataFrame())
    if not sub_df.empty:
        sub_df_display = sub_df.copy()
        
        projected_burn = []
        for idx, row in sub_df_display.iterrows():
            if str(row['CONTRACT_TYPE']).lower() == 'fixed':
                projected_burn.append(row['MONTHLY_CAP'])
            else:
                hours = 160
                calc_burn = row['HOURLY_RATE'] * hours
                projected_burn.append(min(calc_burn, row['MONTHLY_CAP']))
                
        sub_df_display['PROJECTED_MONTHLY_BURN'] = projected_burn
        
        tot_sub_budget = sub_df_display['MONTHLY_CAP'].sum()
        tot_projected_burn = sub_df_display['PROJECTED_MONTHLY_BURN'].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Subcontractor Monthly Cap", f"${tot_sub_budget:,.2f}")
        with col_m2:
            st.metric("Projected Monthly Burn", f"${tot_projected_burn:,.2f}")
        with col_m3:
            burn_ratio = (tot_projected_burn / tot_sub_budget) * 100 if tot_sub_budget > 0 else 0
            st.metric("Burn Ratio vs Cap", f"{burn_ratio:.1f}%")
            
        warning_subcontractors = sub_df_display[sub_df_display['PROJECTED_MONTHLY_BURN'] >= (sub_df_display['MONTHLY_CAP'] * 0.9)]
        if not warning_subcontractors.empty:
            for _, row in warning_subcontractors.iterrows():
                st.warning(f"⚠️ **Cap Alert**: Subcontractor *{row['NAME']}* ({row['COMPANY']}) on Project **{row['PROJECT_ID']}** has projected monthly burn (${row['PROJECTED_MONTHLY_BURN']:,.2f}) close to or exceeding monthly cap (${row['MONTHLY_CAP']:,.2f})!")

        st.dataframe(
            sub_df_display,
            column_config={
                "SUBCONTRACTOR_ID": st.column_config.TextColumn("ID"),
                "NAME": st.column_config.TextColumn("Name"),
                "COMPANY": st.column_config.TextColumn("Company"),
                "PROJECT_ID": st.column_config.TextColumn("Project ID"),
                "HOURLY_RATE": st.column_config.NumberColumn("Hourly Rate ($)", format="$%.2f"),
                "MONTHLY_CAP": st.column_config.NumberColumn("Monthly Cap ($)", format="$%,.2f"),
                "CURRENCY": st.column_config.TextColumn("Currency"),
                "CONTRACT_TYPE": st.column_config.TextColumn("Contract Type"),
                "START_DATE": st.column_config.TextColumn("Start Date"),
                "END_DATE": st.column_config.TextColumn("End Date"),
                "PROJECTED_MONTHLY_BURN": st.column_config.NumberColumn("Projected Burn ($)", format="$%,.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No subcontractor allocation records found.")

