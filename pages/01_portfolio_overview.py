"""
pages/01_portfolio_overview.py
-------------------------------
Portfolio Overview dashboard page for KPI Hub.

Renders program health, risk status, and escalation flags across all active
projects. Extracted from the `if "Portfolio Overview" in selected:` branch of
web_app.py's main() function.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import lib.sidebar as sidebar
import lib.data_loader as data_loader
import lib.kpi_engine as kpi_engine
import lib.charts as charts
from lib.styling import (
    render_page_header, badge, severity_badge, escalation_panel,
    COLORS, CHART_DEFAULTS, STATUS_COLORS,
)
from integrations.openai_client import get_completion

sidebar.bootstrap_sidebar()

data = data_loader.load_data()
if data is None:
    st.error("Could not load data. Please ensure CSV files are in the data/ folder.")
    st.stop()

# ---------------------------------------------------------------------------
# Apply role-based budget visibility
# ---------------------------------------------------------------------------
if st.session_state.get('user_role') != 'Manager':
    if st.session_state.get('user_role') == 'Project Manager' and st.session_state.get('current_pm'):
        pm_identity = st.session_state['current_pm']
        try:
            org_df_filter = pd.read_csv('data/resources/org_mapping.csv')
            pm_projects = org_df_filter[org_df_filter['MANAGER_NAME'] == pm_identity]['PROJECT_ID'].dropna().unique().tolist()
            if 'budget' in data:
                data['budget'] = data['budget'][data['budget']['PROJECT_ID'].isin(pm_projects)].reset_index(drop=True)
        except Exception as e:
            st.error(f"Error applying PM budget filters: {e}")
    else:
        if 'budget' in data:
            data['budget'] = pd.DataFrame(columns=data['budget'].columns)

# ---------------------------------------------------------------------------
# Apply scope filter
# ---------------------------------------------------------------------------
from lib.sidebar import apply_scope_filter

org_df = pd.DataFrame()
try:
    org_df = pd.read_csv('data/resources/org_mapping.csv')
except Exception:
    pass

selected_manager = st.session_state.get('current_manager', 'All')
selected_project = st.session_state.get('current_project', 'All')
data = apply_scope_filter(data, selected_manager, selected_project, org_df)

kpis = kpi_engine.calculate_kpis(data)

# ===========================================================================
# Page Header
# ===========================================================================
render_page_header(
    "Portfolio Overview",
    "Program health, risk status, and escalation flags across all active projects.",
)

# ===========================================================================
# AI Weekly Summary
# ===========================================================================
if st.session_state.get('run_ai_summary', False):
    st.session_state['run_ai_summary'] = False
    with st.spinner("Generating AI summary..."):
        try:
            _projects = data.get('projects')
            _risks = data.get('risks')
            _defects = data.get('defects')
            _tests = data.get('tests')
            _milestones = data.get('milestones')

            total_projects = len(_projects) if _projects is not None else 0
            critical_risks = 0
            top_risks = []
            if _risks is not None and len(_risks) > 0:
                if 'EXPOSURE_SCORE' in _risks.columns:
                    top = _risks.sort_values('EXPOSURE_SCORE', ascending=False).head(3)
                    top_risks = [f"{r['RISK_TITLE']} (exposure={r['EXPOSURE_SCORE']})" for _, r in top.iterrows()]
                else:
                    top = _risks.head(3)
                    top_risks = [r['RISK_TITLE'] for _, r in top.iterrows()]
                critical_risks = len(_risks[_risks['SEVERITY'] == 'CRITICAL']) if 'SEVERITY' in _risks.columns else 0

            open_issues_list = []
            if _defects is not None and len(_defects) > 0:
                open_issues = _defects[_defects.get('STATUS', '') == 'OPEN'] if 'STATUS' in _defects.columns else _defects
                for _, row in open_issues.head(5).iterrows():
                    title = row.get('TITLE') or row.get('ISSUE_TITLE') or str(row.get('DEFECT_ID', ''))
                    open_issues_list.append(title)

            recent_milestones = []
            if _milestones is not None and len(_milestones) > 0:
                if 'END_DATE' in _milestones.columns:
                    try:
                        ms = _milestones.copy()
                        ms['END_DATE'] = pd.to_datetime(ms['END_DATE'], errors='coerce')
                        now_dt = pd.Timestamp.now()
                        window = ms[
                            (ms['END_DATE'] >= (now_dt - pd.Timedelta(days=14))) &
                            (ms['END_DATE'] <= (now_dt + pd.Timedelta(days=30)))
                        ]
                        for _, m in window.head(5).iterrows():
                            recent_milestones.append(
                                f"{m.get('SPRINT_NAME') or m.get('MILESTONE') or m.get('name')} on {m['END_DATE'].date()}"
                            )
                    except Exception:
                        recent_milestones = list(_milestones.head(5).astype(str).itertuples(index=False, name=None))

            test_pass_rate = 0
            try:
                if _tests is not None and len(_tests) > 0 and 'STATUS' in _tests.columns:
                    test_pass_rate = (len(_tests[_tests['STATUS'] == 'PASSED']) / len(_tests)) * 100
            except Exception:
                test_pass_rate = 0

            prompt = (
                f"You are an engineering program analyst. Produce a concise weekly executive summary (4-6 bullets) for leadership. "
                f"Context: total_projects={total_projects}, critical_risks={critical_risks}, test_pass_rate={test_pass_rate:.1f}%.\n"
            )
            if top_risks:
                prompt += "Top risks: " + "; ".join(top_risks) + ".\n"
                prompt += "For each top risk, provide 1-2 concise mitigation actions, suggested owner role, and an estimated timeline.\n"
            if open_issues_list:
                prompt += "Top open issues: " + "; ".join(open_issues_list) + ".\n"
            if recent_milestones:
                prompt += "Recent/upcoming milestones: " + "; ".join(recent_milestones) + ".\n"
            prompt += "End with 2 recommended next actions and a confidence level (low/med/high). Keep it short and actionable."

            ai_text = get_completion(prompt)
            if ai_text:
                st.session_state['ai_summary_text'] = ai_text
            else:
                st.error("AI summary failed — ensure OPENAI_API_KEY is set and network access is available.")
        except Exception as e:
            st.error(f"Failed to generate AI summary: {e}")

if st.session_state.get('ai_summary_text'):
    st.markdown("### Weekly AI Summary")
    st.info(st.session_state['ai_summary_text'])
    st.divider()

# ===========================================================================
# Governance & Escalation Panel
# ===========================================================================
now = datetime.now()

# Calculate Overdue High Risks
risks = data.get('risks', pd.DataFrame())
overdue_high_risks = 0
if not risks.empty and 'DUE_DATE' in risks.columns:
    open_risks = risks[risks['STATUS'] == 'OPEN']
    for _, r in open_risks.iterrows():
        try:
            due_date = pd.to_datetime(r['DUE_DATE'])
            if due_date < now and str(r.get('SEVERITY', '')).upper() in ['HIGH', 'CRITICAL']:
                overdue_high_risks += 1
        except Exception:
            pass

# Calculate ASPICE < 70%
aspice = data.get('aspice', pd.DataFrame())
poor_aspice_projects = 0
if not aspice.empty and 'PROJECT_ID' in aspice.columns and 'ASSESSMENT_READINESS' in aspice.columns:
    for p in aspice['PROJECT_ID'].unique():
        proj_data = aspice[aspice['PROJECT_ID'] == p]
        ready = len(proj_data[proj_data['ASSESSMENT_READINESS'] == 'READY'])
        if len(proj_data) > 0 and (ready / len(proj_data)) < 0.7:
            poor_aspice_projects += 1

# Calculate Pending Decisions > 7 days
decisions = data.get('decisions', pd.DataFrame())
pending_decisions = 0
if not decisions.empty and 'APPROVAL_STATUS' in decisions.columns:
    for _, d in decisions.iterrows():
        if d.get('APPROVAL_STATUS') == 'Pending Approval':
            try:
                due_date = pd.to_datetime(d['DUE_DATE'])
                if (now - due_date).days > 7:
                    pending_decisions += 1
            except Exception:
                pass

st.markdown(escalation_panel([
    {"value": overdue_high_risks,   "label": "Overdue Risks",      "description": "High/Critical past due date"},
    {"value": poor_aspice_projects, "label": "ASPICE Below 70%",   "description": "Projects below readiness threshold"},
    {"value": pending_decisions,    "label": "Pending Decisions",  "description": "Approval delayed 7+ days"},
]), unsafe_allow_html=True)

# ===========================================================================
# One-Click Governance Report
# ===========================================================================
with st.expander("Generate One-Click Weekly Governance Report"):
    report_md = f"""# Weekly Governance Report
**Date:** {now.strftime('%Y-%m-%d')}
## Executive Summary
- Overdue High Risks: {overdue_high_risks}
- Projects failing ASPICE targets: {poor_aspice_projects}
- Bottlenecked Decisions: {pending_decisions}

## Portfolio Status
- Active Projects: {kpis['active_components']}
- Critical Risks: {kpis['critical_risks']}
- Test Pass Rate: {kpis['test_pass_rate']:.1f}%
            """
    st.markdown("Report generated. Review below or download for executive distribution.")
    st.markdown(f"""
    <div style="background-color: var(--card_bg); padding: 20px; border-radius: 8px; border: 1px solid var(--border); margin: 10px 0;">
        <h3 style="margin-top:0; color:var(--text_primary);">Weekly Executive Governance Report</h3>
        <p style="color:var(--text_muted); font-size:12px;">Generated: {now.strftime('%Y-%m-%d %H:%M')}</p>
        <hr style="border-color:var(--border);">
        <h4 style="color:var(--text_primary);">Executive Summary</h4>
        <ul>
            <li><strong>Overdue High/Critical Risks:</strong> {overdue_high_risks}</li>
            <li><strong>Projects failing ASPICE targets:</strong> {poor_aspice_projects}</li>
            <li><strong>Bottlenecked Decisions:</strong> {pending_decisions}</li>
        </ul>
        <h4 style="color:var(--text_primary);">Portfolio Operational Metrics</h4>
        <ul>
            <li><strong>Active Projects:</strong> {kpis['active_components']}</li>
            <li><strong>Critical Risks:</strong> {kpis['critical_risks']}</li>
            <li><strong>Test Pass Rate:</strong> {kpis['test_pass_rate']:.1f}%</li>
            <li><strong>Computed Release Readiness:</strong> {kpis['release_readiness']:.1f}%</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        "Download Executive Report (.md)",
        data=report_md,
        file_name=f"Governance_Report_{now.strftime('%Y%m%d')}.md",
        mime="text/markdown",
    )

st.divider()

# ===========================================================================
# Charts Row 1: Program Health Scores  |  Risk Distribution
# ===========================================================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Program Health Scores")
    fig = charts.build_portfolio_health_chart(data['projects'])
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Risk Distribution")
    fig = charts.build_risk_matrix_chart(data['risks'])
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===========================================================================
# Charts Row 2: Readiness Breakdown  |  Project Health Distribution
# ===========================================================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Portfolio Release Readiness")
    base_maturity = kpis['portfolio_health']
    final_readiness = kpis['release_readiness']

    col1a, col1b = st.columns(2)
    with col1a:
        st.metric("Base Health", f"{base_maturity:.1f}%")
    with col1b:
        st.metric(
            "Release Readiness",
            f"{final_readiness:.1f}%",
            help="Computed via KPI Engine combining portfolio health, test pass rate, resource overallocation penalties, and traceability gap weights."
        )

    st.progress(min(100, max(0, int(final_readiness))) / 100)
    st.caption(f"Engine Release Readiness Score: {final_readiness:.1f}%")

    readiness_categories = ['Design', 'Test', 'Requirements', 'Verification']

    # Requirements rate — from requirements.csv STATUS column
    try:
        reqs = data.get('requirements')
        if reqs is not None and len(reqs) > 0 and 'STATUS' in reqs.columns:
            req_rate = len(reqs[reqs['STATUS'].str.upper() == 'APPROVED']) / len(reqs) * 100
        else:
            req_rate = None
    except Exception:
        req_rate = None

    # Test rate — from tests STATUS column
    try:
        tests_rd = data.get('tests')
        if tests_rd is not None and len(tests_rd) > 0 and 'STATUS' in tests_rd.columns:
            test_rate = len(tests_rd[tests_rd['STATUS'].str.upper() == 'PASSED']) / len(tests_rd) * 100
        else:
            test_rate = None
    except Exception:
        test_rate = None

    # Design rate — from design_reviews.csv ACTION_COMPLETION_PCT column
    # Strip '%' and 'TBD'; average only numeric rows
    try:
        dr = data.get('design_reviews')
        if dr is not None and len(dr) > 0 and 'ACTION_COMPLETION_PCT' in dr.columns:
            _pct = pd.to_numeric(
                dr['ACTION_COMPLETION_PCT'].astype(str).str.rstrip('%').replace('TBD', float('nan')),
                errors='coerce',
            ).dropna()
            design_rate = float(_pct.mean()) if len(_pct) > 0 else None
        else:
            design_rate = None
    except Exception:
        design_rate = None

    # Verification rate — from verification_activities.csv STATUS column
    try:
        ver = data.get('verification')
        if ver is not None and len(ver) > 0 and 'STATUS' in ver.columns:
            _closed = ver['STATUS'].str.upper().isin(['COMPLETED', 'CLOSED', 'PASSED'])
            ver_rate = len(ver[_closed]) / len(ver) * 100
        else:
            ver_rate = None
    except Exception:
        ver_rate = None

    readiness_pcts = [design_rate, test_rate, req_rate, ver_rate]
    bar_texts   = [f"{p:.1f}%" if p is not None else "N/A" for p in readiness_pcts]
    bar_values  = [p if p is not None else 0.0 for p in readiness_pcts]
    readiness_colors = [
        STATUS_COLORS.get("HEALTHY" if (p or 0) >= 75 else ("WATCHLIST" if (p or 0) >= 60 else "CRITICAL"))
        for p in readiness_pcts
    ]

    fig = go.Figure(data=[
        go.Bar(
            y=readiness_categories,
            x=bar_values,
            orientation='h',
            marker=dict(color=readiness_colors),
            text=bar_texts,
            textfont=dict(color=COLORS["text_secondary"], size=11, family='Inter, sans-serif'),
            textposition='outside',
        )
    ])
    r_layout = dict(**CHART_DEFAULTS)
    r_layout["xaxis"] = dict(title="% Complete", range=[0, 120], **CHART_DEFAULTS["xaxis"])
    r_layout["height"] = 240
    r_layout["margin"] = dict(t=8, b=8, l=0, r=0)
    fig.update_layout(**r_layout)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Project Health Distribution")
    projects = data['projects']
    health_counts_series = pd.cut(
        projects['HEALTH_SCORE'],
        bins=[0, 60, 75, 90, 100],
        labels=['Critical', 'Watchlist', 'Healthy', 'Excellent'],
    ).value_counts()

    categories_order = ['Excellent', 'Healthy', 'Watchlist', 'Critical']
    counts_ordered   = [health_counts_series.get(cat, 0) for cat in categories_order]
    h_colors         = [STATUS_COLORS[c.upper()] for c in categories_order]

    fig = go.Figure(data=[
        go.Bar(
            x=categories_order,
            y=counts_ordered,
            marker_color=h_colors,
            text=counts_ordered,
            textposition='outside',
            textfont=dict(color=COLORS["text_secondary"], size=13, family='Inter, sans-serif'),
        )
    ])
    h_layout = dict(**CHART_DEFAULTS)
    h_layout["height"] = 300
    h_layout["xaxis"] = dict(title="", **CHART_DEFAULTS["xaxis"])
    h_layout["yaxis"] = dict(title="Projects", **CHART_DEFAULTS["yaxis"])
    fig.update_layout(**h_layout)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===========================================================================
# Critical Items: Critical Risks | Open Issues | Resource Utilization
# ===========================================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Critical Risks")
    critical_risks_df = data['risks'][data['risks']['SEVERITY'] == 'CRITICAL']
    if len(critical_risks_df) > 0:
        for _, risk in critical_risks_df.head(3).iterrows():
            st.markdown(
                f'<div class="data-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                f'{severity_badge("CRITICAL")}'
                f'<span class="data-card-meta">Exposure: {risk["EXPOSURE_SCORE"]}/9</span>'
                f'</div>'
                f'<div class="data-card-title">{risk["RISK_TITLE"]}</div>'
                f'<div class="data-card-meta" style="margin-top:4px;">{risk["OWNER"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("**Top Risks**")
        for _, r in critical_risks_df.head(3).iterrows():
            st.markdown(f"- **{r['PROJECT_ID']}** — {r['RISK_TITLE']}")
    else:
        st.markdown(
            '<div class="data-card" style="border-left:3px solid var(--green);">'
            '<div class="data-card-title" style="color:var(--green);">No critical risks detected</div>'
            '</div>',
            unsafe_allow_html=True,
        )

with col2:
    st.markdown("#### Open Issues")
    open_issues = data['issues'][data['issues']['STATUS'] == 'OPEN']
    st.metric("Total Open Issues", len(open_issues))
    if len(open_issues) > 0:
        for idx, issue in open_issues.head(3).iterrows():
            severity = str(issue['SEVERITY']).upper()
            sev_map = {"HIGH": "red", "CRITICAL": "red", "MEDIUM": "amber", "LOW": "green"}
            issue_id = issue.get('ISSUE_ID') or issue.get('ID') or f'I{idx+1}'
            st.markdown(
                f'<div class="data-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                f'{badge(severity, sev_map.get(severity, "blue"))}'
                f'<span class="data-card-meta">{issue_id}</span>'
                f'</div>'
                f'<div class="data-card-title">{issue["ISSUE_TITLE"]}</div>'
                f'<div class="data-card-meta" style="margin-top:4px;">{issue["ASSIGNED_TO"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="data-card" style="border-left:3px solid var(--green);">'
            '<div class="data-card-title" style="color:var(--green);">No open issues</div>'
            '</div>',
            unsafe_allow_html=True,
        )

with col3:
    st.markdown("#### Resource Utilization")
    resources = data['resources']
    try:
        overallocated = len(resources[resources['UTILIZATION_PCT'].str.rstrip('%').astype(float) > 100.0])
        avg_util = resources['UTILIZATION_PCT'].str.rstrip('%').astype(float).mean()
    except Exception:
        overallocated = 0
        avg_util = 0.0

    st.metric("Avg Utilization", f"{avg_util:.1f}%")
    ovr_color = COLORS["red"] if overallocated > 0 else COLORS["green"]
    st.markdown(
        f'<div class="data-card">'
        f'<div class="data-card-meta">OVERALLOCATED RESOURCES</div>'
        f'<div style="font-size:28px;font-weight:700;color:{ovr_color};line-height:1.2;">{overallocated}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    try:
        cfd = resources[resources['TEAM_MEMBER'].str.contains('CFD', case=False, na=False)]
        if not cfd.empty:
            cfd_util = cfd.iloc[0].get('UTILIZATION_PCT', 'N/A')
            st.markdown(
                f'<div class="data-card">'
                f'<div class="data-card-title">CFD Team</div>'
                f'<div class="data-card-meta">Utilization: {cfd_util}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass
