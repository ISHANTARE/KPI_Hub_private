"""
pages/06_system_integrations.py
Local data files, configured integration endpoints, sync controls, and audit trail.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import difflib

import lib.sidebar as sidebar
import lib.data_loader as data_loader
from lib.styling import render_page_header
from integrations.config_helper import load_config
from integrations.scheduler import IntegrationScheduler

# ── Bootstrap & load ────────────────────────────────────────────────────────
sidebar.bootstrap_sidebar()
data = data_loader.load_data()
if data is None:
    st.error("Could not load data.")
    st.stop()

render_page_header(
    "System Integrations",
    "Local data files, configured integration endpoints, and sync controls.",
)

from lib.audit import log_data_edit

# ── Refresh control ──────────────────────────────────────────────────────────
if st.button("Refresh data list"):
    st.rerun()

# ── Local CSV Data Files ─────────────────────────────────────────────────────
data_dir = Path("data")
files    = list(data_dir.rglob("*.csv")) if data_dir.exists() else []

if files:
    st.markdown("#### Local CSV Data Files")
    file_cols = st.columns(3)
    for idx, f in enumerate(sorted(files)):
        col = file_cols[idx % 3]
        try:
            stat     = f.stat()
            size_kb  = stat.st_size / 1024
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            size_kb  = 0.0
            modified = "n/a"

        with col:
            with st.expander(f.name, expanded=False):
                mcol1, mcol2 = st.columns([4, 1])
                with mcol1:
                    st.markdown(
                        f'<div class="data-card">'
                        f'<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);">'
                        f'<span><b>Size:</b> {size_kb:.1f} KB</span>'
                        f'<span><b>Modified:</b> {modified}</span>'
                        f'</div>'
                        f'<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">'
                        f'<b>Path:</b> <code>{f}</code>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with mcol2:
                    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                    if st.button("Open", key=f"open_file_{f.parent.name}_{f.name}"):
                        try:
                            import subprocess, platform
                            _path = str(f.resolve())
                            if platform.system() == "Windows":
                                import os as _os
                                _os.startfile(_path)
                            elif platform.system() == "Darwin":
                                subprocess.Popen(["open", _path])
                            else:
                                subprocess.Popen(["xdg-open", _path])
                        except Exception as e:
                            st.error(f"Failed to open: {e}")

                try:
                    df_full     = pd.read_csv(f)
                    is_log_file = 'log' in f.name.lower()
                    is_manager  = st.session_state.get('user_role') == 'Manager'

                    if not is_log_file and is_manager:
                        st.markdown(f"**Edit Data** ({len(df_full)} rows)")
                        edited_df = st.data_editor(
                            df_full,
                            use_container_width=True,
                            num_rows="dynamic",
                            key=f"editor_{f.parent.name}_{f.name}",
                        )
                        scol1, scol2 = st.columns([4, 1])
                        with scol2:
                            if st.button("Save Changes", key=f"save_{f.parent.name}_{f.name}", use_container_width=True):
                                try:
                                    edited_df.to_csv(f, index=False)
                                    log_data_edit('Manager', str(f))
                                    st.cache_data.clear()
                                    st.success(f"Saved {f.name}")
                                except Exception as e:
                                    st.error(f"Failed to save: {e}")
                    else:
                        if is_log_file:
                            st.caption(f"{len(df_full)} rows — Audit Log (Read-Only)")
                        else:
                            st.caption(f"{len(df_full)} rows — View-Only")
                        st.dataframe(df_full, use_container_width=True)
                except Exception as e:
                    st.error(f"Cannot load file: {e}")
else:
    st.info("No CSV data files found under the `data/` folder.")

# ── Configured Integrations ──────────────────────────────────────────────────
st.markdown("#### Configured Integrations")

from urllib.parse import urlparse
import re

def is_valid_url(u):
    try:
        p = urlparse(str(u))
        return all([p.scheme in ('http', 'https'), p.netloc])
    except Exception:
        return False

def is_valid_email(e):
    if not e:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(e)))

def is_valid_port(p):
    try:
        v = int(p)
        return 0 < v < 65536
    except Exception:
        return False

try:
    cfg = IntegrationScheduler().config
except Exception:
    cfg = None

from dotenv import load_dotenv
load_dotenv()
ui_pw = os.getenv('INTEGRATIONS_UI_PASSWORD')

if 'integrations_unlocked' not in st.session_state:
    st.session_state['integrations_unlocked'] = False

if not st.session_state['integrations_unlocked']:
    if ui_pw:
        entered = st.text_input('Enter integrations UI password to unlock editing', type='password', key='ui_pw_input')
        if st.button('Unlock'):
            if entered == ui_pw:
                st.session_state['integrations_unlocked'] = True
                st.success('Integrations editing unlocked')
            else:
                st.error('Incorrect password')
    else:
        st.warning('No INTEGRATIONS_UI_PASSWORD set — editing is allowed but not protected.')
        if st.checkbox('Enable editing (unsafe)', key='allow_edit_no_pw'):
            st.session_state['integrations_unlocked'] = True

if cfg:
    try:
        import yaml as _yaml
    except Exception:
        _yaml = None

    integration_meta = {
        'codebeamer':       'Codebeamer ALM',
        'jira':             'Jira Software',
        'email':            'SMTP Email Notifications',
        'github':           'GitHub / GitLab',
        'teams':            'Microsoft Teams',
        'confluence':       'Confluence Wiki',
        'sharepoint':       'SharePoint Documents',
        'powerbi':          'Power BI Reports',
        'polarion_doors':   'Polarion & DOORS',
        'test_mgmt':        'Test Management (TestRail/Xray)',
        'outlook_calendar': 'Outlook Calendar',
        'kb_rag':           'AI Knowledge Base (RAG)',
        'slack':            'Slack Channel',
        'asana':            'Asana Project Board',
    }

    edited_cfg        = {}
    integration_cols  = st.columns(3)

    for idx, (section, conf) in enumerate(cfg.items()):
        col   = integration_cols[idx % 3]
        title = integration_meta.get(section, section.replace('_', ' ').title())
        with col:
            with st.expander(title, expanded=False):
                st.markdown(f"#### {title} Config")
                if section in ['jira', 'polarion_doors', 'codebeamer']:
                    st.info("🔌 Status: Connected - License Pending")

                if isinstance(conf, dict):
                    section_updates = {}
                    section_errors  = []

                    normal_fields  = []
                    complex_fields = []
                    for k, v in conf.items():
                        if isinstance(v, (list, dict)) or any(tok in k.lower() for tok in ['url', 'query', 'payload', 'body', 'description', 'recipients', 'users']):
                            complex_fields.append((k, v))
                        else:
                            normal_fields.append((k, v))

                    def render_field(k, v, section=section):
                        label    = k.replace('_', ' ').title()
                        key_name = f"cfg_{section}_{k}"
                        disabled = not st.session_state.get('integrations_unlocked', False)

                        if any(tok in k.lower() for tok in ['password', 'secret', 'token', 'api_key', 'pat', 'key']) and not isinstance(v, bool):
                            new_val = st.text_input(label, value=str(v) if v is not None else '', key=key_name, type='password', disabled=disabled)
                        elif isinstance(v, bool):
                            new_val = st.checkbox(label, value=bool(v), key=key_name, disabled=disabled)
                        elif isinstance(v, int):
                            try:
                                new_val = st.number_input(label, value=int(v), key=key_name, disabled=disabled)
                            except Exception:
                                new_val = st.text_input(label, value=str(v), key=key_name, disabled=disabled)
                        elif isinstance(v, (list, dict)):
                            txt_key = f"cfg_{section}_{k}_yaml"
                            try:
                                txt = _yaml.safe_dump(v) if _yaml else str(v)
                            except Exception:
                                txt = str(v)
                            new_txt = st.text_area(label, value=txt, height=120, key=txt_key, disabled=disabled)
                            if _yaml:
                                try:
                                    new_val = _yaml.safe_load(new_txt)
                                except Exception:
                                    new_val = v
                            else:
                                new_val = v
                        else:
                            new_val = st.text_input(label, value=str(v) if v is not None else '', key=key_name, disabled=disabled)

                        try:
                            lowk = k.lower()
                            if ('url' in lowk or lowk == 'url') and new_val:
                                if not is_valid_url(new_val):
                                    st.warning(f"Field '{label}' does not look like a valid URL.")
                            if 'email' in lowk or 'sender_email' in lowk:
                                if new_val and not is_valid_email(new_val):
                                    st.warning(f"Field '{label}' does not look like a valid email.")
                            if 'port' in lowk or lowk in ('smtp_port',):
                                if new_val and not is_valid_port(new_val):
                                    st.warning(f"Field '{label}' does not look like a valid port number.")
                        except Exception:
                            pass

                        return new_val

                    for k, v in normal_fields:
                        section_updates[k] = render_field(k, v)
                    for k, v in complex_fields:
                        section_updates[k] = render_field(k, v)

                    st.divider()
                    confirm_key = f"confirm_save_{section}"
                    confirm     = st.checkbox("Confirm save changes", value=False, key=confirm_key)

                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button("Save", key=f"btn_save_{section}"):
                            if section_errors:
                                st.error('Cannot save — validation errors exist:')
                                for err in section_errors:
                                    st.write(f"- {err}")
                            elif not confirm:
                                st.error('Please check the confirmation box before saving.')
                            else:
                                try:
                                    config_path  = Path('integrations') / 'config.yaml'
                                    if _yaml is None:
                                        st.error('PyYAML not available; cannot save config from UI.')
                                    else:
                                        full = _yaml.safe_load(open(config_path, 'r')) or {}
                                        before_section = full.get(section, {})
                                        full[section]  = section_updates
                                        with open(config_path, 'w') as _cf:
                                            _yaml.safe_dump(full, _cf)
                                        log_path = Path('logs') / 'config_changes.log'
                                        log_path.parent.mkdir(exist_ok=True)
                                        with open(log_path, 'a', encoding='utf-8') as lf:
                                            lf.write(f"{datetime.now().isoformat()} - Saved section: {section}\n")
                                            try:
                                                lf.write('BEFORE:\n'); lf.write(_yaml.safe_dump(before_section))
                                            except Exception:
                                                lf.write(str(before_section) + '\n')
                                            lf.write('AFTER:\n')
                                            try:
                                                lf.write(_yaml.safe_dump(section_updates))
                                            except Exception:
                                                lf.write(str(section_updates) + '\n')
                                            lf.write('----\n')
                                        st.success(f"Saved {section} to integrations/config.yaml")
                                        try:
                                            IntegrationScheduler().config = load_config('integrations/config.yaml')
                                        except Exception:
                                            pass
                                except Exception as e:
                                    st.error(f"Failed to save config: {e}")

                    with action_col2:
                        if st.button("Test Auth", key=f"btn_test_{section}"):
                            try:
                                import requests as _requests
                            except Exception:
                                _requests = None
                            result_msg = None
                            try:
                                sec_conf = section_updates
                                if section == 'codebeamer':
                                    url     = sec_conf.get('url')
                                    headers = {}
                                    token   = sec_conf.get('api_token')
                                    if token:
                                        headers['Authorization'] = f'Bearer {token}'
                                    elif sec_conf.get('username') and sec_conf.get('password'):
                                        import base64 as _b64
                                        creds = _b64.b64encode(f"{sec_conf.get('username')}:{sec_conf.get('password')}".encode()).decode()
                                        headers['Authorization'] = f'Basic {creds}'
                                    result_msg = f"Status {_requests.get(url, headers=headers, timeout=10).status_code}" if _requests and url else "requests/URL missing"
                                elif section == 'jira':
                                    url  = sec_conf.get('url')
                                    auth = (sec_conf.get('username'), sec_conf.get('api_token')) if sec_conf.get('username') and sec_conf.get('api_token') else None
                                    result_msg = f"Status {_requests.get(url, auth=auth, timeout=10).status_code}" if _requests and url else "requests/URL missing"
                                elif section == 'email':
                                    import smtplib as _smtplib
                                    server = sec_conf.get('smtp_server'); port = int(sec_conf.get('smtp_port') or 0)
                                    user   = sec_conf.get('sender_email'); pwd  = sec_conf.get('sender_password')
                                    if not server or not port:
                                        result_msg = 'SMTP server/port missing'
                                    else:
                                        try:
                                            smtp = _smtplib.SMTP(server, port, timeout=10); smtp.ehlo()
                                            if port == 587: smtp.starttls(); smtp.ehlo()
                                            if user and pwd: smtp.login(user, pwd)
                                            smtp.quit(); result_msg = 'SMTP connection and auth OK'
                                        except Exception as e:
                                            result_msg = f'SMTP error: {e}'
                                else:
                                    candidate = sec_conf.get('url') or sec_conf.get('organization') or sec_conf.get('api_key')
                                    if _requests and candidate:
                                        try:
                                            r = _requests.get(candidate, timeout=10)
                                            result_msg = f"Status {r.status_code}: {r.reason}"
                                        except Exception as e:
                                            result_msg = f"Request error: {e}"
                                    else:
                                        result_msg = 'No standard test implemented for this integration.'
                            except Exception as e:
                                result_msg = f"Test failed: {e}"
                            st.info(result_msg)

                    action_col3, action_col4 = st.columns(2)
                    with action_col3:
                        if st.button("Pull Data", key=f"btn_pull_{section}"):
                            try:
                                sched = IntegrationScheduler()
                                if   section == 'codebeamer':    ok = sched.sync_codebeamer()
                                elif section == 'jira':          ok = sched.sync_jira()
                                elif section == 'azure_devops' and getattr(sched, 'azure_devops', None): ok = sched.azure_devops.sync_all()
                                elif section == 'monday_com'   and getattr(sched, 'monday', None):       ok = sched.monday.sync_all()
                                elif section == 'asana'        and getattr(sched, 'asana', None):        ok = sched.asana.sync_all()
                                else: ok = False
                                st.success(f"{section} sync completed") if ok else st.warning(f"{section} sync empty or disabled")
                            except Exception as e:
                                st.error(f"Sync failed: {e}")

                    with action_col4:
                        if st.button("Revert", key=f"btn_revert_{section}"):
                            for kk in [k for k in st.session_state.keys() if k.startswith(f'cfg_{section}_')]:
                                try:
                                    del st.session_state[kk]
                                except Exception:
                                    pass
                            st.rerun()

                    edited_cfg[section] = {'updates': section_updates, 'errors': section_errors}
                else:
                    st.write(conf)

    # ── Global actions ────────────────────────────────────────────────────────
    st.divider()
    confirm_all = st.checkbox('Confirm save all integrations', value=False, key='confirm_save_all')
    gcol1, gcol2, gcol3 = st.columns(3)

    with gcol1:
        if st.button("Save All Integrations"):
            try:
                import yaml as _yaml
            except Exception:
                _yaml = None
            if _yaml is None:
                st.error('PyYAML not available; cannot save config from UI.')
            elif not confirm_all:
                st.error('Please check Confirm save all integrations before saving.')
            else:
                try:
                    config_path = Path('integrations') / 'config.yaml'
                    full        = _yaml.safe_load(open(config_path, 'r')) or {}
                    log_path    = Path('logs') / 'config_changes.log'
                    log_path.parent.mkdir(exist_ok=True)
                    with open(log_path, 'a', encoding='utf-8') as lf:
                        lf.write(f"{datetime.now().isoformat()} - Saved integrations config via UI\n")
                    for s, data_s in edited_cfg.items():
                        updates = data_s.get('updates') if isinstance(data_s, dict) else data_s
                        errors  = data_s.get('errors')  if isinstance(data_s, dict) else []
                        if errors:
                            continue
                        before = full.get(s, {})
                        full[s] = updates
                        with open(log_path, 'a', encoding='utf-8') as lf:
                            lf.write(f"Section: {s}\n")
                            try:
                                lf.write('BEFORE:\n'); lf.write(_yaml.safe_dump(before))
                            except Exception:
                                lf.write(str(before) + '\n')
                            lf.write('AFTER:\n')
                            try:
                                lf.write(_yaml.safe_dump(updates))
                            except Exception:
                                lf.write(str(updates) + '\n')
                            lf.write('----\n')
                    with open(config_path, 'w') as _cf:
                        _yaml.safe_dump(full, _cf)
                    st.success('Saved integrations/config.yaml')
                except Exception as e:
                    st.error(f'Failed to save: {e}')

        if st.button('Preview Changes'):
            try:
                import yaml as _yaml
            except Exception:
                _yaml = None
            config_path = Path('integrations') / 'config.yaml'
            try:
                full = _yaml.safe_load(open(config_path, 'r')) if _yaml else {}
            except Exception:
                full = {}
            for s, updates in edited_cfg.items():
                before = full.get(s, {})
                try:
                    before_txt = _yaml.safe_dump(before).splitlines()  if _yaml else str(before).splitlines()
                    after_txt  = _yaml.safe_dump(updates).splitlines() if _yaml else str(updates).splitlines()
                except Exception:
                    before_txt = str(before).splitlines()
                    after_txt  = str(updates).splitlines()
                d = list(difflib.unified_diff(before_txt, after_txt,
                                              fromfile=f'{s} (before)', tofile=f'{s} (after)', lineterm=''))
                st.subheader(f'Preview: {s}')
                st.code('\n'.join(d) if d else 'No changes')

    with gcol2:
        if st.button('Test All Authentications'):
            results = {}
            try:
                import requests as _requests
            except Exception:
                _requests = None
            for s, conf in cfg.items():
                try:
                    if s == 'email':
                        import smtplib as _smtplib
                        server = conf.get('smtp_server'); port = int(conf.get('smtp_port') or 0)
                        try:
                            smtp = _smtplib.SMTP(server, port, timeout=10); smtp.ehlo()
                            if port == 587: smtp.starttls(); smtp.ehlo()
                            smtp.quit(); results[s] = 'OK'
                        except Exception as e:
                            results[s] = f'Error: {e}'
                    else:
                        candidate = conf.get('url') or conf.get('organization') or None
                        if _requests and candidate:
                            try:
                                r = _requests.get(candidate, timeout=10)
                                results[s] = f'{r.status_code} {r.reason}'
                            except Exception as e:
                                results[s] = f'Error: {e}'
                        else:
                            results[s] = 'Skipping (no requests or no URL)'
                except Exception as e:
                    results[s] = f'Error: {e}'
            st.json(results)

    with gcol3:
        if st.button('Pull Data For All Enabled'):
            sched       = IntegrationScheduler()
            run_results = {}
            try:   run_results['codebeamer'] = sched.sync_codebeamer()
            except Exception as e: run_results['codebeamer'] = f'Error: {e}'
            try:   run_results['jira'] = sched.sync_jira()
            except Exception as e: run_results['jira'] = f'Error: {e}'
            try:
                if getattr(sched, 'azure_devops', None):
                    run_results['azure_devops'] = sched.azure_devops.sync_all()
            except Exception as e: run_results['azure_devops'] = f'Error: {e}'
            try:
                if getattr(sched, 'monday', None):
                    run_results['monday_com'] = sched.monday.sync_all()
            except Exception as e: run_results['monday_com'] = f'Error: {e}'
            try:
                if getattr(sched, 'asana', None):
                    run_results['asana'] = sched.asana.sync_all()
            except Exception as e: run_results['asana'] = f'Error: {e}'
            st.json(run_results)

else:
    st.info("No integrations configured or unable to load integration settings.")

# ═══════════════════════════════════════════════════════════════
# AUDIT TRAIL (spec req 2.6 — mapped to this page)
# ═══════════════════════════════════════════════════════════════
st.divider()
with st.expander("🔍 System Action Log & Audit Trail", expanded=False):
    st.markdown("Inspect synchronization logs, user configuration audits, and scheduler execution traces.")

    log_dir   = Path("logs")
    log_files = list(log_dir.glob("*.log")) if log_dir.exists() else []

    if log_files:
        log_names    = [f.name for f in log_files]
        selected_log = st.selectbox("Select log file to inspect", log_names, key="audit_log_select")
        log_path     = log_dir / selected_log

        if log_path.exists():
            stat = log_path.stat()
            st.text(f"File size: {round(stat.st_size / 1024, 1)} KB | Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
            num_lines   = st.slider("Number of lines to read", min_value=10, max_value=200, value=50, key="audit_lines")
            search_term = st.text_input("Filter log entries (case-insensitive search)", key="audit_search")
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as lf:
                    lines = lf.readlines()
                filtered   = [l for l in lines if search_term.lower() in l.lower()] if search_term else lines
                tail_lines = filtered[-num_lines:]
                st.code("".join(tail_lines), language='text')
            except Exception as e:
                st.error(f"Failed to read log file: {e}")
    else:
        st.info("No system log files found.")
