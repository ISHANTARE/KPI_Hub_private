"""
KPI Hub Integrations Module
Provides automated data synchronization from core ALM and messaging tools to KPI Hub.

Active Connectors:
- Jira
- Codebeamer
- Email (SMTP/IMAP)
- Microsoft Teams Webhook
- GitHub
- Slack
- Outlook Calendar
"""

from .codebeamer_sync import CodebeamerSync
from .jira_sync import JiraSync
from .scheduler import IntegrationScheduler

__all__ = [
    'CodebeamerSync',
    'JiraSync',
    'IntegrationScheduler'
]
