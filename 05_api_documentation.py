"""Page 5: REST API Documentation"""
import streamlit as st

st.title("🔌 REST API Documentation")
st.markdown("Programmatic access to KPI Hub data")
st.divider()

st.info(
    "**REST API** allows other applications and tools to access KPI Hub data programmatically.\n\n"
    "Phase 2 will include a running FastAPI server. For now, this shows available endpoints."
)

st.divider()

st.subheader("📡 Available Endpoints")

# Health endpoint
with st.expander("✅ GET /health", expanded=True):
    st.write("**Description:** Check if API and database are operational")
    st.write("**Response:**")
    st.json({
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected"
    })

# Metrics endpoint
with st.expander("📊 GET /api/v1/metrics"):
    st.write("**Description:** Retrieve portfolio-level KPIs")
    st.write("**Response:**")
    st.json({
        "portfolio_kpis": {
            "portfolio_health": 82.5,
            "on_time_delivery": 75,
            "quality_score": 88,
            "test_pass_rate": 93.3
        },
        "active_projects": 3,
        "critical_risks": 1
    })

# Projects endpoint
with st.expander("📋 GET /api/v1/projects"):
    st.write("**Description:** List all projects with basic info")
    st.write("**Query Parameters:**")
    st.write("- `limit`: Number of projects to return (default: 50, max: 500)")
    st.write("**Response:**")
    st.json([
        {
            "project_id": "P001",
            "project_name": "EV Battery Management System",
            "status": "In Progress",
            "health_score": 82
        },
        {
            "project_id": "P002",
            "project_name": "Motor Controller Unit",
            "status": "Planning",
            "health_score": 75
        }
    ])

# Project details endpoint
with st.expander("🎯 GET /api/v1/projects/{project_id}"):
    st.write("**Description:** Get detailed information for a specific project")
    st.write("**Path Parameters:**")
    st.write("- `project_id`: The project ID (e.g., 'P001')")
    st.write("**Response:**")
    st.json({
        "PROJECT_ID": "P001",
        "PROJECT_NAME": "EV Battery Management System",
        "STATUS": "In Progress",
        "HEALTH_SCORE": 82,
        "SCHEDULE_STATUS": "GREEN",
        "BUDGET_USED_PCT": 65,
        "TEAM_SIZE": 8,
        "START_DATE": "2026-01-15",
        "END_DATE": "2026-12-31"
    })

# EVM endpoint
with st.expander("💰 GET /api/v1/financials/evm"):
    st.write("**Description:** Retrieve Earned Value Management (financial) metrics")
    st.write("**Response:**")
    st.json({
        "portfolio_cpi": 0.98,
        "portfolio_spi": 0.95,
        "estimate_at_completion": 1050000,
        "variance_at_completion": -50000
    })

st.divider()

st.subheader("🐍 Python Example")

st.code(
    """
import requests

# Get portfolio metrics
response = requests.get('http://localhost:8000/api/v1/metrics')
data = response.json()

print(f"Portfolio Health: {data['portfolio_kpis']['portfolio_health']}")
print(f"On-Time Delivery: {data['portfolio_kpis']['on_time_delivery']}%")

# Get specific project
project_response = requests.get('http://localhost:8000/api/v1/projects/P001')
project = project_response.json()

print(f"Project: {project['PROJECT_NAME']}")
print(f"Status: {project['STATUS']}")
    """,
    language="python"
)

st.divider()

st.subheader("🔧 JavaScript / Node.js Example")

st.code(
    """
// Get portfolio metrics
fetch('http://localhost:8000/api/v1/metrics')
  .then(response => response.json())
  .then(data => {
    console.log('Portfolio Health:', data.portfolio_kpis.portfolio_health);
    console.log('On-Time Delivery:', data.portfolio_kpis.on_time_delivery + '%');
  });

// Get all projects
fetch('http://localhost:8000/api/v1/projects?limit=10')
  .then(response => response.json())
  .then(projects => {
    projects.forEach(p => {
      console.log(`${p.project_name}: ${p.health_score}/100`);
    });
  });
    """,
    language="javascript"
)

st.divider()

st.subheader("⚙️ API Features")

features = [
    "✅ RESTful JSON API",
    "✅ No authentication required (MVP demo)",
    "✅ Fast response times (<100ms)",
    "✅ CORS enabled for web applications",
    "✅ Error handling and status codes",
    "✅ Pagination support for large datasets",
    "✅ Rate limiting (Phase 2)",
    "✅ API key authentication (Phase 2)"
]

for feature in features:
    st.write(feature)

st.info(
    "**Phase 2 Enhancements:**\n\n"
    "- Webhook support for real-time notifications\n"
    "- GraphQL API alternative\n"
    "- Advanced filtering & search\n"
    "- Data export (CSV, Excel, PDF)\n"
    "- Integration with monitoring tools"
)
