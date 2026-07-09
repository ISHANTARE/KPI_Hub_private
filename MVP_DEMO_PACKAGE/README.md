# KPI Hub MVP Demo - First Review (10-20% Scope)

## 🎯 Quick Start (2 Minutes)

### Step 1: Install Dependencies
```bash
pip install streamlit pandas plotly pydantic fastapi
```

### Step 2: Run the Dashboard
```bash
cd MVP_DEMO_PACKAGE
python -m streamlit run app.py
```

### Step 3: Open Browser
Go to: `http://localhost:8501`

---

## 📊 What's Included in MVP Demo

### Pages (5 Core Dashboards)
1. ✅ **Portfolio Overview** - Executive summary of all projects
2. ✅ **Project Health** - Individual project status & metrics
3. ✅ **Testing & Quality** - Test results & defect tracking
4. ✅ **Resource Utilization** - Team workload & capacity
5. ✅ **API Documentation** - Show REST endpoints

### Features Demonstrated
- 📊 Interactive dashboards with Plotly charts
- 🎨 Clean, professional UI with Streamlit
- 📁 Sample data (pre-loaded CSVs)
- 🔐 Role-based access control (Viewer/Admin)
- 🔌 REST API endpoints showcase
- 📈 Real-time KPI calculations

### Sample Data Included
- 3 projects with varying health scores
- 150+ test cases with pass/fail status
- 50+ defects with severity levels
- 6 team members with utilization metrics
- 3 milestones with completion status

---

## 🗂️ File Structure

```
MVP_DEMO_PACKAGE/
├── app.py                           # Main dashboard entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── data/                            # Sample data (CSVs)
│   ├── projects.csv
│   ├── tests.csv
│   ├── defects.csv
│   ├── resources.csv
│   └── milestones.csv
│
├── lib/                             # Core functionality
│   ├── __init__.py
│   ├── auth.py                      # Login & role-based access
│   ├── kpi_engine.py                # KPI calculations
│   ├── data_loader.py               # Load CSV data
│   └── styling.py                   # UI styling
│
├── pages/                           # Dashboard pages
│   ├── 01_portfolio_overview.py
│   ├── 02_project_health.py
│   ├── 03_testing_quality.py
│   ├── 04_resource_utilization.py
│   └── 05_api_documentation.py
│
└── config.yaml                      # Configuration
```

---

## 🔑 Login Credentials (Demo)

**Admin Account:**
- Username: `admin`
- Password: `demo123`

**Viewer Account:**
- Username: `viewer`
- Password: `demo123`

---

## 📊 Dashboard Overview

### Page 1: Portfolio Overview
- **Portfolio Health Score**: 82/100 (Healthy)
- **On-Time Delivery**: 75%
- **Quality Score**: 88/100
- **Active Projects**: 3
- **Critical Risks**: 1
- Interactive charts showing project distribution

### Page 2: Project Health
- Project 1: EV Battery System (🟢 GREEN - 82/100)
- Project 2: Motor Controller (🟡 YELLOW - 75/100)
- Project 3: Safety Validation (🟢 GREEN - 88/100)
- Individual KPI breakdown per project

### Page 3: Testing & Quality
- Test Pass Rate: 93.3% (140/150 passed)
- Defect Distribution: Critical (3%), High (12%), Medium (52%), Low (33%)
- Defect aging analysis
- Test execution trends

### Page 4: Resource Utilization
- Team member allocation table
- Utilization heatmap (60-120% range)
- Capacity warnings for over-allocated resources
- Monthly utilization trends

### Page 5: API Documentation
- `/health` - Database health check
- `/api/v1/metrics` - Portfolio KPIs
- `/api/v1/projects` - Project list
- Example API calls in Python

---

## 🚀 Demo Flow (For Reviewers)

**Time: ~5 minutes**

1. **(0:00-0:30)** Open app, show login screen
   - Login as `admin` / `demo123`
   
2. **(0:30-1:30)** Navigate to Portfolio Overview
   - Point out: "All projects visible in one place"
   - Highlight: Health scores, KPI cards
   - Show: Interactive chart (click/hover)
   
3. **(1:30-2:30)** Click into Project Health
   - Show: Individual project details
   - Explain: Traffic light status (Green/Yellow/Red)
   - Point out: Metrics breakdown
   
4. **(2:30-3:30)** Go to Testing & Quality
   - Show: Test pass rate (93%)
   - Highlight: Defect severity pie chart
   - Explain: How data updates
   
5. **(3:30-4:30)** Show Resource Utilization
   - Point out: Team workload distribution
   - Highlight: Over-allocation warnings
   - Show: Monthly trends
   
6. **(4:30-5:00)** Quick API overview
   - Show: API documentation page
   - Explain: REST endpoints for integration

---

## 💡 Key Talking Points

✅ **"Centralized Visibility"** - All project data in one dashboard
✅ **"Real-Time Metrics"** - KPIs calculated instantly from CSV uploads
✅ **"Data-Driven"** - Upload data → See insights
✅ **"Scalable Architecture"** - Built for Phase 2 features
✅ **"Enterprise-Ready"** - REST API for integration
✅ **"Security First"** - Role-based access control

---

## 🔮 Phase 2 Features (Coming Later)

- 🤖 AI-powered predictions & anomaly detection
- 🔗 Jira & Codebeamer integrations
- 📧 Email & Teams notifications
- 📈 ASPICE compliance tracking
- 🎯 Safety (ISO 26262) management
- 📊 Advanced forecasting (EVM)
- 🎬 Scenario simulation
- 📱 Mobile-responsive design

---

## 🛠️ Development Notes

### Sample Data
- All data is **realistic** (automotive industry context)
- Data is **diverse** (multiple projects, varying statuses)
- Data is **educational** (shows all KPI types)

### Code Quality
- Clean, modular architecture
- Easy to extend
- Well-commented
- No hard-coded secrets

### Performance
- Data loads in <1 second
- Charts render instantly
- No database required (uses CSV)

---

## ❓ FAQ

**Q: Can I use this with real company data?**
A: Yes! Replace CSV files in `data/` folder with your actual project data.

**Q: Does it need a database?**
A: No. MVP uses CSV files. Phase 2 will add SQLite/PostgreSQL.

**Q: Can I customize the data?**
A: Yes! Edit CSV files or modify `lib/data_loader.py`.

**Q: How do I deploy this?**
A: Use Streamlit Cloud (free tier) or any Python hosting.

---

## 📝 Submission Checklist

- ✅ Runs without errors
- ✅ Shows all 5 dashboard pages
- ✅ Sample data pre-loaded
- ✅ Login screen works
- ✅ Charts are interactive
- ✅ API documentation included
- ✅ README with quick-start guide
- ✅ <5 minute demo time

---

## 📞 Support

For issues or questions:
1. Check the README
2. Review sample data in `data/` folder
3. Check `lib/` for implementation details

---

**Ready to impress your reviewers! 🚀**
