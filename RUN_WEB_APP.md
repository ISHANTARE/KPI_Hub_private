# How to Run the KPI Hub Web Dashboard

## Quick Start (2 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Web App
```bash
streamlit run web_app.py
```

### Step 3: Open in Browser
The app will automatically open at: `http://localhost:8501`

---

## What You'll See

### Dashboard Tab (Home)
- **Overall Maturity:** 80.6% (Portfolio health score)
- **Release Readiness:** 44.0% (Release readiness metric)
- **Active Components:** 20 (Active projects/components)
- **Critical Risks:** 0 (Critical risk count)
- **Test Pass Rate:** 72% (Quality metric)

### Charts & Visualizations
1. **Domain Scores** - Bar chart showing health by release/domain
2. **Risk Distribution** - Donut chart of risks by severity
3. **Readiness Breakdown** - Base maturity + risk penalty
4. **Project Health Status** - Count of projects by health status

### Navigation Menu (Left Sidebar)
- 🏠 Dashboard - Main KPI overview
- 📈 KPI Analysis - Detailed KPI breakdown
- 🔧 Components - System components
- 📋 ECRs - Engineering Change Requests
- ⚠️ Risks - Risk register and analysis
- 📊 Trends - Trend analysis over time
- ✅ Actions - Action items and issues
- 📤 Upload - Data upload interface
- 🔍 Audit - Audit trail
- 💡 Insights - AI-powered insights

---

## Customization

### Update KPI Calculations
Edit `web_app.py` in the `calculate_kpis()` function to modify metric calculations.

### Change Colors & Styling
Look for the CSS section at the top of `web_app.py` to customize colors and layout.

### Add New Visualizations
Use Plotly (already imported) to add new charts in the respective view sections.

---

## Troubleshooting

### Port Already in Use
```bash
streamlit run web_app.py --server.port 8502
```

### Data Not Loading
Ensure CSV files are in the `data/` folder:
- data/projects/projects_status.csv
- data/risks/risk_register.csv
- data/resources/resource_allocation.csv
- data/metrics/defects.csv
- etc.

### Module Not Found
```bash
pip install streamlit pandas plotly numpy
```

---

## Performance Tips

- First load may take a few seconds to process all CSV files
- Use the `@st.cache_data` decorator (already in code) to cache data
- For large datasets, consider filtering in the view sections

---

## Next Steps

1. Run the app with `streamlit run web_app.py`
2. Explore all navigation tabs
3. Modify colors and styling to match your brand
4. Add real data by replacing CSV files
5. Deploy to cloud (AWS, Heroku, Google Cloud, etc.)

---

## Deployment Options

### Local Network
```bash
streamlit run web_app.py --server.address 0.0.0.0
```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "web_app.py"]
```

### Cloud Deployment
- **Streamlit Cloud:** https://share.streamlit.io/
- **Heroku:** Container deployment
- **AWS:** EC2 + Docker
- **Google Cloud:** Cloud Run

---

**Status:** ✅ Ready to Run
**Version:** 1.0
**Last Updated:** May 30, 2026
