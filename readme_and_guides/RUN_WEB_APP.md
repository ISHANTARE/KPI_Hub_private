# Running the KPI Hub Platform

This guide provides instructions to run the updated, multi-page, SQLite-backed KPI Hub platform.

---

## ⚡ Quick Start

### 1. Install Dependencies
Make sure you have Python 3.9+ installed, then install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit Dashboard
Launch the main user interface:
```bash
python -m streamlit run web_app.py
```
The application will automatically launch in your browser at `http://localhost:8501`.

### 3. Log In (Bcrypt Secured)
Sign in using the default manager credentials:
- **Username / Email**: `admin@kpihub.local`
- **Password**: `admin123`

---

## 🛠️ Running Platform Services

The modernized platform consists of three core executable layers:

### 1. Streamlit Web Dashboard
- **Command**: `python -m streamlit run web_app.py`
- **Main Page**: Houses the role-based auth gate, then redirects to the 9-page dashboard navigation.
- **Port**: Default `8501`

### 2. FastAPI REST API Sidecar
- **Command**: `uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload`
- **API Documentation**: Access interactive swagger docs at `http://127.0.0.1:8000/docs`.
- **Endpoints**:
  - `/health` - Service health status with SQLite database ping checks.
  - `/api/v1/projects` - Retrieve structured project health and status lists.
  - `/api/v1/metrics` - Fetch real-time quality and compliance KPI metrics.

### 3. Automated Sync Scheduler
- **Command**: `python -m integrations.scheduler`
- **Single Run**: `python -m integrations.scheduler --once`
- **Function**: Automatically synchronizes data from active connectors (Jira, Codebeamer, GitHub, Outlook Calendar, SAP, Slack, Teams, Email) and loads them into runtime CSV files.

---

## 📂 Core Architecture & Customization

- **SQLite Database Layer**: All operational views read data from `data/kpihub.db`. Runtime CSV files in `data/` are automatically synced to the SQLite tables via `lib/database.py` during initialization and data uploads.
- **KPI calculations**: Business logic for EVM forecasting, release readiness, and cross-system compliance penalties is managed in `lib/kpi_engine.py`.
- **Styles & Themes**: Modern UI styling tokens and styling parameters are consolidated in `lib/styling.py` and `lib/styles.css`.
- **Page Configurations**: Pages 1 to 9 are located in the `pages/` directory.

---

## 🧪 Verification & Testing

Verify that your local setup is correct by running the unit test suite:
```bash
python -m pytest
```
*Expected: 110 tests passed successfully.*
