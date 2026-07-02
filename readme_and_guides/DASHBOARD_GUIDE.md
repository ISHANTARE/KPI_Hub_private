# 🚀 KPI Hub Web Dashboard - User Guide

## Overview
The KPI Hub is an enterprise-grade multi-page Streamlit web dashboard. It features role-based access control, a unified SQL operational database layer, automatic CSV-to-DB synchronization, and predictive AI insights tailored for automotive and engineering program management.

---

## 🔐 Authentication & Roles

The system secures access with a Bcrypt-hashed user authentication gate.

- **Manager Role**: Has full read/write access to all portfolio pages, data editors, database upload utilities (Page 7), and external system integrations (Page 6).
- **Viewer Role**: Read-only access restricted to specific assigned projects (defined in `config/users.yaml`); budget details and admin configuration screens are hidden.

---

## 📈 Multi-Page Dashboard Directory

### Page 1: Portfolio Overview
- **Key Metrics**: Portfolio Health Index (calculated from combined project indexes), On-Time Delivery %, Quality Score, and Action Closure Rate.
- **Charts**:
  - **Portfolio Maturity Scores**: Base maturity against target ASIL compliance levels.
  - **EVM Comparison**: Planned Value (PV) vs Earned Value (EV) vs Actual Cost (AC) grouped bar charts.
- **Alerts**: Real-time alerts for budget variance limits, HIL testing blockages, and milestone slippage.

### Page 2: Project Health
- **Scope**: Drill down into specific engineering projects.
- **Widgets**:
  - **Milestone Timelines**: Current status of target dates and schedule variance.
  - **ECR Status**: Engineering Change Requests pending vs completed.
  - **Risk Exposure**: Heatmaps displaying risk impact vs probability.

### Page 3: Dev Operations
- **Overview**: Monitors Git commit metrics, pull request cycle times, and automated build failures.
- **Integrations**: Displays details synced directly from enterprise developer spaces (e.g. GitHub/GitLab).

### Page 4: Testing & Quality
- **Focus**: Displays verification and validation activity metrics.
- **Features**: Traceability matrices mapping system requirements (SYS.1-SYS.3) to test cases (SWE.1-SWE.6), showing orphan counts and phase mismatches.

### Page 5: Resource Utilization
- **Workload Management**: Displays monthly allocation of engineering roles (FTE) across active projects.
- **Rebalancing recommendations**: AI-assisted reallocation recommendations to resolve team bottlenecks.

### Page 6: System Integrations (Manager Only)
- **Features**: Edit and sync configurations for Jira, Codebeamer, GitHub, Email, Teams, SAP, and Outlook.
- **Operations**: Trigger on-demand syncs ("Pull Data") or run connection health tests ("Test Auth").

### Page 7: Data Upload (Manager Only)
- **Features**: Drag-and-drop CSV uploader to update system datasets.
- **Sync**: Uploading files triggers automatic database refresh (`sync_all_csvs_to_db(force=True)`).

### Page 8: AI Insights
- **Function**: Explores the compiled document index and queries automotive standards (ASPICE v3.1, ISO 26262 ASIL ratings) using the RAG model.

### Page 9: Scenario Simulation
- **Function**: Predicts budget and schedule impacts by tweaking project variables (such as FTE counts or safety compliance requirements).
