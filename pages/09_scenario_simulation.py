"""
pages/09_scenario_simulation.py
-------------------------------
What-If Scenario Simulation Engine for KPI Hub.
Allows program managers to simulate resource rebalancing, budget reallocation,
and schedule compression without mutating operational records.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import lib.sidebar as sidebar
import lib.data_loader as data_loader
import lib.kpi_engine as kpi_engine
from lib.evm_engine import calculate_evm_metrics, calculate_forecasts
from lib.styling import render_page_header, COLORS

sidebar.bootstrap_sidebar()

data = data_loader.load_data()
if data is None:
    st.error("Could not load data. Please ensure CSV files are in the data/ folder.")
    st.stop()

render_page_header(
    "What-If Scenario Simulation Engine",
    "Simulate resource reallocation, budget shifts, and schedule compression to evaluate portfolio impacts."
)

st.info("**Sandbox Environment:** Adjust parameters below to model portfolio scenarios in real-time. Changes here do not alter live database records.")

base_kpis = kpi_engine.calculate_kpis(data)
base_evm = kpi_engine.calculate_portfolio_evm(data)
projects_df = data.get('projects', pd.DataFrame()).copy()
budget_df = data.get('budget', pd.DataFrame()).copy()

# ===========================================================================
# Simulation Control Panel
# ===========================================================================
st.markdown("### Scenario Control Panel")

col1, col2, col3 = st.columns(3)

with col1:
    resource_shift_pct = st.slider(
        "Senior Specialist Reallocation (%)",
        min_value=-50,
        max_value=50,
        value=0,
        step=5,
        help="Reallocate senior safety and system architects to bottlenecked projects."
    )

with col2:
    budget_shift_pct = st.slider(
        "Capital Budget Reallocation (%)",
        min_value=-30,
        max_value=30,
        value=0,
        step=5,
        help="Shift contingency budget toward critical-path R&D milestones."
    )

with col3:
    velocity_change_pct = st.slider(
        "Engineering Velocity Delta (%)",
        min_value=-20,
        max_value=30,
        value=0,
        step=5,
        help="Simulate productivity shifts due to automation or scope changes."
    )

# ===========================================================================
# Compute Simulated Impact
# ===========================================================================
sim_health = min(100.0, max(0.0, base_kpis['portfolio_health'] + (resource_shift_pct * 0.15) + (velocity_change_pct * 0.2)))
sim_readiness = min(100.0, max(0.0, base_kpis['release_readiness'] + (resource_shift_pct * 0.2) + (velocity_change_pct * 0.25)))
sim_cpi = round(max(0.5, base_evm['portfolio_cpi'] + (budget_shift_pct * 0.005) - (resource_shift_pct * 0.002)), 2)
sim_spi = round(max(0.5, base_evm['portfolio_spi'] + (velocity_change_pct * 0.008) + (resource_shift_pct * 0.003)), 2)

base_eac = base_evm['portfolio_eac']
sim_eac = round(base_eac / (sim_cpi / base_evm['portfolio_cpi']), 2) if base_evm['portfolio_cpi'] > 0 else base_eac

st.divider()

# ===========================================================================
# Simulated Metrics Comparison
# ===========================================================================
st.markdown("### Baseline vs. Simulated Portfolio Impact")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric(
        "Simulated Health Index",
        f"{sim_health:.1f}%",
        delta=f"{sim_health - base_kpis['portfolio_health']:+.1f}%",
        delta_color="normal" if sim_health >= base_kpis['portfolio_health'] else "inverse"
    )

with m_col2:
    st.metric(
        "Simulated Release Readiness",
        f"{sim_readiness:.1f}%",
        delta=f"{sim_readiness - base_kpis['release_readiness']:+.1f}%",
        delta_color="normal" if sim_readiness >= base_kpis['release_readiness'] else "inverse"
    )

with m_col3:
    st.metric(
        "Simulated CPI",
        f"{sim_cpi:.2f}",
        delta=f"{sim_cpi - base_evm['portfolio_cpi']:+.2f}",
        delta_color="normal" if sim_cpi >= base_evm['portfolio_cpi'] else "inverse"
    )

with m_col4:
    st.metric(
        "Simulated EAC Forecast",
        f"${sim_eac:,.0f}",
        delta=f"${sim_eac - base_eac:+,.0f}",
        delta_color="normal" if sim_eac <= base_eac else "inverse"
    )

st.divider()

# ===========================================================================
# Visual Scenario Comparison Chart
# ===========================================================================
st.markdown("### Metric Comparison Radar / Bar View")

categories = ['Portfolio Health', 'Release Readiness', 'On-Time Delivery', 'Quality Score']
baseline_vals = [base_kpis['portfolio_health'], base_kpis['release_readiness'], base_kpis['on_time_delivery'], base_kpis['quality_score']]
simulated_vals = [sim_health, sim_readiness, min(100.0, base_kpis['on_time_delivery'] + velocity_change_pct), base_kpis['quality_score']]

fig = go.Figure()
fig.add_trace(go.Bar(x=categories, y=baseline_vals, name='Baseline Actuals', marker_color='#3B82F6'))
fig.add_trace(go.Bar(x=categories, y=simulated_vals, name='Simulated Scenario', marker_color='#10B981'))

fig.update_layout(
    title="Portfolio Performance: Baseline vs. Simulated Scenario",
    barmode='group',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=COLORS.get('text_primary', '#FFFFFF')),
    height=350
)
st.plotly_chart(fig, width='stretch')

st.divider()

# ===========================================================================
# Granular Resource Move Simulator
# ===========================================================================
st.markdown("### Granular Resource Move Simulator")
st.caption("Model moving specific engineering team members between projects to evaluate headcount capacity shifts, release readiness changes, and cost deltas.")

# Load active projects and resources
projects_list = sorted(projects_df['PROJECT_ID'].unique().tolist()) if not projects_df.empty else []
res_df = data.get('resources', pd.DataFrame())

col_sim1, col_sim2 = st.columns(2)

with col_sim1:
    source_proj = st.selectbox("Source Project (From)", options=projects_list, index=0 if len(projects_list) > 0 else None, key="sim_src_proj")
    # Filter resources to those currently allocated to source project
    source_resources = []
    if not res_df.empty and source_proj:
        source_resources = sorted(res_df[res_df['PROJECT_ID'] == source_proj]['TEAM_MEMBER'].dropna().unique().tolist())
    
    selected_moved_res = st.multiselect("Select Team Members to Move", options=source_resources, key="sim_moved_resources")

with col_sim2:
    # Target project options (exclude source project)
    target_options = [p for p in projects_list if p != source_proj]
    target_proj = st.selectbox("Target Project (To)", options=target_options, index=0 if len(target_options) > 0 else None, key="sim_tgt_proj")
    duration_wks = st.slider("Move Duration (Weeks)", min_value=1, max_value=12, value=4, key="sim_duration")

if st.button("Run Resource Move Simulation", type="primary"):
    if not selected_moved_res:
        st.warning("Please select at least one team member to move.")
    elif not source_proj or not target_proj:
        st.warning("Please select both source and target projects.")
    else:
        from lib.scenario_engine import simulate_resource_move
        sim_res = simulate_resource_move(data, source_proj, target_proj, selected_moved_res, duration_wks)
        
        st.success(f"Successfully simulated reallocation of {sim_res['moved_count']} resource(s)!")
        
        # Display deltas
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            orig_rr = sim_res['original_kpis'].get('release_readiness', 0.0)
            sim_rr = sim_res['simulated_kpis'].get('release_readiness', 0.0)
            st.metric(
                "Simulated Release Readiness",
                f"{sim_rr:.1f}%",
                delta=f"{sim_rr - orig_rr:+.1f}%",
                delta_color="normal" if sim_rr >= orig_rr else "inverse"
            )
        with col_res2:
            orig_util = sim_res['original_util']
            sim_util = sim_res['simulated_util']
            st.metric(
                "Simulated Resource Utilization",
                f"{sim_util:.1f}%",
                delta=f"{sim_util - orig_util:+.1f}%",
                delta_color="off"
            )
        with col_res3:
            st.metric(
                "Estimated Cost Delta",
                f"${sim_res['cost_delta']:,.2f}",
                help="Projected cost reallocation for the moved resources over the simulated duration."
            )
            
        # Before/after comparison table
        comp_data = {
            "Metric": ["Portfolio Health Score", "Release Readiness Score", "Active Components"],
            "Baseline": [
                f"{sim_res['original_kpis'].get('portfolio_health', 0.0):.1f}%",
                f"{sim_res['original_kpis'].get('release_readiness', 0.0):.1f}%",
                str(sim_res['original_kpis'].get('active_components', 0))
            ],
            "Simulated": [
                f"{sim_res['simulated_kpis'].get('portfolio_health', 0.0):.1f}%",
                f"{sim_res['simulated_kpis'].get('release_readiness', 0.0):.1f}%",
                str(sim_res['simulated_kpis'].get('active_components', 0))
            ],
            "Change": [
                f"{sim_res['simulated_kpis'].get('portfolio_health', 0.0) - sim_res['original_kpis'].get('portfolio_health', 0.0):+.1f}%",
                f"{sim_res['simulated_kpis'].get('release_readiness', 0.0) - sim_res['original_kpis'].get('release_readiness', 0.0):+.1f}%",
                f"{sim_res['simulated_kpis'].get('active_components', 0) - sim_res['original_kpis'].get('active_components', 0):+d}"
            ]
        }
        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

