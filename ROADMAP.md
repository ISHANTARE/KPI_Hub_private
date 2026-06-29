# KPI Hub — Platform Integration & Architecture Overview

This document outlines the current active integration connectors, architectural layers, and operational status of KPI Hub.

---

## Active & Operational Connectors

| Connector | Status | Purpose | Implementation File |
|-----------|--------|---------|---------------------|
| **Jira** | 🟢 Operational | Issue, Epic, Sprint, and Ticket synchronization | [integrations/jira_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/jira_sync.py) |
| **Codebeamer** | 🟢 Operational | Automotive ALM requirements, design reviews, and test cases | [integrations/codebeamer_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/codebeamer_sync.py) |
| **Email (SMTP/IMAP)** | 🟢 Operational | Daily digest reports, escalation alerts, and automated notifications | [integrations/email_notify.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/email_notify.py) |
| **Microsoft Teams** | 🟢 Operational | Webhook alerts, channel cards, and instant team notifications | [integrations/teams_notify.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/teams_notify.py) |

---

## Enterprise Connectors (Scaffolding-Ready Templates)

The following modules provide ready-to-wire scaffold templates for enterprise expansion:

- ⚡ **GitHub / GitLab**: Commit tracking, PR cycle times, and velocity metrics ([integrations/github_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/github_sync.py))
- ⚡ **Slack**: Real-time channel notifications and webhooks ([integrations/slack_notify.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/slack_notify.py))
- ⚡ **Outlook Calendar**: Milestone deadline synchronization and event tracking ([integrations/outlook_calendar_sync.py](file:///c:/Users/Admin/VIT_Projects/KPI_Hub_private/integrations/outlook_calendar_sync.py))

---

## Platform Architecture Features

- 🗄️ **SQLite Data Layer (`data/kpihub.db`)**: Operational SQLite database with force synchronization (`sync_all_csvs_to_db`) from runtime CSV files.
- ⚙️ **Unified KPI Engine (`lib/kpi_engine.py`)**: Centralized computation engine for Release Readiness, Quality Scores, and Cross-System Penalty Algorithms.
- 🚀 **FastAPI Sidecar (`api/main.py`)**: Programmatic REST endpoints for project summaries and `/health` DB ping verification.
- 🧠 **Dynamic Automotive RAG (`lib/knowledge_base.py`)**: Real-time search engine covering ASPICE standards and ISO 26262 functional safety guidelines.
