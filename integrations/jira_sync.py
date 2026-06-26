"""
Jira Integration Module
Syncs data from Jira to KPI Hub CSV files

Features:
- Sync issues, sprints, epics
- Map Jira projects to KPI projects
- Custom JQL queries for flexible filtering
- Automatic scheduled syncing
"""

try:
    import requests
except Exception:
    requests = None

try:
    import pandas as pd
except Exception:
    pd = None
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional
try:
    import yaml
except Exception:
    yaml = None
from base64 import b64encode
try:
    from requests.auth import HTTPBasicAuth
except Exception:
    HTTPBasicAuth = None
from integrations.config_helper import load_config
import os
try:
    from requests.adapters import HTTPAdapter
except Exception:
    HTTPAdapter = None
try:
    from urllib3.util.retry import Retry
except Exception:
    Retry = None

logger = logging.getLogger(__name__)


class JiraSync:
    """Sync data from Jira to KPI Hub"""
    
    def __init__(self, config_path: str = "integrations/config.yaml"):
        """Initialize Jira sync with config"""
        # Load config with environment overrides
        self.config = load_config(config_path)
        self.jira_config = self.config.get('jira', {})
        self.base_url = self.jira_config.get('url')
        self.username = self.jira_config.get('username')
        self.api_token = self.jira_config.get('api_token')
        self.data_dir = Path("data")
        # Prepare a requests session with retries (if requests available)
        if requests is not None and HTTPAdapter is not None and Retry is not None:
            self.session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retries)
            self.session.mount('https://', adapter)
            self.session.mount('http://', adapter)
        elif requests is not None:
            # requests available but retry tools are missing; use a basic session
            self.session = requests.Session()
        else:
            self.session = None
        self._setup_logging()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _setup_logging(self):
        """Setup logging for sync activities"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(log_dir / "jira_sync.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    
    def _get_headers(self) -> Dict:
        """Get authentication headers for Jira API"""
        headers = {'Content-Type': 'application/json'}
        # For Jira prefer using requests' HTTPBasicAuth when making requests
        return headers
    
    def sync_issues(self, project_key: str, jql_query: Optional[str] = None) -> bool:
        """Sync issues from Jira using JQL query"""
        try:
            logger.info(f"Syncing issues for project {project_key}")
            
            if not jql_query:
                jql_query = f"project = {project_key} AND status in (Open, 'In Progress')"
            
            # Jira API endpoint for issues
            url = f"{self.base_url}/rest/api/3/search"
            
            params = {
                'jql': jql_query,
                'maxResults': 100,
                'fields': ['key', 'summary', 'status', 'priority', 'assignee', 
                          'created', 'updated', 'issuetype', 'labels']
            }
            
            if self.session is None:
                logger.warning("requests package not available; skipping Jira issues sync")
                return False
            auth = HTTPBasicAuth(self.username, self.api_token) if self.username and self.api_token else None
            response = self.session.get(url, headers=self._get_headers(), params=params, timeout=30, auth=auth)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            # Pagination
            total = data.get('total', len(issues))
            start_at = data.get('startAt', 0) + len(issues)
            while start_at < total:
                params['startAt'] = start_at
                resp2 = self.session.get(url, headers=self._get_headers(), params=params, timeout=30, auth=auth)
                resp2.raise_for_status()
                page = resp2.json().get('issues', [])
                issues.extend(page)
                start_at += len(page)
            
            # Transform to KPI format
            df_data = []
            for issue in issues:
                fields = issue.get('fields', {})
                df_data.append({
                    'ISSUE_ID': issue.get('key'),
                    'PROJECT_ID': project_key,
                    'ISSUE_TITLE': fields.get('summary'),
                    'STATUS': fields.get('status', {}).get('name'),
                    'SEVERITY': fields.get('priority', {}).get('name'),
                    'CREATED_DATE': fields.get('created'),
                    'ASSIGNED_TO': fields.get('assignee', {}).get('displayName'),
                    'ISSUE_TYPE': fields.get('issuetype', {}).get('name'),
                })
            
            # Save to CSV
            output_path = self.data_dir / "projects" / "issues.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if pd is not None:
                df = pd.DataFrame(df_data)
                df.to_csv(output_path, index=False)
            else:
                if df_data:
                    keys = list(df_data[0].keys())
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(','.join(keys) + '\n')
                        for r in df_data:
                            f.write(','.join([str(r.get(k, '')) for k in keys]) + '\n')
            
            logger.info(f"Successfully synced {len(df_data)} issues")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync issues: {e}")
            return False
    
    def sync_sprints(self, project_key: str) -> bool:
        """Sync sprint data from Jira"""
        try:
            logger.info(f"Syncing sprints for project {project_key}")
            
            # Jira API endpoint for sprints
            url = f"{self.base_url}/rest/agile/1.0/board"
            
            params = {'projectKey': project_key}
            
            if self.session is None:
                logger.warning("requests package not available; skipping Jira sprints sync")
                return False
            auth = HTTPBasicAuth(self.username, self.api_token) if self.username and self.api_token else None
            response = self.session.get(url, headers=self._get_headers(), params=params, timeout=30, auth=auth)
            response.raise_for_status()
            
            boards = response.json().get('values', [])
            if not boards:
                logger.warning(f"No agile boards found for {project_key}")
                return False
            
            board_id = boards[0]['id']
            
            # Get sprints
            sprints_url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint"
            auth = HTTPBasicAuth(self.username, self.api_token) if self.username and self.api_token else None
            sprints_response = self.session.get(sprints_url,
                                                headers=self._get_headers(),
                                                timeout=30,
                                                auth=auth)
            sprints_response.raise_for_status()
            
            sprints = sprints_response.json().get('values', [])
            
            # Transform to KPI format
            df_data = []
            for sprint in sprints:
                df_data.append({
                    'SPRINT_ID': sprint.get('id'),
                    'PROJECT_ID': project_key,
                    'SPRINT_NAME': sprint.get('name'),
                    'STATUS': sprint.get('state'),
                    'START_DATE': sprint.get('startDate'),
                    'END_DATE': sprint.get('endDate'),
                    'COMPLETION_PCT': 0,  # Calculated separately
                })
            
            # Save to CSV
            output_path = self.data_dir / "projects" / "milestones.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if pd is not None:
                df = pd.DataFrame(df_data)
                df.to_csv(output_path, index=False)
            else:
                if df_data:
                    keys = list(df_data[0].keys())
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(','.join(keys) + '\n')
                        for r in df_data:
                            f.write(','.join([str(r.get(k, '')) for k in keys]) + '\n')
            
            logger.info(f"Successfully synced {len(df_data)} sprints")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync sprints: {e}")
            return False
    
    def sync_epics(self, project_key: str) -> bool:
        """Sync epic data from Jira"""
        try:
            logger.info(f"Syncing epics for project {project_key}")
            
            # Jira API endpoint for epics
            jql_query = f"project = {project_key} AND issuetype = Epic"
            url = f"{self.base_url}/rest/api/3/search"
            
            params = {
                'jql': jql_query,
                'maxResults': 100,
                'fields': ['key', 'summary', 'status', 'created']
            }
            
            if self.session is None:
                logger.warning("requests package not available; skipping Jira epics sync")
                return False
            auth = HTTPBasicAuth(self.username, self.api_token) if self.username and self.api_token else None
            response = self.session.get(url, headers=self._get_headers(), params=params, timeout=30, auth=auth)
            response.raise_for_status()
            
            data = response.json()
            epics = data.get('issues', [])
            # Pagination for epics
            total = data.get('total', len(epics))
            start_at = data.get('startAt', 0) + len(epics)
            while start_at < total:
                params['startAt'] = start_at
                resp2 = self.session.get(url, headers=self._get_headers(), params=params, timeout=30, auth=auth)
                resp2.raise_for_status()
                page = resp2.json().get('issues', [])
                epics.extend(page)
                start_at += len(page)
            
            # Transform to KPI format
            df_data = []
            for epic in epics:
                fields = epic.get('fields', {})
                df_data.append({
                    'EPIC_ID': epic.get('key'),
                    'PROJECT_ID': project_key,
                    'EPIC_NAME': fields.get('summary'),
                    'STATUS': fields.get('status', {}).get('name'),
                    'CREATED_DATE': fields.get('created'),
                })
            
            # Save epics to CSV (map to escalations.csv)
            df = pd.DataFrame(df_data)
            output_path = self.data_dir / "projects" / "escalations.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)

            logger.info(f"Successfully synced {len(df_data)} epics")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync epics: {e}")
            return False

    def create_issue(self, project_key: str, summary: str, description: str, issue_type: str = "Task", mock: bool = True) -> Optional[str]:
        """Create a new issue in Jira. Mocks creation by default."""
        try:
            logger.info(f"{'Mocking' if mock else 'Attempting'} issue creation: {summary} in {project_key}")
            
            # API endpoint for creating issue
            url = f"{self.base_url}/rest/api/3/issue"
            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}]
                            }
                        ]
                    },
                    "issuetype": {"name": issue_type}
                }
            }

            if mock:
                import uuid
                mock_id = f"{project_key}-{str(uuid.uuid4().int)[:4]}"
                logger.info(f"Mock Jira issue created successfully: {mock_id}")
                return mock_id
            
            # Actual implementation (currently bypassed by mock flag)
            # if self.session is None:
            #     logger.warning("requests package not available; skipping Jira issue creation")
            #     return None
            # auth = HTTPBasicAuth(self.username, self.api_token) if self.username and self.api_token else None
            # response = self.session.post(url, headers=self._get_headers(), json=payload, timeout=30, auth=auth)
            # response.raise_for_status()
            # return response.json().get('key')
            
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None

    def sync_all(self) -> bool:
        """Sync all data from Jira"""
        if not self.jira_config.get('enabled'):
            logger.info("Jira integration is disabled")
            return False
        
        success = True
        
        for project in self.jira_config.get('projects', []):
            jira_key = project.get('jira_key')
            jql_query = project.get('jql_query')
            sync_opts = self.jira_config.get('sync_options', {})
            
            if sync_opts.get('issues'):
                success &= self.sync_issues(jira_key, jql_query)
            
            if sync_opts.get('sprints'):
                success &= self.sync_sprints(jira_key)
            
            if sync_opts.get('epics'):
                success &= self.sync_epics(jira_key)
        
        return success


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync = JiraSync()
    sync.sync_all()
