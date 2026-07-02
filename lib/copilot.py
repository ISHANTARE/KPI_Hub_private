"""
lib/copilot.py
--------------
AI Governance Copilot dialog.
Uses lib.styling.COLORS for all visual tokens.
"""

import streamlit as st
from lib.styling import COLORS
from lib.ai_service import chat

QUICK_PROMPTS = [
    ("High Risks",           "Show high-risk projects"),
    ("ASPICE Status",        "Which projects are ASPICE ready?"),
    ("Overdue Risks",        "List top 5 overdue risks with owners"),
    ("Governance Report",    "Generate weekly governance report for PMO"),
    ("Resource Availability","Which resources will be available next month and at what capacity?"),
    ("Recommendations",      "Recommend 3 actions to improve our readiness score"),
]


def init_copilot_state():
    if 'copilot_history' not in st.session_state:
        st.session_state['copilot_history'] = []
    if 'show_copilot' not in st.session_state:
        st.session_state['show_copilot'] = False
    if 'copilot_pending_query' not in st.session_state:
        st.session_state['copilot_pending_query'] = None


if hasattr(st, "dialog"):
    @st.dialog("AI Copilot", width="large")
    def _copilot_dialog(data_context, global_kpis=None):
        _render_copilot_body(data_context, global_kpis)
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("AI Copilot", width="large")
    def _copilot_dialog(data_context, global_kpis=None):
        _render_copilot_body(data_context, global_kpis)
else:
    def _copilot_dialog(data_context, global_kpis=None):
        pass


def launch_copilot(data_context, global_kpis=None):
    init_copilot_state()
    if hasattr(st, "dialog") or hasattr(st, "experimental_dialog"):
        _copilot_dialog(data_context, global_kpis)
    else:
        st.session_state['show_copilot'] = True
        _copilot_inline(data_context, global_kpis)


def _copilot_inline(data_context, global_kpis=None):
    st.divider()
    with st.container():
        _render_copilot_body(data_context, global_kpis)


def _inject_copilot_css():
    """Scoped CSS for the copilot dialog — aligns with design system tokens."""
    st.markdown(f"""
        <style>
        /* Quick prompt ghost buttons */
        div[data-testid="stDialog"] .stButton > button,
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            background: transparent !important;
            border: 1px solid {COLORS['border']} !important;
            color: {COLORS['text_secondary']} !important;
            box-shadow: none !important;
            font-size: 12px !important;
            font-weight: 500 !important;
        }}
        div[data-testid="stDialog"] .stButton > button:hover,
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {{
            border-color: {COLORS['border_strong']} !important;
            background: {COLORS['surface_raised']} !important;
            color: {COLORS['text_primary']} !important;
        }}
        /* Primary send button */
        div[data-testid="stDialog"] button[kind="primary"],
        div[data-testid="stVerticalBlockBorderWrapper"] button[kind="primary"] {{
            background: {COLORS['blue']} !important;
            border: none !important;
            color: #FFFFFF !important;
        }}
        div[data-testid="stDialog"] button[kind="primary"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"] button[kind="primary"]:hover {{
            background: #1741B8 !important;
        }}
        /* Message bubbles */
        .copilot-user-msg {{
            background: {COLORS['blue_bg']};
            border: 1px solid #BFDBFE;
            border-radius: 6px;
            padding: 8px 12px;
            margin: 6px 0;
            font-size: 13px;
            color: {COLORS['text_primary']};
            text-align: right;
        }}
        .copilot-ai-label {{
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: {COLORS['text_muted']};
            margin-top: 12px;
            margin-bottom: 2px;
        }}
        </style>
    """, unsafe_allow_html=True)


def _render_copilot_body(data_context, global_kpis=None):
    _inject_copilot_css()

    # Header row
    hc1, hc2, hc3 = st.columns([5, 1, 1])
    with hc1:
        st.markdown(
            f"<span style='font-size:12px;color:{COLORS['text_muted']};'>"
            f"Messages: {len(st.session_state['copilot_history'])}</span>",
            unsafe_allow_html=True,
        )
    with hc2:
        if st.button("Clear", key="clear_chat", width='stretch'):
            st.session_state['copilot_history'] = []
            st.rerun()
    with hc3:
        if st.button("Close", key="close_chat", width='stretch'):
            st.session_state['show_copilot'] = False
            st.rerun()

    st.divider()

    chat_placeholder = st.container(height=380)

    st.divider()

    user_msg = st.chat_input("Ask anything about the program portfolio...")

    pending = st.session_state.pop('copilot_pending_query', None)
    if pending:
        _send_message(pending, data_context, global_kpis)
    elif user_msg:
        _send_message(user_msg.strip(), data_context, global_kpis)

    with chat_placeholder:
        if not st.session_state['copilot_history']:
            # Empty state
            st.markdown(
                f"<div style='text-align:center;padding:24px 0;'>"
                f"<div style='font-size:14px;font-weight:700;color:{COLORS['text_primary']};'>"
                f"AI Governance Copilot</div>"
                f"<div style='font-size:12px;color:{COLORS['text_muted']};margin-top:4px;'>"
                f"Governance anomaly detector &amp; program advisor</div>"
                f"<div style='font-size:12px;color:{COLORS['text_muted']};margin-top:16px;'>"
                f"Select a prompt or ask anything below:</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            for i in range(0, len(QUICK_PROMPTS), 2):
                qc1, qc2 = st.columns(2)
                for j, col in enumerate([qc1, qc2]):
                    idx = i + j
                    if idx < len(QUICK_PROMPTS):
                        label, prompt = QUICK_PROMPTS[idx]
                        if col.button(label, key=f"qp_{idx}", width='stretch'):
                            st.session_state['copilot_pending_query'] = prompt
        else:
            for msg in st.session_state['copilot_history']:
                role    = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    st.markdown(
                        f'<div class="copilot-user-msg">{content}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="copilot-ai-label">AI Copilot</div>',
                        unsafe_allow_html=True,
                    )
                    with st.container():
                        st.markdown(content)


def _send_message(user_message: str, data_context: dict, global_kpis: dict = None):
    st.session_state['copilot_history'].append({'role': 'user', 'content': user_message})

    if global_kpis:
        data_context['global_kpis'] = global_kpis

    low_msg = user_message.lower()

    # ── Local fast-path: resource availability ────────────────────────────
    if any(k in low_msg for k in ("available next month", "availability next month", "available in july")):
        try:
            import pandas as pd
            from dateutil.relativedelta import relativedelta
            from datetime import datetime

            util_df      = pd.read_csv("data/resources/monthly_utilization.csv")
            next_month_dt = datetime.now() + relativedelta(months=1)
            next_month   = next_month_dt.strftime("%B")
            year         = next_month_dt.year
            nm_df        = util_df[(util_df['MONTH'] == next_month) & (util_df['YEAR'] == year)]
            total_util   = nm_df.groupby('RESOURCE_ID')['UTILIZATION_PCT'].sum().reset_index()

            available_list = []
            for _, r in total_util.iterrows():
                free_cap = round(max(0.0, 1.0 - float(r['UTILIZATION_PCT'])) * 100)
                if free_cap > 0:
                    available_list.append(f"- **{r['RESOURCE_ID']}**: {free_cap}% available")

            if available_list:
                resp = f"Resource availability for **{next_month} {year}**:\n\n" + "\n".join(available_list)
            else:
                resp = f"All resources are fully allocated for **{next_month} {year}**."
        except Exception as e:
            resp = f"Could not read resource matrix: {e}"

        st.session_state['copilot_history'].append({'role': 'assistant', 'content': resp})
        return

    # ── Local fast-path: utilization risk ────────────────────────────────
    if "utilization risk" in low_msg:
        try:
            import pandas as pd
            from datetime import datetime

            util_df = pd.read_csv("data/resources/monthly_utilization.csv")
            res_cfg: dict = {}
            try:
                from integrations.config_helper import load_config
                res_cfg = load_config("integrations/config.yaml").get("resources", {}).get("risk_thresholds", {})
            except Exception:
                pass
            under_threshold = float(res_cfg.get("underutilized_pct", 50))
            over_threshold  = float(res_cfg.get("overallocated_pct", 120))

            # Aggregate total utilisation per resource-month
            agg = (
                util_df.groupby(["YEAR", "MONTH", "RESOURCE_ID"])["UTILIZATION_PCT"]
                .sum()
                .reset_index()
            )

            risky_months: list[str] = []
            for (year, month), grp in agg.groupby(["YEAR", "MONTH"]):
                avg_util = grp["UTILIZATION_PCT"].mean()
                if avg_util < under_threshold or avg_util > over_threshold:
                    over_res  = grp[grp["UTILIZATION_PCT"] >= over_threshold]["RESOURCE_ID"].tolist()
                    under_res = grp[grp["UTILIZATION_PCT"] <= under_threshold]["RESOURCE_ID"].tolist()
                    detail = f"avg={avg_util:.0f}%"
                    if over_res:
                        detail += f", overallocated: {', '.join(over_res[:3])}"
                    if under_res:
                        detail += f", underutilized: {', '.join(under_res[:3])}"
                    risky_months.append(f"**{month} {year}** — {detail}")

            if risky_months:
                resp = (
                    f"Utilization risk detected in {len(risky_months)} month(s):\n\n"
                    + "\n".join(f"- {m}" for m in risky_months)
                    + f"\n\nThresholds: under ≤{under_threshold:.0f}%, over ≥{over_threshold:.0f}%."
                )
            else:
                resp = (
                    f"No utilization risk detected. All months are within the "
                    f"{under_threshold:.0f}%–{over_threshold:.0f}% target band."
                )
        except Exception as e:
            resp = f"Could not calculate utilization risk from data: {e}"

        st.session_state['copilot_history'].append({'role': 'assistant', 'content': resp})
        return

    # ── AI call ───────────────────────────────────────────────────────────
    with st.spinner("Thinking..."):
        ai_response = chat(
            query=user_message,
            data_context=data_context,
            history=st.session_state['copilot_history'][-10:],
        )

    if ai_response:
        st.session_state['copilot_history'].append({'role': 'assistant', 'content': ai_response})
    else:
        st.session_state['copilot_history'].append({
            'role': 'assistant',
            'content': "Could not reach the AI service. Ensure OPENAI_API_KEY is set.",
        })

    # Keep history bounded
    if len(st.session_state['copilot_history']) > 20:
        st.session_state['copilot_history'] = st.session_state['copilot_history'][-20:]
