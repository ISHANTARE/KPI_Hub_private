"""
pages/08_ai_insights.py
AI-powered copilot, governance analysis, and traceability intelligence.
"""
import streamlit as st
import pandas as pd

import lib.sidebar as sidebar
import lib.data_loader as data_loader
import lib.kpi_engine as kpi_engine
from lib.styling import render_page_header, COLORS
from lib.sidebar import apply_scope_filter
from lib.copilot import launch_copilot

try:
    from lib.governance_agent import GovernanceAnalyzer
    _has_governance = True
except Exception:
    _has_governance = False

try:
    from integrations.openai_client import get_completion
    _has_openai = True
except Exception:
    _has_openai = False

# ── Bootstrap & load ────────────────────────────────────────────────────────
sidebar.bootstrap_sidebar()
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

global_kpis = kpi_engine.calculate_kpis(data)

render_page_header(
    "AI Insights",
    "AI-powered copilot, governance analysis, and traceability intelligence.",
)

# ── Live KPI summary ──────────────────────────────────────────────────────────
_projects  = data.get('projects',  pd.DataFrame())
_risks     = data.get('risks',     pd.DataFrame())
_tests     = data.get('tests',     pd.DataFrame())
_resources = data.get('resources', pd.DataFrame())
_aspice    = data.get('aspice',    pd.DataFrame())

ph_score   = round(global_kpis.get('portfolio_health',  0), 1)
otd_score  = round(global_kpis.get('on_time_delivery',  0), 1)
tpr_score  = round(global_kpis.get('test_pass_rate',    0), 1)
crit_risks = int(global_kpis.get('critical_risks', 0))

ph_status  = "HEALTHY" if ph_score >= 75 else ("WATCHLIST" if ph_score >= 60 else "CRITICAL")

# Resource bottlenecks
bottlenecks = []
if not _resources.empty and 'UTILIZATION_PCT' in _resources.columns:
    try:
        _res = _resources.copy()
        _res['_util'] = _res['UTILIZATION_PCT'].astype(str).str.rstrip('%').astype(float)
        _over = _res[_res['_util'] >= 110]
        for _, row in _over.iterrows():
            name = row.get('TEAM_MEMBER') or row.get('RESOURCE_ID') or 'Unknown'
            util = row['_util']
            proj = row.get('PROJECT_ID', '')
            bottlenecks.append(f"{name} at {util:.0f}% ({proj})")
    except Exception:
        pass

obs_lines = [
    f"**Portfolio Health:** {ph_score}% — status: **{ph_status}**",
    f"**On-Time Delivery:** {otd_score}%",
    f"**Test Pass Rate:** {tpr_score}%",
    f"**Critical Risks Open:** {crit_risks}",
]
if bottlenecks:
    obs_lines.append(f"**Resource Bottlenecks:** {'; '.join(bottlenecks[:3])}")

action_lines = []
if ph_score < 60:
    action_lines.append("Portfolio is CRITICAL — schedule an emergency steering committee review.")
elif ph_score < 75:
    action_lines.append("Portfolio is in WATCHLIST — prioritise top-3 risks for mitigation this sprint.")
if otd_score < 80:
    action_lines.append(f"On-time delivery ({otd_score}%) is below 80% — review milestone plans for slipping projects.")
if tpr_score < 80:
    action_lines.append(f"Test pass rate ({tpr_score}%) is below 80% — run regression review and close critical defects first.")
if crit_risks > 0:
    action_lines.append(f"{crit_risks} critical risk(s) require immediate owner assignment and mitigation action.")
if not action_lines:
    action_lines.append("All key KPIs are on track. Continue current execution cadence.")

obs_md = "\n".join(f"{i+1}. {l}" for i, l in enumerate(obs_lines))
act_md = "\n".join(f"- {l}" for l in action_lines)

st.info(f"**Key Observations (live data):**\n\n{obs_md}\n\n**Recommended Actions:**\n\n{act_md}")

with st.expander("✨ Generate AI Narrative for these observations"):
    if st.button("Generate AI Insights Narrative"):
        if _has_openai:
            with st.spinner("Generating AI narrative..."):
                ai_prompt = (
                    f"You are an automotive engineering PMO advisor. Based on these live KPI observations, "
                    f"provide a 4-6 bullet executive narrative with specific, actionable next steps:\n\n"
                    f"{obs_md}\n\n{act_md}\n\n"
                    f"Keep it concise, factual, and suitable for a steering committee."
                )
                ai_narrative = get_completion(ai_prompt)
            if ai_narrative:
                st.markdown(ai_narrative)
            else:
                st.warning("AI narrative unavailable — ensure OPENAI_API_KEY is set.")
        else:
            st.warning("OpenAI client not available.")

st.divider()

# ── AI Copilot ────────────────────────────────────────────────────────────────
st.markdown("#### AI Copilot")
copilot_clicked = st.button("Launch AI Copilot", use_container_width=False, type="primary")

if hasattr(st, "dialog") or hasattr(st, "experimental_dialog"):
    if copilot_clicked:
        launch_copilot(data, global_kpis=global_kpis)
else:
    if copilot_clicked:
        st.session_state['show_copilot'] = True
    if st.session_state.get('show_copilot', False):
        launch_copilot(data, global_kpis=global_kpis)

st.divider()

# ── Governance & Traceability Analysis ───────────────────────────────────────
st.markdown("#### Governance & Traceability Analysis")

if _has_governance:
    with st.spinner("Analyzing traceability gaps..."):
        gov_analyzer = GovernanceAnalyzer()
        gov_results  = gov_analyzer.analyze_traceability(data)

        st.metric("Overall Traceability Score", f"{gov_results['score']:.1f}%")

        if gov_results['gaps']:
            st.warning(f"Detected {len(gov_results['gaps'])} governance gaps. Review required.")
            for gap in gov_results['gaps']:
                st.error(f"**{gap['type']} ({gap['item']}):** {gap['description']}")
        else:
            st.success("No governance gaps detected. Traceability is 100%.")
else:
    st.info("Governance analyzer module not available.")

st.divider()

# ── Lessons Learned & Standards Lookup ───────────────────────────────────────
st.markdown("#### Lessons Learned & Standards Lookup")

rag_databases = [
    "All Databases (Federated Search)",
    "Automotive Lessons Learned (Internal - Project Histories)",
    "ISO 26262 Functional Safety Standards & Guidelines",
    "STRIDE Threat Modeling Definitions & Examples",
    "CFD & Thermal Simulation Best Practices",
]
selected_rag = st.selectbox("Select Knowledge Base to Query:", options=rag_databases)

search_query = st.text_input("Search knowledge base for keywords (e.g., safety, CFD, security)")
if search_query:
    st.markdown(f"**Search results for: *{search_query}***")
    results = []

    if "safety" in search_query.lower() or "iso" in search_query.lower() or "asil" in search_query.lower():
        results.append({
            "Source": "Lessons Learned (Project P003)",
            "Content": "ASIL decomposition from ASIL-D to ASIL-B(D) and ASIL-A(D) should be baselined at Change Request stage to avoid safety validation blockages during late-stage execution."
        })
        results.append({
            "Source": "ISO 26262-6 Standard Reference",
            "Content": "Part 6 details requirements for software development, verification, and compliance matrices corresponding to respective ASIL target levels."
        })
    elif "cfd" in search_query.lower() or "resource" in search_query.lower() or "thermal" in search_query.lower():
        results.append({
            "Source": "Lessons Learned (Project P001)",
            "Content": "CFD thermal analysis resource constraints can block prototype gates. Recommend scheduling backup engineering consultants at least 4 weeks in advance of design reviews."
        })
    elif "cyber" in search_query.lower() or "stride" in search_query.lower() or "security" in search_query.lower():
        results.append({
            "Source": "Standards Reference (ISO 21434)",
            "Content": "Requires STRIDE-based threat analysis and risk assessment (TARA) to establish cybersecurity requirement baselines for gateway modules."
        })
    else:
        results.append({
            "Source": "KPI Hub general RAG database",
            "Content": f"No direct standards match for '{search_query}'. Showing general lesson: Ensure daily/weekly commits and reviews are synced before steering committee audit."
        })

    for res in results:
        with st.expander(res['Source']):
            st.write(res['Content'])

st.divider()

# ── Traceability Heatmap ──────────────────────────────────────────────────────
st.markdown("#### Traceability Intelligence")
try:
    import lib.charts as charts
    reqs      = data.get('requirements', pd.DataFrame())
    tests_df  = data.get('tests', pd.DataFrame())
    trace_ins = data.get('traceability_insights', pd.DataFrame())

    if not trace_ins.empty:
        st.caption(f"Traceability analysis found {len(trace_ins)} insight records.")
        fig_trace = charts.build_traceability_heatmap_chart(trace_ins)
        st.plotly_chart(fig_trace, use_container_width=True)
    else:
        st.info("No traceability insight data found. Ensure requirements and tests are loaded.")
except Exception as e:
    st.info(f"Traceability chart unavailable: {e}")
