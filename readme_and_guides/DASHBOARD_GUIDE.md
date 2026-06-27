# 🚀 KPI Hub Web Dashboard - Getting Started

## Overview

The KPI Hub is a **Streamlit-based web dashboard** that displays real-time KPI metrics and visualizations for engineering programs.

**Similar to the image you provided**, the dashboard includes:
- ✅ Overall Maturity & Release Readiness metrics
- ✅ Domain Scores (bar charts)
- ✅ Risk Distribution (donut chart)
- ✅ Project Health Status breakdown
- ✅ Readiness breakdown with base maturity + penalties
- ✅ Sidebar navigation menu
- ✅ Multiple analysis views

---

## Installation & Setup

### Option 1: Quick Start (Windows)
```bash
# Double-click this file:
run_app.bat

# OR run from terminal:
python -m pip install -r requirements.txt
streamlit run web_app.py
```

### Option 2: Manual Setup (All Platforms)

**Step 1: Install Python packages**
```bash
pip install -r requirements.txt
```

**Step 2: Run the application**
```bash
streamlit run web_app.py
```

**Step 3: Open browser**
- Automatically opens at `http://localhost:8501`
- Or manually open in your browser

---

## Dashboard Features

### 📊 Main Dashboard Tab

**Top Metrics:**
```
┌─────────────────┬──────────────────┬──────────────┬──────────────┬─────────────┐
│ Overall         │ Release          │ Active       │ Critical     │ Test Pass   │
│ Maturity        │ Readiness        │ Components   │ Risks        │ Rate        │
│ 80.6%           │ 44.0%            │ 20           │ 0            │ 72%         │
└─────────────────┴──────────────────┴──────────────┴──────────────┴─────────────┘
```

**Visualizations:**
1. **Domain Scores** - Shows health of B-Release, K-Release, Quality
2. **Risk Distribution** - Pie chart: Critical, High, Medium, Low
3. **Project Health Status** - Bar chart: Excellent, Healthy, Watchlist, Critical
4. **Readiness Breakdown** - Base Maturity (85.2%) + Risk Penalty (-8.5%)

**Quick Summary Cards:**
- 🔴 Critical Risks (top 3)
- ⚠️ Open Issues (count & top 3)
- 📊 Resource Utilization (overallocated & average %)

---

### 📈 Other Navigation Options

| Tab | Description |
|-----|-------------|
| 🏠 Dashboard | Main KPI overview (you are here) |
| 📈 KPI Analysis | Detailed breakdown by project |
| 🔧 Components | System component tracking |
| 📋 ECRs | Engineering Change Requests |
| ⚠️ Risks | Full risk register with severity |
| 📊 Trends | Trend analysis over time |
| ✅ Actions | Open issues & escalations |
| 📤 Upload | Upload new data files |
| 🔍 Audit | System audit trail |
| 💡 Insights | AI-powered recommendations |

---

## What Gets Displayed

### Data Source
The dashboard automatically loads data from:
```
data/
├── projects/projects_status.csv
├── projects/milestones.csv
├── projects/budget_tracking.csv
├── projects/issues.csv
├── projects/escalations.csv
├── risks/risk_register.csv
├── resources/resource_allocation.csv
└── metrics/
    ├── defects.csv
    ├── test_execution.csv
    ├── requirements.csv
    └── ... (other metrics)
```

### KPI Calculations
The app calculates metrics from your data:
- **Portfolio Health:** Average of all project health scores
- **Release Readiness:** (Health × Test Pass Rate) / 100
- **On-Time Delivery %:** % of projects on GREEN schedule
- **Test Pass Rate:** % of tests with PASSED status
- **Critical Risks:** Count of risks with CRITICAL severity

---

## Customization

### Change Colors
Edit in `web_app.py`:
```python
# Domain Scores colors:
marker_color=['#6366f1', '#06b6d4', '#10b981']  # Indigo, Cyan, Green

# Risk colors:
colors = {'CRITICAL': '#dc3545', 'HIGH': '#fd7e14', ...}
```

### Modify KPI Formulas
Edit `calculate_kpis()` function in `web_app.py`:
```python
def calculate_kpis(data):
    # Edit these calculations:
    portfolio_health = projects['HEALTH_SCORE'].mean()
    on_time = len(projects[...]) / len(projects) * 100
```

### Add New Charts
Streamlit + Plotly make it easy:
```python
import plotly.graph_objects as go
fig = go.Figure(data=[go.Bar(...)])
st.plotly_chart(fig, use_container_width=True)
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Port 8501 already in use"
**Solution:**
```bash
streamlit run web_app.py --server.port 8502
```

### Issue: Data files not loading
**Check:**
1. CSV files are in `data/` folder
2. File names match exactly (case-sensitive on Linux/Mac)
3. CSV format is correct (first row is headers)

**Fix:**
```bash
# Check data folder
ls -la data/projects/
ls -la data/metrics/
```

### Issue: Charts not displaying
**Solution:**
- Ensure Plotly is installed: `pip install plotly`
- Clear browser cache: Ctrl+Shift+Delete
- Restart Streamlit: Stop and run again

---

## Performance & Optimization

### Caching (Already Implemented)
```python
@st.cache_data
def load_data():
    # Data is cached - only loads once
```

### For Large Datasets
1. Filter data in views (e.g., only show last 100 rows)
2. Use Streamlit session state for user selections
3. Consider pagination for large tables

### Monitor Performance
- Check browser console (F12)
- Look at terminal output for errors
- Use `st.write(st.session_state)` to debug

---

## Deployment Options

### 1. Streamlit Cloud (Free, Easy)
```bash
# Push to GitHub, then:
# Go to https://share.streamlit.io/
# Connect GitHub repo
# Done!
```

### 2. Local Network
```bash
streamlit run web_app.py --server.address 0.0.0.0
# Access from: http://<your-ip>:8501
```

### 3. Docker (Production)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "web_app.py"]
```

### 4. Cloud Providers
- **AWS:** EC2 with Streamlit
- **Heroku:** Container deployment
- **Google Cloud:** Cloud Run
- **Azure:** Container Instances

---

## Workflow

### Daily Use
1. Run `run_app.bat` (Windows) or `bash run_app.sh` (Mac/Linux)
2. Dashboard opens at localhost:8501
3. Review KPIs and metrics
4. Navigate to specific tabs for details
5. Export data if needed
6. Press Ctrl+C to stop

### Weekly Updates
1. Update CSV files in `data/` folder
2. Run app again (data auto-reloads)
3. Generate reports
4. Share dashboard URL with team

### Data Integration
- **Codebeamer Export** → Copy to `data/metrics/`
- **Jira Export** → Copy to `data/projects/`
- **Excel/CSV** → Save to appropriate folder
- Refresh page to see updates

---

## File Structure

```
KPI_Hub_Project/
├── web_app.py                    [Main Streamlit application]
├── requirements.txt              [Python dependencies]
├── run_app.bat                   [Windows startup script]
├── run_app.sh                    [Mac/Linux startup script]
├── RUN_WEB_APP.md               [This file]
├── .streamlit/config.toml        [Streamlit configuration]
└── data/                         [CSV data files]
    ├── projects/
    ├── metrics/
    ├── risks/
    └── resources/
```

---

## Support & Help

### Documentation
- Streamlit Docs: https://docs.streamlit.io
- Plotly Docs: https://plotly.com/python
- Pandas Docs: https://pandas.pydata.org

### Common Issues
- **Data not loading:** Check file paths in `load_data()` function
- **Charts not rendering:** Install `pip install plotly`
- **Performance slow:** Reduce data size or use filtering

### Debugging
```python
# Add to web_app.py to see data:
st.write(data)
st.write(kpis)
```

---

## Next Steps

1. ✅ Run the app: `run_app.bat` or `streamlit run web_app.py`
2. ✅ Explore all dashboard tabs
3. ✅ Customize colors & metrics to your needs
4. ✅ Replace sample data with real project data
5. ✅ Deploy to cloud (optional)
6. ✅ Share dashboard URL with your team

---

## Tips & Tricks

### Keyboard Shortcuts
- **R** - Rerun app
- **C** - Clear cache
- **F** - Focus mode
- **S** - Toggle sidebar

### Streamlit Magic
- Use `st.write()` to display anything
- Use `st.metric()` for KPI cards
- Use `st.plotly_chart()` for interactive charts
- Use `st.dataframe()` for tables

### Performance
- Use `@st.cache_data` for expensive operations
- Avoid loading full datasets in every view
- Use column filtering when possible

---

**Status:** ✅ Ready to Launch  
**Version:** 1.0  
**Last Updated:** May 30, 2026

**Happy Dashboarding! 🎉**
