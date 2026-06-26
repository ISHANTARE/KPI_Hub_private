# KPI Hub - Integration Guide

## Overview

The KPI Hub supports automated data synchronization from multiple project management and test management tools. Instead of manually updating CSV files, your data is automatically synced from your existing tools.

---

## 🎯 Integration Options

### **1. CODEBEAMER** ✅ (Recommended for Requirements & Test Management)

**What it syncs:**
- Requirements tracking
- Test case execution results
- Defects/issues
- Design reviews
- Risk register
- ASPICE compliance data

**Setup Steps:**

1. **Get API Token from Codebeamer:**
   - Go to: Administration → API Access → Create Token
   - Copy the token

2. **Configure in `integrations/config.yaml`:**
   ```yaml
   codebeamer:
     enabled: true
     url: "https://your-codebeamer-instance.com"
     api_token: "YOUR_API_TOKEN_HERE"
     
     projects:
       - codebeamer_id: "P001"
         kpi_project_id: "P001"
         name: "TurboCharger V5"
     
     sync_interval: 60  # Minutes
     
     sync_options:
       requirements: true
       defects: true
       test_cases: true
       design_reviews: true
   ```

3. **Start Automatic Sync:**
   ```bash
   python integrations/scheduler.py
   ```

**Data Mapping:**
| Codebeamer | KPI Hub | File |
|-----------|---------|------|
| Requirements | REQUIREMENT_ID, STATUS | requirements.csv |
| Test Cases | TEST_ID, TEST_CASE_NAME, STATUS | test_execution.csv |
| Defects | DEFECT_ID, SEVERITY, STATUS | defects.csv |
| Design Reviews | DESIGN_REVIEW_ID, OPEN_ACTIONS | design_reviews.csv |

---

### **2. JIRA** ✅ (Recommended for Issues & Tracking)

**What it syncs:**
- Issues/tickets
- Sprints and sprint metrics
- Epics
- Custom fields
- Issue history and transitions

**Setup Steps:**

1. **Get API Token from Jira:**
   - Go to: Profile → Security → Create API Token
   - Copy the token

2. **Configure in `integrations/config.yaml`:**
   ```yaml
   jira:
     enabled: true
     url: "https://your-jira-instance.com"
     username: "your_email@company.com"
     api_token: "YOUR_API_TOKEN_HERE"
     
     projects:
       - jira_key: "PRJ"
         kpi_project_id: "P001"
         jql_query: "project = PRJ AND status in (Open, 'In Progress')"
     
     sync_interval: 60  # Minutes
     
     sync_options:
       issues: true
       sprints: true
       epics: true
   ```

3. **Start Automatic Sync:**
   ```bash
   python integrations/scheduler.py
   ```

**Data Mapping:**
| Jira | KPI Hub | File |
|------|---------|------|
| Issues | ISSUE_ID, STATUS, SEVERITY | issues.csv |
| Sprints | SPRINT_NAME, STATUS, COMPLETION_PCT | milestones.csv |
| Epics | EPIC_ID, EPIC_NAME | escalations.csv |

**Advanced: Custom JQL Queries**
```yaml
jql_query: "project = PRJ AND type = Bug AND priority = Critical AND created >= -7d"
```

---

### **3. AZURE DEVOPS**

**What it syncs:**
- Work items
- Test results
- Build/Release pipelines
- Burndown data

**Setup Steps:**

1. **Generate Personal Access Token (PAT):**
   - User Settings → Personal access tokens → New Token
   - Required scopes: Work Item Read, Test Result Read

2. **Configure in `integrations/config.yaml`:**
   ```yaml
   azure_devops:
     enabled: true
     organization: "your_org"
     project: "Your Project"
     pat_token: "YOUR_PAT_TOKEN"
     
     sync_interval: 60
     
     sync_options:
       work_items: true
       test_results: true
       pipelines: true
   ```

3. **Install dependency:**
   ```bash
   pip install azure-devops
   ```

---

### **4. MONDAY.COM**

**What it syncs:**
- Project board status
- Task completion
- Team assignments
- Timeline tracking

**Setup Steps:**

1. **Get API Key:**
   - Admin → Integrations → Monday API → Get your API Key

2. **Configure in `integrations/config.yaml`:**
   ```yaml
   monday_com:
     enabled: true
     api_key: "YOUR_API_KEY_HERE"
     
     boards:
       - board_id: 12345
         kpi_project_id: "P001"
   ```

---

### **5. ASANA**

**What it syncs:**
- Tasks and projects
- Milestones
- Portfolio data
- Team assignments

**Setup Steps:**

1. **Get Personal Access Token:**
   - Account Settings → Apps and integrations → Create Token

2. **Configure in `integrations/config.yaml`:**
   ```yaml
   asana:
     enabled: true
     personal_access_token: "YOUR_PAT_HERE"
     
     projects:
       - project_id: "1234567890"
         kpi_project_id: "P001"
   ```

---

## 🔔 Notification Integrations

### **SLACK** - Real-time Alerts

Get instant notifications in Slack for critical events:
- 🔴 Critical risks detected
- 📊 Schedule changes
- 💰 Budget overruns
- ❌ Test failures

**Setup:**

1. **Create Webhook:**
   - Slack App → Incoming Webhooks → Create New Webhook
   - Copy the webhook URL

2. **Configure:**
   ```yaml
   slack:
     enabled: true
     webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
     
     notifications:
       critical_risks: true
       schedule_changes: true
       budget_overrun: true
       test_failures: true
   ```

### **EMAIL** - Daily Reports

Receive daily KPI reports via email:

1. **Configure Email Settings:**
   ```yaml
   email:
     enabled: true
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "kpi@company.com"
     sender_password: "YOUR_PASSWORD_HERE"
     
     daily_report_recipients:
       - "manager@company.com"
       - "team@company.com"
   ```

2. **Gmail Setup (if using Gmail):**
   - Enable 2FA on Google Account
   - Generate App Password
   - Use the app password as `sender_password`

---

## 🚀 Running Integrations

### **Option 1: Continuous Background Sync**
```bash
# Starts scheduler that syncs based on configured intervals
python integrations/scheduler.py

# Output:
# KPI Hub Integration Scheduler started
# Codebeamer sync ✓ SUCCESS (2.34s)
# Jira sync ✓ SUCCESS (1.87s)
```

### **Option 2: Single Sync (Testing)**
```bash
# Run one sync cycle without continuous scheduling
python integrations/scheduler.py --once

# Output:
# Running single sync cycle...
# Codebeamer sync ✓ SUCCESS (2.34s)
# Jira sync ✓ SUCCESS (1.87s)
# Single sync cycle complete
```

### **Option 3: From Dashboard**
Add a button in Streamlit to trigger manual sync:
```python
if st.sidebar.button("🔄 Sync Now"):
    with st.spinner("Syncing data..."):
        scheduler = IntegrationScheduler()
        scheduler.run_once()
        st.success("Sync complete!")
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│           External Data Sources                         │
├─────────────────────────────────────────────────────────┤
│  Codebeamer  │  Jira  │  Azure DevOps  │  Monday.com   │
└────────┬──────┬────────┬────────────────┬───────────────┘
         │      │        │                │
         └──────┼────────┼────────────────┘
                ▼
        ┌─────────────────┐
        │  Integration    │
        │   Scheduler     │
        │ (scheduler.py)  │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ .csv     │ │ .csv     │ │ .csv     │
│ Files    │ │ Files    │ │ Files    │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     └────────────┼────────────┘
                  ▼
         ┌─────────────────┐
         │  Web Dashboard  │
         │   (Streamlit)   │
         └─────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
 Charts      KPI Metrics    Reports
```

---

## 🔧 Configuration Reference

### **config.yaml Structure**

```yaml
# Each integration section has:
# - enabled: true/false (enable/disable)
# - url/api_key: Authentication credentials
# - sync_interval: Minutes between syncs (default: 60)
# - sync_options: Which data to sync

# Authentication Priority:
# 1. API Token (if available)
# 2. Username + Password
# 3. Personal Access Token (PAT)
```

---

## 🐛 Troubleshooting

### **Sync Fails - "Connection Refused"**
```
❌ Error: Could not connect to Codebeamer instance
✓ Solution:
  1. Verify URL is correct (include https://)
  2. Check network connectivity
  3. Ensure firewall allows outbound connections
```

### **Authentication Error - "Invalid Token"**
```
❌ Error: Authorization failed
✓ Solution:
  1. Verify API token is not expired
  2. Regenerate token if needed
  3. Check username/password are correct
  4. Ensure account has API access permissions
```

### **Data Not Updating**
```
❌ Issue: CSV files not changing after sync
✓ Solution:
  1. Check scheduler is running: ps aux | grep scheduler
  2. Verify sync_interval (default 60 minutes)
  3. Check logs: tail -f logs/scheduler.log
  4. Run manual sync: python integrations/scheduler.py --once
```

### **Check Sync Logs**
```bash
# View Codebeamer sync logs
tail -f logs/codebeamer_sync.log

# View Jira sync logs
tail -f logs/jira_sync.log

# View scheduler logs
tail -f logs/scheduler.log
```

---

## 📈 Monitoring Integration Health

Check integration status in dashboard:
1. Go to **Dashboard** → **Audit** tab
2. View "Last Sync Time" and "Sync Status"
3. See error count for any failed syncs

---

## 🎓 Examples

### **Example 1: Sync Codebeamer Requirements Every 30 Minutes**
```yaml
codebeamer:
  enabled: true
  url: "https://cb.company.com"
  api_token: "abc123xyz"
  sync_interval: 30
  sync_options:
    requirements: true
    defects: true
```

### **Example 2: Jira + Slack Notifications**
```yaml
jira:
  enabled: true
  sync_interval: 60

slack:
  enabled: true
  notifications:
    critical_risks: true
    test_failures: true
```

### **Example 3: Daily Email Report with Codebeamer Sync**
```yaml
codebeamer:
  enabled: true
  sync_interval: 60

email:
  enabled: true
  daily_report_recipients:
    - "team@company.com"
```

---

## 📞 Support

For integration issues:
1. Check logs in `logs/` directory
2. Run `python integrations/scheduler.py --once` for single sync
3. Verify credentials in `integrations/config.yaml`
4. Test API connectivity from command line

---

## 🔐 Security Best Practices

1. **Never commit API tokens to Git:**
   ```bash
   # Add to .gitignore
   integrations/config.yaml
   ```

2. **Use environment variables:**
   ```yaml
   codebeamer:
     api_token: ${CODEBEAMER_TOKEN}
   ```

You can also set environment variables directly (recommended for CI/servers):

```powershell
# Windows (PowerShell)
$env:CODEBEAMER_URL = "https://cb.company.com"
$env:CODEBEAMER_TOKEN = "abc123xyz"
$env:JIRA_URL = "https://your-jira-instance.com"
$env:JIRA_USERNAME = "your_email@company.com"
$env:JIRA_API_TOKEN = "your_jira_token"

# macOS / Linux (bash)
export CODEBEAMER_URL="https://cb.company.com"
export CODEBEAMER_TOKEN="abc123xyz"
export JIRA_URL="https://your-jira-instance.com"
export JIRA_USERNAME="your_email@company.com"
export JIRA_API_TOKEN="your_jira_token"
```

3. **Rotate tokens regularly** (recommended: every 90 days)

4. **Use restricted scopes** for API tokens:
   - Only grant required permissions
   - Disable unused integrations

---

## Next Steps

1. **Choose your primary integration** (Codebeamer or Jira)
2. **Get API credentials** from your tool
3. **Update `integrations/config.yaml`**
4. **Run `python integrations/scheduler.py`**
5. **Monitor logs** to verify sync is working
6. **Enable notifications** (Slack/Email)

Your dashboard will now automatically update with the latest project data! 🎉

---

## 🧠 OpenAI Integration Example

You can use an OpenAI API key from your `.env` to call the API from the app.

Example Python usage (uses `integrations/openai_client.py`):

```python
from integrations.openai_client import get_completion

prompt = "Summarize the recent changes to the project in one paragraph."
result = get_completion(prompt)
print(result)
```

Notes:
- Ensure `OPENAI_API_KEY` is set in `.env` or environment.
- The helper tries the `openai` package first, then falls back to an HTTP call if needed.
