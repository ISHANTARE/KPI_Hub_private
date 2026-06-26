"""
AI Service for KPI Dashboard
Provides LLM-powered analysis, Q&A, and recommendations.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from integrations.openai_client import get_completion

logger = logging.getLogger(__name__)

# ============================================================
# SYSTEM PROMPT
# ============================================================

_SYSTEM_PROMPT = """\
You are a Governance Anomaly Detector and Decision Support AI for enterprise product operations.
Your role:
  1. Actively cross-reference data across domains (e.g. correlate milestone delays in 'projects' with overallocated personnel in 'resources').
  2. Identify trends, bottlenecks, anomalies, and risks in the provided GitHub/Jira/SharePoint data.
  3. Provide actionable recommendations structured as Facts → Root Causes → Actions.
  4. Answer natural language queries directly based on the provided Data Context.
  5. Help PMs analyze resource availability (e.g., "Which resources will be available next month and at what capacity?").

Response rules:
  - Deliver extremely concise, short answers using structured brevity. Do not write exhaustive prose or essays.
  - When summarizing a project, always use this fixed structure: one sentence on budget status, one on schedule, one on top risk, one recommended action.
  - Bad news first, good news last: always lead with the highest severity risk or budget exhaustion warning if either is present. After that, mention schedule/milestone status, then resource overallocation, then general health. If none of those are red/amber, a short 'all clear' summary is fine.
  - Quantify impacts with numbers from the supplied data context.
  - Never invent numbers not present in the data context.

Data context keys you may receive:
  projects      — Project metadata, budgets, health scores
  budget        — Project monthly budget tracking limits and actuals
  issues        — Jira tickets, blockers, status
  resources     — Personnel, roles, utilization rates, allocation status
  monthly_utilization — Month-by-month resource utilization (RESOURCE_ID, PROJECT_ID, MONTH, YEAR, UTILIZATION_PCT)
  cost_rates    — Monthly cost rates by role (ROLE, COST_RATE_MONTHLY)
  risks         — Project risks and severities
  defects       — Bug reports and severities
  requirements  — Functional requirements and traceability status
  traceability_insights — Computed ASPICE SWE.6 gap analysis (stale, missing, overlinked, etc)
"""


# ============================================================
# TOKEN BUDGETS
# ============================================================

# Hard cap on items sent to the LLM to stay inside context windows
_MAX_PROJECTS   = 10
_MAX_ISSUES     = 30
_MAX_RESOURCES  = 30
_MAX_RISKS      = 30
_MAX_DEFECTS    = 30
_MAX_REQS       = 30

def chat(query: str, data_context: Dict[str, Any], history: List[Dict[str, str]]) -> str:
    """
    Constructs a prompt based on the user's query, history, and available data context,
    and returns the AI's response using the openai client.
    """
    
    # 1. Format the context data
    context_str = "Data Context (Cross-Referenced):\n\n"
    
    def _inject_df(key: str, max_rows: int):
        if key in data_context and data_context[key] is not None and not data_context[key].empty:
            df = data_context[key]
            return f"- {key.capitalize()}: {len(df)} total. Top {min(max_rows, len(df))}:\n" + df.head(max_rows).to_string(index=False) + "\n\n"
        return ""

    context_str += _inject_df('projects', _MAX_PROJECTS)
    context_str += _inject_df('budget', 200)
    context_str += _inject_df('issues', _MAX_ISSUES)
    context_str += _inject_df('resources', _MAX_RESOURCES)
    context_str += _inject_df('monthly_utilization', 60)
    context_str += _inject_df('cost_rates', 30)
    context_str += _inject_df('risks', _MAX_RISKS)
    context_str += _inject_df('defects', _MAX_DEFECTS)
    context_str += _inject_df('requirements', _MAX_REQS)
    
    if 'traceability_insights' in data_context and data_context['traceability_insights'] is not None and not data_context['traceability_insights'].empty:
        df = data_context['traceability_insights']
        context_str += f"- Traceability_Insights: {len(df)} total. Top {_MAX_REQS}:\n" + df.head(_MAX_REQS).to_string(index=False) + "\n\n"

    # 2. Build the full prompt including history
    prompt = _SYSTEM_PROMPT + "\n\n" + context_str + "\n\nConversation History:\n"
    
    for msg in history:
        role = "User" if msg['role'] == 'user' else "AI"
        prompt += f"{role}: {msg['content']}\n"
        
    prompt += f"\nUser: {query}\nAI:"
    
    try:
        response = get_completion(prompt, max_tokens=800)
        if not response:
            return "I'm sorry, I couldn't generate a response. Please check your API configuration."
        return response
    except Exception as e:
        logger.error(f"Error in ai_service.chat: {e}")
        return f"An error occurred while communicating with the AI service: {e}"
