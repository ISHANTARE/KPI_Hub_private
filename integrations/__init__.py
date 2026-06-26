"""
KPI Hub Integrations Module
Provides automated data synchronization from various project management and 
test management tools to the KPI Hub dashboard.

Supported Integrations:
- Codebeamer - Requirements, test cases, defects
- Jira - Issues, sprints, epics
- Azure DevOps - Work items, test results
- Monday.com - Project board tracking
- Asana - Project management
- Slack - Notifications
- Email - Daily reports

Usage:
    from integrations.scheduler import IntegrationScheduler
    
    # Run continuous sync
    scheduler = IntegrationScheduler()
    scheduler.run()
    
    # Or run single sync
    scheduler.run_once()
"""

from .codebeamer_sync import CodebeamerSync
from .jira_sync import JiraSync
from .scheduler import IntegrationScheduler

__all__ = [
    'CodebeamerSync',
    'JiraSync',
    'IntegrationScheduler'
]
