# KPI & Project Tracking Agent

## Overview

This is a comprehensive KPI and project tracking agent for engineering development programs. The agent monitors project health, analyzes engineering metrics, and provides executive-level insights for program management and steering committees.

## Quick Start

### Using the Agent

The agent instructions are defined in `.instructions.md`. The agent will:

1. **Monitor project portfolios** across programs, releases, and products
2. **Generate KPI dashboards** for executive, engineering, ASPICE, safety, and cybersecurity metrics
3. **Track schedules** with traffic-light health indicators
4. **Manage resources** and predict bottlenecks
5. **Identify and analyze risks** with exposure scoring
6. **Provide predictive insights** on schedule slippage and delivery confidence
7. **Generate professional reports** for weekly, monthly, and steering committee reviews

### Input Data

Place your project data in the `data/` directory. Supported formats:

* **Codebeamer** - Project exports, metrics exports
* **Jira** - Project boards, issue exports, custom metrics
* **Polarion** - Test management, requirements data
* **Azure DevOps** - Work items, burndown data
* **DOORS** - Requirements data
* **Excel/CSV** - Project plans, resource allocation, budgets
* **Power BI** - Dashboard exports

### Workflow

```
data/          → Place source data here
    ├── projects/
    ├── risks/
    ├── resources/
    └── metrics/

src/           → Add processing scripts here (optional)

templates/     → Store report templates here
```

## Agent Capabilities

### 1. Executive KPIs
- Portfolio Health Index
- On-Time Delivery %
- Budget Utilization %
- Risk & Escalation Status

### 2. Engineering KPIs
- Requirements coverage and volatility
- Test execution progress
- Defect metrics and aging
- Verification & validation progress

### 3. ASPICE Compliance
- Process compliance scoring
- Work product completion tracking
- Assessment readiness

### 4. Functional Safety & Cybersecurity
- Safety requirements and test coverage
- ASIL compliance
- Security findings and exposure

### 5. Advanced Analytics
- Schedule variance analysis (Planned vs Actual)
- Resource utilization and bottleneck prediction
- Risk exposure scoring (Impact × Probability)
- Trend analysis and predictive insights

### 6. Professional Reporting
- Weekly Status Reports
- Monthly Executive Reports
- Steering Committee Dashboards
- Actionable recommendations with owner assignments

## Output Structure

All agent responses include:

```
Executive Summary
├── KPI Dashboard
├── Project Health Status
├── Schedule Analysis
├── Quality Analysis
├── Resource Analysis
├── Risk Analysis
├── Predictive Insights
├── Recommendations
└── Action Items
```

## How to Query the Agent

### Simple Status Check
> "What is the current health of Project X?"

### KPI Dashboard
> "Generate a KPI dashboard for the Q3 2026 portfolio"

### Risk Analysis
> "Analyze critical risks for the Turbo Compressor program"

### Predictive Insights
> "Predict schedule slippage for Program Y based on current trends"

### Executive Report
> "Generate a steering committee report for the next board meeting"

### Resource Planning
> "Identify resource bottlenecks and hiring needs for the next quarter"

## Data Requirements

For optimal agent performance, provide:

| Data | Format | Frequency |
|------|--------|-----------|
| Project Schedules | Baseline + Current | Weekly |
| Defect Metrics | Count by severity | Weekly |
| Test Execution | Pass/Fail/Blocked | Daily |
| Risk Register | Description, Impact, Probability | Weekly |
| Resource Allocation | Team, Hours, Utilization % | Bi-weekly |
| Requirements | Total, Approved, Changed | Weekly |
| Budget | Planned vs Spent | Monthly |

## Configuration

The agent is configured via `.instructions.md`. To customize:

1. Modify KPI weights in Project Health Scoring section
2. Adjust thresholds for traffic-light indicators
3. Update supported data sources as needed
4. Customize output format for specific governance requirements

## Support for Multiple Platforms

The agent integrates with:

- **Codebeamer** - Native KPI queries and exports
- **Jira** - Custom JQL queries and metrics
- **Polarion** - Test metrics and traceability
- **Azure DevOps** - Work item dashboards
- **Manual Data** - Excel/CSV uploads for ad-hoc programs

## Best Practices

✅ **DO:**
- Provide consistent data naming conventions
- Update risk/issue registers weekly
- Include baseline and current schedules for variance analysis
- Specify confidence levels for predictions
- Use consistent date formats (YYYY-MM-DD)

❌ **AVOID:**
- Mixing data sources without reconciliation
- Stale data (older than 2 weeks)
- Incomplete risk severity assessments
- Ambiguous project naming

## Examples

### Example 1: Portfolio Health Dashboard
```
Query: "Generate a portfolio health dashboard for all active programs"

Response:
- Executive Summary (30-second overview)
- KPI Heatmap (25+ KPIs across 5 programs)
- Traffic Light Status (Green/Yellow/Red)
- Critical Issues (3 items requiring immediate attention)
- Recommendations (Root cause + corrective actions)
```

### Example 2: Risk Analysis with Recommendations
```
Query: "Analyze turbo design risks for Q3 2026"

Response:
- Open Risks (12 identified, 3 critical)
- Risk Exposure Scoring (calculated per risk)
- Aging Analysis (risks pending 30+ days)
- Recommended Actions (by priority and owner)
- Mitigation Timeline
```

## Next Steps

1. Place your project data in the `data/` directory
2. Ask the agent for a portfolio health check
3. Review recommendations and assign action items
4. Use weekly/monthly reports for governance meetings
5. Leverage predictive insights for proactive program management

---

## Setup & Run (Local Development)

Follow these steps to create a Python virtual environment, install dependencies, and run the dashboard locally.

1. Create a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\pip.exe install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
```

Or on macOS / Linux (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure secrets and API keys:

- Create a `.env` file in the workspace root with your OpenAI key (already supported):

```text
OPENAI_API_KEY=sk-...
```

- If you want email notifications, configure SMTP in `integrations/config.yaml` or set the corresponding environment variables:

```yaml
email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender_email: "kpi@company.com"
    sender_password: "YOUR_APP_PASSWORD"
    daily_report_recipients:
        - "manager@company.com"
```

3. Run the Streamlit dashboard:

```bash
streamlit run web_app.py
```

4. Run a one-off integration sync (for testing):

```bash
# from workspace root
python -m integrations.scheduler --once
```

5. Notes:
- PDF export requires `reportlab` (included in `requirements.txt`). If `reportlab` is not installed, the download will be a plain-text fallback.
- Keep secrets out of source control — `.env` is included in `.gitignore`.
- On Windows, prefer PowerShell when running the included VS Code task.


**KPI Hub PMO Agent** — Enabling data-driven project decisions.
