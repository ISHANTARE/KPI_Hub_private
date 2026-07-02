"""
pages/07_data_upload.py
Upload updated CSV files to refresh metrics, requirements, commits, and defects.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

import lib.sidebar as sidebar
import lib.data_loader as data_loader
from lib.styling import render_page_header

# ── Bootstrap & load ────────────────────────────────────────────────────────
sidebar.bootstrap_sidebar()
from lib.auth import require_role
require_role(["Manager"])

data = data_loader.load_data()
if data is None:
    st.error("Could not load data.")
    st.stop()

render_page_header(
    "Data Upload",
    "Upload updated CSV files to refresh metrics, requirements, commits, and defects.",
)

# ── File Mapping ─────────────────────────────────────────────────────────────
file_mapping = {
    'Projects Status (projects_status.csv)':            ('projects',  'projects_status.csv'),
    'Milestones (milestones.csv)':                      ('projects',  'milestones.csv'),
    'Budget Tracking (budget_tracking.csv)':            ('projects',  'budget_tracking.csv'),
    'Risk Register (risk_register.csv)':                ('risks',     'risk_register.csv'),
    'Resource Allocation (resource_allocation.csv)':    ('resources', 'resource_allocation.csv'),
    'Defects (defects.csv)':                            ('metrics',   'defects.csv'),
    'Test Cases (test_execution.csv)':                  ('metrics',   'test_execution.csv'),
    'Requirements (requirements.csv)':                  ('metrics',   'requirements.csv'),
    'Issues (issues.csv)':                              ('projects',  'issues.csv'),
    'Escalations (escalations.csv)':                    ('projects',  'escalations.csv'),
    'ASPICE Compliance (aspice_status.csv)':            ('metrics',   'aspice_status.csv'),
    'Change Request / Ticket Analysis (ecrs.csv)':      ('projects',  'ecrs.csv'),
    'Development Commits (development_metrics.csv)':    ('metrics',   'development_metrics.csv'),
}

selected_file_type = st.selectbox("Select CSV file to replace/upload", list(file_mapping.keys()))
uploaded_file      = st.file_uploader("Choose CSV file", type=['csv'])

if uploaded_file is not None:
    folder, filename = file_mapping[selected_file_type]
    target_path      = Path("data") / folder / filename

    try:
        uploaded_df = pd.read_csv(uploaded_file)
        
        # Pydantic Validation
        from lib.models import MODEL_MAPPING, validate_dataframe
        from lib.database import save_dataframe_to_db
        
        model_class = MODEL_MAPPING.get(filename)
        if model_class:
            valid_df, errors = validate_dataframe(uploaded_df, model_class)
            if errors:
                st.warning(f"Found {len(errors)} validation warnings (e.g. {errors[0]})")

        if target_path.exists():
            existing_df  = pd.read_csv(target_path)
            uploaded_cols = set(uploaded_df.columns)
            existing_cols = set(existing_df.columns)
            missing_cols  = existing_cols - uploaded_cols
            extra_cols    = uploaded_cols  - existing_cols

            if missing_cols:
                st.error(f"Validation Failed! Uploaded file is missing required columns: {list(missing_cols)}")
            else:
                if extra_cols:
                    st.warning(f"Note: Uploaded file contains extra columns that will be added: {list(extra_cols)}")
                if st.button(f"Confirm & Overwrite {filename}", type="primary"):
                    # Save runtime CSV
                    uploaded_df.to_csv(target_path, index=False)
                    
                    # Archive upload
                    archive_dir = Path("data") / "uploads"
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    archive_path = archive_dir / f"{target_path.stem}_{timestamp}.csv"
                    uploaded_df.to_csv(archive_path, index=False)
                    
                    # Sync to SQLite DB
                    table_name = target_path.stem
                    if table_name == "projects_status": table_name = "projects"
                    elif table_name == "budget_tracking": table_name = "budget"
                    elif table_name == "risk_register": table_name = "risks"
                    elif table_name == "resource_allocation": table_name = "resources"
                    elif table_name == "aspice_status": table_name = "aspice"
                    elif table_name == "test_execution": table_name = "tests"
                    from lib.database import save_dataframe_to_db, sync_all_csvs_to_db
                    save_dataframe_to_db(table_name, uploaded_df, if_exists="replace")
                    sync_all_csvs_to_db(force=True)

                    st.success(f"Successfully updated {filename}, synced to SQLite DB, and archived!")
                    st.cache_data.clear()
        else:
            if st.button(f"Save as New File {filename}", type="primary"):
                target_path.parent.mkdir(parents=True, exist_ok=True)
                uploaded_df.to_csv(target_path, index=False)
                
                table_name = target_path.stem
                save_dataframe_to_db(table_name, uploaded_df, if_exists="replace")
                
                st.success(f"Successfully created and saved {target_path}!")
                st.cache_data.clear()
    except Exception as e:
        st.error(f"Error validating file: {e}")

st.divider()

# ── AI Data Segregation ───────────────────────────────────────────────────────
st.markdown("#### AI Data Segregation")
st.caption("Upload unstructured documents to extract and segregate data by category.")

uploaded_seg_doc = st.file_uploader("Choose a document to segregate", type=['pptx', 'xlsx', 'txt'], key="seg_doc")

if uploaded_seg_doc is not None:
    doc_type = uploaded_seg_doc.name.split('.')[-1].lower()
    with st.spinner("Parsing document..."):
        from lib.doc_parser import extract_text_from_file
        doc_text = extract_text_from_file(uploaded_seg_doc, doc_type)

    with st.expander("Preview Extracted Text"):
        st.text(doc_text[:1000] + ("..." if len(doc_text) > 1000 else ""))

    if st.button("Extract & Segregate Data"):
        with st.spinner("Analyzing and segregating data with AI..."):
            from integrations.openai_client import get_completion
            prompt = f"""Analyze the following text and segregate it into relevant datasets. Focus on:
1. **issues**: (summary, description, severity, status)
2. **risks**: (risk_description, probability, impact, mitigation)
3. **requirements**: (requirement_text, priority, status)
4. **team**: (resource_name, role, project_id)
5. **kpis**: (metric_name, value, target, status)

Format the response as a JSON object with keys: "issues", "risks", "requirements", "team", "kpis". Each key should contain a list of objects. Return ONLY valid JSON without markdown formatting.
Text:
{doc_text[:10000]}"""
            response = get_completion(prompt, max_tokens=1500)
            try:
                import json, re
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    extracted_data = json.loads(match.group(0))
                    st.session_state['segregated_data'] = extracted_data
                else:
                    st.error("Failed to parse AI response.")
            except Exception as e:
                st.error(f"Error parsing AI response: {e}")

if st.session_state.get('segregated_data'):
    st.success("AI successfully extracted the following data:")

    data_map = {
        "issues":       {"file": "projects/issues.csv",              "cols": ["ISSUE_TITLE", "DESCRIPTION", "SEVERITY", "STATUS", "ISSUE_ID", "PROJECT_ID"]},
        "risks":        {"file": "risks/risk_register.csv",          "cols": ["RISK_DESCRIPTION", "PROBABILITY", "IMPACT", "MITIGATION", "RISK_ID", "PROJECT_ID"]},
        "requirements": {"file": "metrics/requirements.csv",         "cols": ["REQUIREMENT_TEXT", "PRIORITY", "STATUS", "REQUIREMENT_ID", "PROJECT_ID"]},
        "team":         {"file": "resources/resource_allocation.csv","cols": ["RESOURCE_NAME", "ROLE", "PROJECT_ID"]},
        "kpis":         {"file": "metrics/kpis.csv",                 "cols": ["METRIC_NAME", "VALUE", "TARGET", "STATUS", "PROJECT_ID"]},
    }

    for key, items in st.session_state['segregated_data'].items():
        if items:
            st.write(f"### {key.title()} ({len(items)})")
            df = pd.DataFrame(items)
            st.dataframe(df, width='stretch')

    st.divider()
    apply_mode = st.radio("How would you like to apply this data?",
                          ["Append to existing CSVs", "Overwrite existing CSVs"], horizontal=True)

    if st.button("Apply Data to CSVs", type="primary"):
        for key, items in st.session_state['segregated_data'].items():
            if items and key in data_map:
                target_file = Path("data") / data_map[key]["file"]
                new_df      = pd.DataFrame(items)
                new_df.columns = [c.upper() for c in new_df.columns]
                if 'SUMMARY' in new_df.columns and key == 'issues':
                    new_df.rename(columns={'SUMMARY': 'ISSUE_TITLE'}, inplace=True)
                for col in data_map[key]["cols"]:
                    if col not in new_df.columns:
                        new_df[col] = "AI_GEN" if "ID" in col else "N/A"
                if target_file.exists():
                    existing_df = pd.read_csv(target_file)
                    if apply_mode.startswith("Append"):
                        final_df = pd.concat([existing_df, new_df], ignore_index=True)
                    else:
                        final_df = new_df
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    final_df = new_df
                final_df.to_csv(target_file, index=False)
                st.success(f"Saved {len(items)} {key} to {target_file.name}")
        st.session_state['segregated_data'] = None
        st.cache_data.clear()

st.divider()

# ── Transcript & Minutes Parser ───────────────────────────────────────────────
st.markdown("#### Transcript & Minutes Parser")
st.caption("Upload raw text transcripts, meeting minutes, or emails to extract commitments and flag missing Jira tickets.")

uploaded_doc = st.file_uploader("Choose a document", type=['txt', 'eml', 'pptx', 'xlsx'])
if uploaded_doc is not None:
    doc_type = uploaded_doc.name.split('.')[-1].lower()
    with st.spinner("Parsing document..."):
        from lib.doc_parser import extract_text_from_file
        doc_text = extract_text_from_file(uploaded_doc, doc_type)

    with st.expander("Preview Extracted Text"):
        st.text(doc_text[:1000] + ("..." if len(doc_text) > 1000 else ""))

    if st.button("Extract Implicit Commitments"):
        with st.spinner("Analyzing with AI..."):
            from integrations.openai_client import get_completion
            prompt = f"""Analyze the following meeting transcript/document. Extract any implicit commitments, action items, or promises made during this conversation. 
Return a JSON array of objects with keys: 'assignee' (who is doing it), 'task_description' (what they are doing), 'deadline' (when it's due, or 'TBD'), 'issue_type' (Task/Bug).
Ensure the response is ONLY valid JSON.
Text:
{doc_text[:10000]}"""
            response = get_completion(prompt, max_tokens=1000)
            try:
                import json, re
                match = re.search(r'\[.*\]', response, re.DOTALL)
                if match:
                    commitments = json.loads(match.group(0))
                    issues_df   = data.get('issues', pd.DataFrame())
                    unticketed  = []
                    for comm in commitments:
                        assignee    = comm.get('assignee', '')
                        task        = comm.get('task_description', '')
                        is_ticketed = False
                        if not issues_df.empty and assignee:
                            person_issues = issues_df[issues_df['ASSIGNED_TO'].str.contains(assignee, case=False, na=False)]
                            for _, row in person_issues.iterrows():
                                title = str(row.get('ISSUE_TITLE', '')).lower()
                                words = set(task.lower().split())
                                if len(words.intersection(set(title.split()))) > 2:
                                    is_ticketed = True
                                    break
                        if not is_ticketed:
                            unticketed.append(comm)
                    st.session_state['unticketed_commitments'] = unticketed
                    if not unticketed:
                        st.success("All extracted commitments already seem to have Jira tickets!")
                else:
                    st.error("Failed to parse AI response. Please try again.")
            except Exception as e:
                st.error(f"Error parsing AI response: {e}")

if st.session_state.get('unticketed_commitments'):
    st.warning(f"Found {len(st.session_state['unticketed_commitments'])} implicit commitments without Jira tickets!")
    for i, ticket in enumerate(st.session_state['unticketed_commitments']):
        with st.container():
            st.write(f"**Assignee:** {ticket.get('assignee', 'Unassigned')} | **Deadline:** {ticket.get('deadline', 'TBD')}")
            st.write(f"**Task:** {ticket.get('task_description', '')}")

            if st.button(f"Generate Ticket {i+1}", key=f"create_ticket_{i}"):
                from integrations.jira_sync import JiraSync
                jira = JiraSync()
                _active_project = st.session_state.get('selected_project', 'All')
                project_key     = _active_project if _active_project and _active_project != 'All' else 'P001'
                issue_id = jira.create_issue(
                    project_key,
                    ticket.get('task_description', '')[:50],
                    ticket.get('task_description', ''),
                    ticket.get('issue_type', 'Task')
                )
                if issue_id:
                    st.success(f"Successfully created Jira ticket: {issue_id}")
                    csv_path = Path("data") / "projects" / "issues.csv"
                    if csv_path.exists():
                        df_csv  = pd.read_csv(csv_path)
                        new_row = {
                            'ISSUE_ID':        issue_id,
                            'PROJECT_ID':      project_key,
                            'ISSUE_TITLE':     ticket.get('task_description', '')[:50],
                            'DESCRIPTION':     ticket.get('task_description', ''),
                            'SEVERITY':        'MEDIUM',
                            'STATUS':          'OPEN',
                            'ASSIGNED_TO':     ticket.get('assignee', 'Unassigned'),
                            'CREATED_DATE':    datetime.now().strftime("%Y-%m-%d"),
                            'RESOLUTION_DATE': 'N/A',
                        }
                        df_csv = pd.concat([df_csv, pd.DataFrame([new_row])], ignore_index=True)
                        df_csv.to_csv(csv_path, index=False)
                else:
                    st.error("Failed to create Jira ticket.")
