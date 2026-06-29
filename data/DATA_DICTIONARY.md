# Data Dictionary - KPI Agent

## Overview
This document describes all CSV files in the data directory and their fields. Use this to understand data structure and validation rules.

---

## File Structure

### 1. PROJECTS

#### projects_status.csv
Master project inventory with health metrics.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| PROJECT_ID | String | Unique project identifier | P[001-999] | P001 |
| PROJECT_NAME | String | Human-readable project name | 1-80 chars | TurboCharger V5 |
| PROGRAM | String | Program name/code | 1-40 chars | Turbo Advanced |
| RELEASE | String | Release/quarter designation | Q[1-4]-YYYY or "Ongoing" | Q3-2026 |
| PRODUCT_LINE | String | Product line category | 1-30 chars | Heavy Duty |
| STATUS | String | Current project status | In Progress, Completed, Planned, On Hold | In Progress |
| PLANNED_END_DATE | Date | Original planned completion | YYYY-MM-DD | 2026-06-30 |
| ACTUAL_END_DATE | Date | Actual/projected completion | YYYY-MM-DD or N/A | 2026-07-15 |
| BASELINE_SCHEDULE | Date | Baseline plan completion | YYYY-MM-DD | 2026-06-30 |
| CURRENT_SCHEDULE | Date | Current forecast completion | YYYY-MM-DD | 2026-07-15 |
| SCHEDULE_STATUS | String | Traffic light indicator | GREEN, YELLOW, RED | RED |
| BUDGET_PLANNED | Number | Planned budget | USD amount | 5000000 |
| BUDGET_SPENT | Number | Amount spent to date | USD amount | 3500000 |
| BUDGET_STATUS | String | Budget health | GREEN, YELLOW, RED | YELLOW |
| RESOURCE_ALLOCATED | Number | Planned FTE | 0-100 | 25 |
| RESOURCE_UTILIZED | Number | Actual FTE in use | 0-100 | 22 |
| HEALTH_STATUS | String | Overall project health | EXCELLENT, HEALTHY, WATCHLIST, CRITICAL | WATCHLIST |
| HEALTH_SCORE | Number | Numeric health (0-100) | 0-100 | 68 |
| DELIVERY_CONFIDENCE | String | Confidence in delivery date | HIGH, MEDIUM, LOW | MEDIUM |
| NOTES | String | Free-form notes | 1-500 chars | "2-week delay due to supplier..." |

#### milestones.csv
Project milestones and completion tracking.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| MILESTONE_ID | String | Unique milestone ID | M[001-999] | M001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| MILESTONE_NAME | String | Milestone description | 1-80 chars | Requirements Baseline Complete |
| PLANNED_DATE | Date | Original planned date | YYYY-MM-DD | 2026-03-15 |
| ACTUAL_DATE | Date | Actual completion or N/A | YYYY-MM-DD or N/A | 2026-03-18 |
| BASELINE_DATE | Date | Baseline plan date | YYYY-MM-DD | 2026-03-15 |
| STATUS | String | Milestone status | COMPLETED, IN_PROGRESS, PLANNED, AT_RISK, BLOCKED | COMPLETED |
| COMPLETION_PCT | String | % complete | 0-100% | 100% |
| OWNER | String | Responsible person | Name | John Smith |
| CRITICAL_PATH | String | Is critical path? | YES, NO | YES |
| DEPENDENCIES | String | Dependent milestones | Comma-separated IDs or "None" | "M001, M002" |
| NOTES | String | Free-form notes | 1-500 chars | "3-day delay due to stakeholder..." |

#### budget_tracking.csv
Financial tracking by project and category.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| BUDGET_ID | String | Unique budget line ID | BUD[001-999] | BUD001 |
| PROJECT_ID | String | Parent project or "Q-TOTAL" | P[001-999] or "[Q1-4]-TOTAL" | P001 |
| BUDGET_CATEGORY | String | Spending category | Engineering Labor, Materials, Testing, Tools, Other | Engineering Labor |
| BUDGET_PERIOD | String | Time period | Q[1-4] YYYY or "Q[1-4]-Q[1-4] YYYY" | Q1-Q2 2026 |
| PLANNED_AMOUNT | Number | Budgeted amount | USD | 1500000 |
| COMMITTED_AMOUNT | Number | Purchase orders issued | USD | 1400000 |
| SPENT_AMOUNT | Number | Invoiced/paid amount | USD | 1200000 |
| VARIANCE_AMOUNT | Number | Dollar variance (Planned - Spent) | USD (can be negative) | 300000 |
| VARIANCE_PCT | String | Percentage variance | ±0-100% | 20% |
| STATUS | String | Budget health | UNDERSPEND, ON_TRACK, OVERSPEND | UNDERSPEND |
| NOTES | String | Variance explanation | 1-500 chars | "Hiring delays; not all contractor..." |

#### issues.csv
Project blockers and escalations.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| ISSUE_ID | String | Unique issue ID | I[001-999] | I001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| ISSUE_TITLE | String | Issue summary | 1-80 chars | Supplier Quality Issue - Heat Exchanger |
| DESCRIPTION | String | Detailed description | 1-500 chars | Incoming inspection rejecting 12% of... |
| SEVERITY | String | Impact level | CRITICAL, HIGH, MEDIUM, LOW | HIGH |
| STATUS | String | Issue state | OPEN, IN_PROGRESS, RESOLVED, ESCALATED, CLOSED | IN_PROGRESS |
| CREATED_DATE | Date | Issue creation | YYYY-MM-DD | 2026-05-10 |
| RESOLUTION_DATE | Date | Resolved date or N/A | YYYY-MM-DD or N/A | 2026-05-18 |
| DAYS_OPEN | Number | Days since creation | 0-365+ | 20 |
| ASSIGNED_TO | String | Responsible person | Name | John Smith |
| RELATED_RISK | String | Risk registry link | R[001-999] or "None" | R001 |
| ESCALATION_LEVEL | String | Escalation path | ENGINEERING, PMO, MANAGEMENT, PROGRAM_MANAGEMENT | MANAGEMENT |
| ROOT_CAUSE | String | Identified cause | 1-200 chars | Process control breakdown at supplier |
| IMPACT | String | Business impact | 1-200 chars | 2-week schedule impact |

#### escalations.csv
Management escalations requiring steering committee attention.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| ESCALATION_ID | String | Unique escalation ID | E[001-999] | E001 |
| PROJECT_ID | String | Related project | P[001-999] | P001 |
| ESCALATION_TITLE | String | Escalation summary | 1-80 chars | Supplier Quality Delivery Miss |
| ESCALATION_TYPE | String | Category | CUSTOMER, TECHNICAL, RESOURCE, SCHEDULE, INFRASTRUCTURE, DATA_QUALITY, PROCUREMENT, OPERATIONS, PROCESS | CUSTOMER |
| SEVERITY | String | Urgency/impact | CRITICAL, HIGH, MEDIUM, LOW | HIGH |
| STATUS | String | Escalation state | ESCALATED, IN_RESOLUTION, RESOLVED | ESCALATED |
| CREATED_DATE | Date | Escalation date | YYYY-MM-DD | 2026-05-10 |
| RESOLVED_DATE | Date | Resolution date or N/A | YYYY-MM-DD or N/A | N/A |
| ESCALATED_TO | String | Executive recipient | Role/Name | VP Sales & Program Director |
| ROOT_CAUSE | String | Underlying issue | 1-200 chars | Supplier capacity constraint |
| BUSINESS_IMPACT | String | Business consequence | 1-200 chars | Risk of 2-week program delay |
| RESOLUTION | String | Corrective action | 1-200 chars | Engage secondary supplier |
| DAYS_OPEN | Number | Days since escalation | 0-365+ | 20 |

---

### 2. RISKS

#### risk_register.csv
Risk identification and tracking.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| RISK_ID | String | Unique risk ID | R[001-999] | R001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| RISK_TITLE | String | Risk summary | 1-80 chars | Supplier Lead Time Delay |
| DESCRIPTION | String | Risk detail | 1-500 chars | TurboCharger V5 compressor supplier... |
| IMPACT | String | Consequence severity | LOW, MEDIUM, HIGH, CRITICAL | HIGH |
| PROBABILITY | String | Likelihood | LOW, MEDIUM, HIGH | HIGH |
| EXPOSURE_SCORE | Number | Impact × Probability | 1-9 (3×3 matrix) | 9 |
| SEVERITY | String | Overall severity | LOW, MEDIUM, HIGH, CRITICAL | CRITICAL |
| STATUS | String | Risk state | OPEN, MITIGATED, CLOSED, ACTIVE | OPEN |
| OWNER | String | Risk owner | Name | John Smith |
| MITIGATION_PLAN | String | Mitigation strategy | 1-200 chars | Engage secondary supplier... |
| DUE_DATE | Date | Mitigation target | YYYY-MM-DD | 2026-06-15 |
| CREATED_DATE | Date | Risk identification date | YYYY-MM-DD | 2026-05-15 |
| DAYS_OPEN | Number | Days identified | 0-365+ | 15 |

---

### 3. RESOURCES

#### resource_allocation.csv
Team allocation and utilization tracking.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| TEAM_MEMBER | String | Person or team name | 1-50 chars | John Smith |
| ROLE | String | Job title/role | 1-50 chars | Project Manager |
| SKILL | String | Primary skill | 1-50 chars | Program Management |
| ALLOCATED_HOURS_WEEKLY | Number | Planned hours/week | 0-60 | 40 |
| UTILIZED_HOURS_WEEKLY | Number | Actual hours/week | 0-60 | 40 |
| UTILIZATION_PCT | String | % used vs planned | 0-150% | 100% |
| DEPARTMENT | String | Organization | 1-40 chars | PMO |
| START_DATE | Date | Assignment start | YYYY-MM-DD | 2026-01-01 |
| END_DATE | Date | Assignment end | YYYY-MM-DD | 2026-08-31 |
| ALLOCATION_STATUS | String | Status | ALLOCATED, OVERALLOCATED, UNDERUTILIZED, COMPLETED | ALLOCATED |
| NOTES | String | Free-form notes | 1-500 chars | "Full-time project lead" |

---

### 4. METRICS

#### defects.csv
Quality defect tracking.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| DEFECT_ID | String | Unique defect ID | D[001-999] | D001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| TITLE | String | Defect summary | 1-80 chars | Thermal Simulation Mismatch |
| DESCRIPTION | String | Defect detail | 1-500 chars | Compressor outlet temperature 5°C higher... |
| SEVERITY | String | Impact level | CRITICAL, HIGH, MEDIUM, LOW | CRITICAL |
| STATUS | String | Defect state | OPEN, IN_PROGRESS, FIXED, VERIFIED, CLOSED, WONTFIX | OPEN |
| FOUND_DATE | Date | Discovery date | YYYY-MM-DD | 2026-05-10 |
| FIXED_DATE | Date | Fix date or N/A | YYYY-MM-DD or N/A | N/A |
| DAYS_OPEN | Number | Days since discovery | 0-365+ | 20 |
| ROOT_CAUSE | String | Identified cause | 1-200 chars | Design assumption error... |
| ASSIGNED_TO | String | Developer/owner | Name | Maria Garcia |
| COMPONENT | String | Affected component | 1-50 chars | Compressor Design |
| VERIFICATION_STATUS | String | Test status | PENDING_VERIFICATION, PENDING_FIX, INVESTIGATING, IN_PROGRESS, TESTING, VERIFIED, RESOLVED | PENDING_VERIFICATION |

#### test_execution.csv
Test case execution and results.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| TEST_ID | String | Unique test case ID | TC[001-999] | TC001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| TEST_SUITE | String | Test suite name | 1-50 chars | Thermal Performance |
| TEST_CASE_NAME | String | Test case description | 1-100 chars | Compressor outlet temperature... |
| STATUS | String | Execution status | PASSED, FAILED, BLOCKED, IN_PROGRESS, NOT_EXECUTED | PASSED |
| EXECUTION_DATE | Date | Last execution date | YYYY-MM-DD | 2026-05-28 |
| PASS_DATE | Date | Date of pass or N/A | YYYY-MM-DD or N/A | 2026-05-28 |
| FAIL_DATE | Date | Date of fail or N/A | YYYY-MM-DD or N/A | N/A |
| DEFECT_ID | String | Linked defect or N/A | D[001-999] or N/A | D001 |
| AUTOMATION_STATUS | String | Automation level | AUTOMATED, MANUAL, SEMI_AUTOMATED | AUTOMATED |
| TEST_CATEGORY | String | Test type | Functional, Integration, Performance, Regression, Safety, Security, Compliance | Functional |
| COMPONENT | String | Component tested | 1-50 chars | Compressor Design |
| ENVIRONMENT | String | Test environment | 1-50 chars | Test Dyno 1 |
| EXECUTIONS | Number | Total executions | 1-1000 | 5 |
| PASS_COUNT | Number | Passed executions | 0-executions | 4 |
| FAIL_COUNT | Number | Failed executions | 0-executions | 1 |

#### requirements.csv
Requirements management and traceability.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| REQUIREMENT_ID | String | Unique requirement ID | REQ[001-999] | REQ001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| REQUIREMENT_TEXT | String | Requirement description | 1-500 chars | Compressor outlet temperature... |
| CATEGORY | String | Req category | Functional, Performance, Safety, Thermal, Control, Mechanical, Communication, etc | Thermal |
| PRIORITY | String | Priority level | Critical, High, Medium, Low | Critical |
| STATUS | String | Approval status | APPROVED, OPEN, CHANGED, WITHDRAWN | APPROVED |
| APPROVED_DATE | Date | Approval date or N/A | YYYY-MM-DD or N/A | 2026-01-15 |
| LAST_CHANGED | Date | Last modification or N/A | YYYY-MM-DD or N/A | 2026-04-10 |
| CHANGE_COUNT | Number | Times changed | 0-100 | 2 |
| TRACE_TEST_CASE | String | Linked test cases | Comma-separated TC IDs or N/A | "TC002, TC001" |
| TRACE_DESIGN | String | Design element | Comma-separated IDs or N/A | "CAD-001" |
| VERIFICATION_STATUS | String | Verification state | VERIFIED, IN_PROGRESS, NOT_STARTED, BLOCKED | VERIFIED |
| ASIL_LEVEL | String | Safety level or N/A | A, B, C, D or N/A | "D" |

#### design_reviews.csv
Design review meeting tracking.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| DESIGN_REVIEW_ID | String | Unique review ID | DR[001-999] | DR001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| REVIEW_TYPE | String | Review category | System Design, Detailed Design, Code Review, FAI Readiness | System Design Review |
| REVIEW_DATE | Date | Meeting date | YYYY-MM-DD | 2026-03-20 |
| DESIGN_PHASE | String | Project phase | Planning, System Architecture, Detailed Design, Coding, FAI Readiness | System Architecture |
| STATUS | String | Review status | COMPLETED, IN_PROGRESS, SCHEDULED, BLOCKED | COMPLETED |
| OPEN_ACTIONS | Number | Open action items | 0-100 | 0 |
| CLOSED_ACTIONS | Number | Closed action items | 0-100 | 18 |
| ACTION_COMPLETION_PCT | String | % of actions complete | 0-100% | 100% |
| ATTENDEES | String | Participants | Comma-separated names | "John Smith, Maria Garcia" |
| LEAD_REVIEWER | String | Review lead | Name | John Smith |
| NEXT_REVIEW_DATE | Date | Follow-up date | YYYY-MM-DD | 2026-04-01 |
| NOTES | String | Review notes | 1-500 chars | "All actions resolved..." |

#### engineering_kpis.csv
General engineering metrics and KPIs.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| METRIC_NAME | String | KPI name | 1-50 chars | Requirements Total |
| METRIC_CATEGORY | String | Category | Requirements, Testing, Quality, Functional Safety, Cybersecurity | Requirements |
| CURRENT_VALUE | Number/String | Current value | Varies by metric | 247 |
| BASELINE_VALUE | Number/String | Baseline/target | Varies by metric | 250 |
| TARGET_VALUE | Number/String | Goal value | Varies by metric | 250 |
| UNIT | String | Measurement unit | Count, %, Hours, etc | Count |
| TREND | String | Trend direction | STABLE, UP, DOWN | STABLE |
| STATUS | String | Health status | GREEN, YELLOW, RED | GREEN |
| CONFIDENCE | String | Data confidence | HIGH, MEDIUM, LOW | HIGH |
| DATE_MEASURED | Date | Measurement date | YYYY-MM-DD | 2026-05-28 |
| NOTES | String | Context | 1-500 chars | "All requirements baselined" |

#### aspice_status.csv
ASPICE process compliance tracking.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| ASPICE_PROCESS | String | Process code | SYS.1-4, SWE.1-6, ASS.1, etc | SYS.1 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| PROCESS_AREA | String | Process description | 1-50 chars | Software Architecture |
| TARGET_LEVEL | String | Target capability | Level 0-3 | Level 2 |
| CURRENT_LEVEL | String | Achieved level | Level 0-3 | Level 1 |
| COMPLETION_PCT | String | Completion % | 0-100% | 35% |
| WORK_PRODUCTS_PLANNED | Number | WP count | 0-50 | 5 |
| WORK_PRODUCTS_COMPLETED | Number | WP done | 0-planned | 2 |
| REVIEWS_PLANNED | Number | Review count | 0-20 | 3 |
| REVIEWS_COMPLETED | Number | Reviews done | 0-planned | 1 |
| STATUS | String | Process status | PLANNED, IN_PROGRESS, COMPLETED, BLOCKED | IN_PROGRESS |
| ASSESSMENT_READINESS | String | Assessment ready? | READY, NEARLY_READY, NOT_READY | NOT_READY |
| COMMENTS | String | Status notes | 1-500 chars | "System architecture drafted..." |

#### functional_safety_requirements.csv
Safety-critical requirements.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| SAFETY_REQ_ID | String | Unique safety req ID | SR[001-999] | SR001 |
| PROJECT_ID | String | Parent project | P[001-999] | P003 |
| SAFETY_REQUIREMENT | String | Safety requirement | 1-200 chars | Motor control shall detect power... |
| ASIL_LEVEL | String | Automotive Safety Integrity Level | A, B, C, D | D |
| CATEGORY | String | Safety category | Failure Detection, System Performance, Fault Detection, etc | Failure Detection |
| STATUS | String | Requirement status | APPROVED, OPEN, DERIVED | APPROVED |
| DERIVED_FROM | String | Parent requirement | REQ[001-999] | REQ011 |
| VERIFICATION_METHOD | String | How verified | Simulation, Hardware Test, Analysis, etc | Simulation & Hardware Test |
| TEST_ID | String | Verification test | TC[001-999] or N/A | TC014 |
| VALIDATION_STATUS | String | Validation state | VERIFIED, IN_VERIFICATION, BLOCKED, NOT_STARTED | VERIFIED |
| SAFETY_ANALYSIS_LINK | String | FMEA/analysis link | FMEA_[CODE]_[NUM] | FMEA_SM_001 |
| APPROVED_DATE | Date | Approval date | YYYY-MM-DD | 2026-04-10 |
| NOTES | String | Status notes | 1-200 chars | "Critical timing requirement..." |

#### verification_activities.csv
Verification test execution.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| VERIFICATION_ID | String | Unique verification ID | VER[001-999] | VER001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| VERIFICATION_ACTIVITY | String | Activity description | 1-50 chars | Compressor Performance Verification |
| COMPONENT | String | Component verified | 1-50 chars | Compressor |
| REQUIREMENT_ID | String | Requirement traced | REQ[001-999] | REQ001 |
| PLANNED_DATE | Date | Original schedule | YYYY-MM-DD | 2026-05-20 |
| ACTUAL_DATE | Date | Actual execution | YYYY-MM-DD or N/A | 2026-05-28 |
| STATUS | String | Activity status | COMPLETED, FAILED, PLANNED, IN_PROGRESS | COMPLETED |
| RESULT | String | Verification result | PASSED, FAILED, PENDING | PASSED |
| FINDINGS_COUNT | Number | Issues found | 0-100 | 2 |
| OPEN_FINDINGS | Number | Unresolved findings | 0-findings | 0 |
| VERIFICATION_METHOD | String | Test method | Dynamometer Test, HIL Testing, etc | Dynamometer Test |
| TEST_CASE_LINK | String | Related test cases | Comma-separated TC IDs | "TC001, TC002" |
| APPROVED_BY | String | Approval authority | Name | Maria Garcia |
| NOTES | String | Status notes | 1-500 chars | "Minor thermal margin identified..." |

#### validation_activities.csv
Validation activities and customer acceptance.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| VALIDATION_ID | String | Unique validation ID | VAL[001-999] | VAL001 |
| PROJECT_ID | String | Parent project | P[001-999] | P001 |
| VALIDATION_ACTIVITY | String | Activity description | 1-80 chars | Prototype Validation - Thermal |
| SCOPE | String | Validation scope | 1-200 chars | Compressor thermal performance... |
| PLANNED_DATE | Date | Planned date | YYYY-MM-DD | 2026-06-15 |
| ACTUAL_DATE | Date | Execution date | YYYY-MM-DD or N/A | N/A |
| STATUS | String | Activity status | COMPLETED, IN_PROGRESS, PLANNED, PENDING | PLANNED |
| CUSTOMER_ACCEPTANCE | String | Customer approval | PASSED, PENDING, FAILED | PENDING |
| CUSTOMERS_INVOLVED | String | Customer(s) | Comma-separated names | "OEM Tier1, Engine Development" |
| FINDINGS_COUNT | Number | Issues found | 0-100 | 0 |
| OPEN_FINDINGS | Number | Unresolved findings | 0-findings | 0 |
| VALIDATION_ENVIRONMENT | String | Test environment | 1-50 chars | "Test Vehicle with Dyno Simulation" |
| APPROVED_BY | String | Approval authority | Name or N/A | N/A |
| NOTES | String | Status notes | 1-500 chars | "Customer validation planned for Q3" |

#### action_log.csv (data/projects/action_log.csv)
Project action item tracking log for PMO Action Closure Rate calculation.

| Field | Type | Description | Format/Range | Example |
|-------|------|-------------|--------------|---------|
| ACTION_ID | String | Unique action item ID | ACT[001-999] | ACT-001 |
| PROJECT_ID | String | Parent project ID | P[001-999] | P001 |
| DESCRIPTION | String | Action item description | 1-200 chars | Review thermal simulation results |
| STATUS | String | Action completion status | Completed, Done, Open, In Progress | Completed |
| OWNER | String | Action owner / assignee | Resource Role / Name | Engineering Manager |
| DUE_DATE | Date | Action deadline | YYYY-MM-DD | 2026-05-15 |

---

## Data Quality Rules

### Mandatory Fields
- All PROJECT_IDs, *_IDs, DATEs (unless noted N/A)
- STATUS fields must use predefined values
- OWNER/ASSIGNED_TO must match resource names

### Date Format
- Format: YYYY-MM-DD (ISO 8601)
- "N/A" for unknown/pending dates
- Actual dates should be ≥ Planned dates

### Numeric Fields
- Percentages: 0-100 or 0-150% (for overallocation)
- DAYS_OPEN: calculated as (today - created_date)
- Variance: Planned - Actual (can be negative)

### Traffic Light Status
- GREEN: On track, target met, low risk
- YELLOW: Minor deviation, medium risk
- RED: Significant deviation, high risk

### Confidence Levels
- HIGH: 80-100% confidence
- MEDIUM: 50-79% confidence
- LOW: <50% confidence

---

## Example Queries

### "Get all RED items"
Filter WHERE STATUS = "RED"

### "Get critical risks"
Filter risk_register.csv WHERE SEVERITY = "CRITICAL"

### "Calculate portfolio health"
Average HEALTH_SCORE across all projects WHERE STATUS != "Completed"

### "Get resource bottlenecks"
Filter resource_allocation.csv WHERE UTILIZATION_PCT > "100%"

### "Get aging issues"
Filter issues.csv WHERE DAYS_OPEN > 30 AND STATUS != "CLOSED"

---

End of Data Dictionary
