# KPI Hub — Engineering PMO & Automotive Tracking Platform

## Overview

**KPI Hub** is an industry-grade engineering PMO and project tracking platform designed for automotive and hardware engineering programs. Built on top of Python, Streamlit, and FastAPI, KPI Hub monitors project health, calculates ASPICE & ISO 26262 compliance metrics, evaluates cross-system penalties, and delivers AI-powered executive insights for steering committees.

---

## Architecture & Core Components

```
KPI Hub Platform Architecture
├── data/                    → CSV Datasets & SQLite Operational DB (kpihub.db)
├── lib/                     → Core Analytical Engines & Data Loaders
│   ├── kpi_engine.py        → Unified KPI & Cross-System Penalty Calculation
│   ├── data_loader.py       → 24-Key Data Contract & CSV/DB Loading
│   ├── database.py          → SQLite SQLAlchemy Sync Layer (sync_all_csvs_to_db)
│   ├── knowledge_base.py    → Dynamic Automotive Standards Search (ASPICE / ISO 26262)
│   ├── ai_engine.py         → Predictive Trend & Hotspot Analysis
│   └── styling.py           → Modern UI Design System Tokens
├── pages/                   → Multi-Page Streamlit Dashboard UI (Pages 01 to 08)
├── api/                     → FastAPI REST API Sidecar (main.py)
├── integrations/            → ALM Connectors (Jira, Codebeamer, Email, Teams)
└── tests/                   → Pytest Verification Suite (95/95 Tests Passing)
```

---

## Key Features & Capabilities

### 1. Portfolio & Project Health Governance
- **Unified KPI Engine**: Computes Portfolio Health Index, On-Time Delivery %, Quality Score, and Action Closure Rate (60.0%) from a single source of truth.
- **Cross-System Penalty Engine**: Automatically penalizes release readiness based on resource overallocation and traceability gaps.

### 2. Automotive Compliance (ASPICE & ISO 26262)
- **Traceability Intelligence**: Detects stale coverage, phase mismatches, and orphaned test cases across requirements and test execution logs.
- **Dynamic Standards Search**: Real-time query resolution on Page 8 searching ASPICE process areas (SYS.1-3, SWE.1-6) and ASIL safety levels (A-D).

### 3. Resource & Financial Management
- **Resource Rebalancing**: Real-time monthly workload tracking with automated AI bottleneck resolution recommendations.
- **Budget Exhaustion Guards**: Live variance tracking and run-rate calculations.

### 4. Enterprise REST API Sidecar
- Powered by **FastAPI** (`api/main.py`). Provides `/health` with live SQL database ping tests and programmatic JSON endpoints (`/api/v1/projects`, `/api/v1/metrics`).

---

## Getting Started

### 1. Local Setup & Execution

Run the Streamlit Web Dashboard:
```powershell
python -m streamlit run web_app.py
```

Run the FastAPI REST Sidecar:
```powershell
uvicorn api.main:app --reload --port 8000
```

Run Automated Test Verification:
```powershell
python -m pytest
```

---

## Data Management

Place or update project CSV datasets in the `data/` directory. Uploading files via **Page 7 (Data Upload)** automatically triggers SQLite database re-synchronization (`sync_all_csvs_to_db(force=True)`) and updates all dashboard metrics instantly.

---

**KPI Hub Engineering PMO Platform** — Enabling data-driven engineering decisions.
