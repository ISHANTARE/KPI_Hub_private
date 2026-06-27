# Sample Data Inventory

## Overview
This directory contains comprehensive sample data for 5 development programs representing various project types and maturity levels.

**Generated:** May 30, 2026
**Data Period:** Q1-Q3 2026

---

## Data Files by Category

### Project Portfolio Data

| File | Records | Format | Purpose |
|------|---------|--------|---------|
| `projects/projects_status.csv` | 5 | CSV | Master project inventory with health scores |
| `projects/milestones.csv` | 25 | CSV | Project milestones and completion tracking |
| `projects/budget_tracking.csv` | 25 | CSV | Financial tracking by project and category |
| `projects/issues.csv` | 12 | CSV | Open issues and blockers |
| `projects/escalations.csv` | 10 | CSV | Management escalations (steering committee) |

**Total Projects:** 5 active
- P001: TurboCharger V5 (Turbo Advanced, Heavy Duty)
- P002: Electric Motor Control (EV Platform)
- P003: Safety Module Redesign (Safety Engineering)
- P004: Legacy System Migration (Platform, Completed)
- P005: Cybersecurity Hardening (Security)

---

### Risk Management

| File | Records | Format | Purpose |
|------|---------|--------|---------|
| `risks/risk_register.csv` | 6 | CSV | Risk identification with exposure scoring |

**Risk Summary:**
- 6 total risks identified
- 3 CRITICAL (Exposure Score 9)
- 3 HIGH (Exposure Score 6)
- Status: 4 OPEN, 1 MITIGATED, 1 CLOSED

---

### Resource Management

| File | Records | Format | Purpose |
|------|---------|--------|---------|
| `resources/resource_allocation.csv` | 10 | CSV | Team allocation and utilization |

**Resource Summary:**
- 10 team members across 5 projects
- 1 OVERALLOCATED (CFD engineers at 119%)
- 6 FULLY ALLOCATED (100%)
- 3 UNDERUTILIZED (<90%)

---

### Engineering Metrics

| File | Records | Format | Purpose |
|-------|---------|--------|---------|
| `metrics/defects.csv` | 15 | CSV | Quality defect tracking (OPEN, FIXED, etc) |
| `metrics/test_execution.csv` | 20 | CSV | Test case execution results |
| `metrics/requirements.csv` | 20 | CSV | Requirements management & traceability |
| `metrics/engineering_kpis.csv` | 18 | CSV | High-level engineering metrics |
| `metrics/design_reviews.csv` | 15 | CSV | Design review tracking |
| `metrics/aspice_status.csv` | 25 | CSV | ASPICE process compliance tracking |
| `metrics/functional_safety_requirements.csv` | 10 | CSV | Safety-critical requirements (ASIL) |
| `metrics/verification_activities.csv` | 15 | CSV | Verification test execution |
| `metrics/validation_activities.csv` | 9 | CSV | Validation and customer acceptance |

---

## Data Quality Metrics

### Completeness
- **Project Coverage:** 100% (5/5 projects have data)
- **Traceability:** 95% (Requirements → Tests → Verification)
- **Milestone Coverage:** 100% (All projects have milestones)
- **Budget Coverage:** 100% (All projects have budget data)

### Data Timeliness
- **Last Updated:** May 30, 2026
- **Time Period:** Q1-Q3 2026 (9 months)
- **Snapshot Date:** May 28, 2026 (2 days old - current)

### Key Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Portfolio Health Score** | **72/100** | WATCHLIST 🟡 |
| **On-Time Delivery %** | 60% | RED 🔴 |
| **Budget Performance** | 5% underspend | GREEN 🟢 |
| **Resource Utilization** | 98.2% | GREEN 🟢 |
| **Critical Risks** | 3 open | RED 🔴 |
| **Open Defects** | 42 | YELLOW 🟡 |
| **Test Pass Rate** | 72% | YELLOW 🟡 |
| **Requirements Coverage** | 92% | GREEN 🟢 |

---

## Project Status Snapshot

### Program Health Overview

| Project | Health | Schedule | Quality | Budget | Risks | Confidence |
|---------|--------|----------|---------|--------|-------|-----------|
| **P001** Turbo V5 | WATCHLIST 68 | 🔴 RED | 🟡 YELLOW | 🟡 YELLOW | 3 | MEDIUM |
| **P002** EV Motor | HEALTHY 82 | 🟢 GREEN | 🟡 YELLOW | 🟢 GREEN | 1 | HIGH |
| **P003** Safety Module | WATCHLIST 71 | 🟡 YELLOW | 🔴 RED | 🟢 GREEN | 2 | MEDIUM |
| **P004** Legacy Migration | CRITICAL 58 | 🔴 RED | 🔴 RED | 🔴 RED | 1 | LOW |
| **P005** Cybersecurity | HEALTHY 79 | 🟢 GREEN | 🟡 YELLOW | 🟢 GREEN | 2 | HIGH |

---

## Critical Items (Steering Committee Focus)

### Top 3 Risks
1. **R001** - Supplier Lead Time Delay (Exposure: 9/9) - P001
2. **R004** - Safety Compliance Gap (Exposure: 9/9) - P003
3. **R002** - Design Review Backlog (Exposure: 6/9) - P001

### Top 3 Escalations
1. **E004** - Safety Engineering Resource Gap (CRITICAL) - P003
2. **E003** - CAN Bus EMI Non-Compliance (CRITICAL) - P002
3. **E001** - Supplier Quality Delivery Miss (HIGH) - P001

### Top 3 Critical Defects
- D001 (P001): Thermal Simulation Mismatch
- D007 (P002): Motor Winding Insulation
- D010 (P003): FMEA Gap

---

## How to Use This Data

### 1. Import into Agent
```
Place all CSV files in data/ folder
Ask agent: "Generate a portfolio health dashboard"
```

### 2. Analyze Specific Program
```
Query: "What is the health of P001 TurboCharger program?"
Returns: Health score, schedule variance, risk analysis, recommendations
```

### 3. Identify Bottlenecks
```
Query: "Identify resource bottlenecks and resource constraints"
Returns: CFD team at 119% allocation, hiring recommendations
```

### 4. Risk Assessment
```
Query: "Analyze critical risks for Q3 2026"
Returns: Risk matrix, exposure scores, mitigation strategies
```

### 5. Generate Reports
```
Query: "Generate a steering committee report"
Returns: Executive dashboard with recommendations
```

---

## Data Dictionary

See `DATA_DICTIONARY.md` for complete field descriptions, validation rules, and example queries.

---

## Key Sample Data Scenarios

### Scenario 1: Project At Risk (P001 - TurboCharger V5)
- Schedule slipped 2 weeks (June 30 → July 15)
- Multiple critical defects blocking closure
- Supplier issues causing component delays
- CFD analysis bottleneck
- Health Score: 68 (WATCHLIST)

**Agent Query:** "What are the risks to TurboCharger V5 delivery?"

### Scenario 2: Project On Track (P002 - EV Motor Control)
- Schedule on target (June 30)
- High quality execution (92% pass rate on tests)
- Good resource utilization
- One CAN bus EMI issue under investigation
- Health Score: 82 (HEALTHY)

**Agent Query:** "What is the delivery confidence for EV Motor Control?"

### Scenario 3: Project With Process Compliance Issues (P003 - Safety Module)
- Safety requirements and verification at risk
- ASIL decomposition blocked by external consultant delay
- 45 days of escalation pending
- FMEA analysis incomplete (12 failure modes)
- Health Score: 71 (WATCHLIST)

**Agent Query:** "Analyze functional safety readiness for Safety Module program"

### Scenario 4: Completed Project (P004 - Legacy Migration)
- Project completed with minor overruns
- 10-day schedule slip (April 30 → May 5)
- 1.3% budget overrun ($20K)
- Data integrity issues resolved
- Successfully migrated to production

**Agent Query:** "Generate lessons learned report for Legacy System Migration"

### Scenario 5: Security Program (P005 - Cybersecurity Hardening)
- Phase 1 (Q2): Threat modeling 70% complete
- Phase 2 (Q3): Security testing in progress
- Critical crypto vulnerability (D013) being remediated
- FIPS 140-2 certification path defined
- Health Score: 79 (HEALTHY)

**Agent Query:** "What are the security compliance gaps and remediation timeline?"

---

## Additional Resources

### Templates
- `templates/WEEKLY_REPORT_TEMPLATE.md` - Weekly status template
- `templates/MONTHLY_EXECUTIVE_REPORT_TEMPLATE.md` - Monthly dashboard template

### Documentation
- `README.md` - Overall project documentation
- `.instructions.md` - Agent system prompt
- `DATA_DICTIONARY.md` - Complete field reference

---

## Getting Started (5-Minute Quick Start)

1. **Review this file** (3 min) - Understand data structure
2. **Open README.md** (2 min) - Review agent capabilities
3. **Ask the agent a question:**

```
Query: "Generate a portfolio health dashboard for May 2026"

Expected Response:
- Executive Summary (1-2 paragraphs)
- KPI Dashboard (10+ metrics)
- Project Health Overview (table)
- Critical Risks (3-5 top risks)
- Recommendations (3-5 action items)
- Action Items (owners + due dates)
```

---

**Last Updated:** May 30, 2026
**Next Data Refresh:** June 6, 2026 (weekly update cycle)
