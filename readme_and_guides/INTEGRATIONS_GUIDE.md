# KPI Hub — Integration & Connector Guide

## Overview

KPI Hub supports automated data synchronization from enterprise ALM and messaging tools into runtime CSV files and the operational SQLite database (`data/kpihub.db`). Configured connectors sync data directly into the platform to update real-time KPI metrics.

---

## Operational Connectors

### 1. Codebeamer ALM 🟢
- **Modules Synced**: Requirements, Test Execution, Defects, Design Reviews, ASPICE Status.
- **Implementation**: [integrations/codebeamer_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/codebeamer_sync.py)
- **Configuration**: Set URL and API token in `integrations/config.yaml` or set environment variables `CODEBEAMER_URL` and `CODEBEAMER_TOKEN`.

### 2. Atlassian Jira 🟢
- **Modules Synced**: Issues, Sprints, Epics, Change Requests.
- **Implementation**: [integrations/jira_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/jira_sync.py)
- **Configuration**: Set URL, Username, and API Token in `integrations/config.yaml` or environment variables `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`.

### 3. Email Alerts (SMTP / IMAP) 🟢
- **Modules Synced**: Daily executive digests and escalation notifications.
- **Implementation**: [integrations/email_notify.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/email_notify.py)
- **Configuration**: Set SMTP server and credentials in `integrations/config.yaml`.

### 4. Microsoft Teams Webhook 🟢
- **Modules Synced**: Instant channel alerts, milestone warnings, and risk escalations.
- **Implementation**: [integrations/teams_notify.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/teams_notify.py)
- **Configuration**: Configure webhook URL in `integrations/config.yaml`.

---

## Enterprise Connectors (Scaffolding Ready)

The platform includes modular scaffolding templates ready for team wiring:

- **GitHub / GitLab**: Commit frequency, PR cycle time, code review velocity ([integrations/github_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/github_sync.py))
- **Slack**: Incident alerts and channel notifications ([integrations/slack_notify.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/slack_notify.py))
- **Outlook Calendar**: Milestone deadline sync ([integrations/outlook_calendar_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/outlook_calendar_sync.py))

---

## Running the Automated Scheduler

To run continuous background synchronization across all configured connectors:

```powershell
python -m integrations.scheduler
```

To execute a single sync pass for testing:

```powershell
python -m integrations.scheduler --once
```
