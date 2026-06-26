"""
Codebeamer Integration Module
Syncs data from Codebeamer to KPI Hub CSV files

Features:
- Sync requirements, test cases, defects
- Map Codebeamer projects to KPI projects
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
import base64
from typing import Dict, List, Optional
try:
    import yaml
except Exception:
    yaml = None
import os
from integrations.config_helper import load_config

logger = logging.getLogger(__name__)


class CodebeamerSync:
    """Sync data from Codebeamer to KPI Hub"""
    
    def __init__(self, config_path: str = "integrations/config.yaml"):
        """Initialize Codebeamer sync with config"""
        # Load config with environment overrides
        self.config = load_config(config_path)
        self.cb_config = self.config.get('codebeamer', {})
        self.base_url = self.cb_config.get('url')
        # api_token may come from env var via config_helper
        self.api_token = self.cb_config.get('api_token')
        self.username = self.cb_config.get('username')
        self.password = self.cb_config.get('password')
        self.data_dir = Path("data")
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
        
        handler = logging.FileHandler(log_dir / "codebeamer_sync.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    
    def _get_headers(self) -> Dict:
        """Get authentication headers for Codebeamer API"""
        headers = {'Content-Type': 'application/json'}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
            return headers

        # Fallback to username/password
        username = self.username or self.cb_config.get('username')
        password = self.password or self.cb_config.get('password')
        if username and password:
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'

        return headers
    
    def sync_requirements(self, project_id: str) -> bool:
        """Sync requirements from Codebeamer"""
        try:
            if requests is None:
                logger.warning("requests package not available; skipping Codebeamer requirements sync")
                return False
            logger.info(f"Syncing requirements for project {project_id}")
            
            # Codebeamer API endpoint for requirements
            url = f"{self.base_url}/api/v3/projects/{project_id}/requirements"
            
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            requirements = response.json().get('items', [])
            
            # Transform to KPI format
            df_data = []
            for req in requirements:
                df_data.append({
                    'REQUIREMENT_ID': req.get('id'),
                    'PROJECT_ID': project_id,
                    'REQUIREMENT_TEXT': req.get('name'),
                    'CATEGORY': req.get('type'),
                    'STATUS': req.get('status'),
                    'PRIORITY': req.get('priority'),
                    'APPROVED_DATE': req.get('created'),
                })
            
            # Save to CSV
            output_path = self.data_dir / "metrics" / "requirements.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if pd is not None:
                df = pd.DataFrame(df_data)
                df.to_csv(output_path, index=False)
            else:
                # Fallback CSV writer
                if df_data:
                    keys = list(df_data[0].keys())
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(','.join(keys) + '\n')
                        for r in df_data:
                            f.write(','.join([str(r.get(k, '')) for k in keys]) + '\n')
            
            logger.info(f"Successfully synced {len(df_data)} requirements")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync requirements: {e}")
            return False
    
    def sync_defects(self, project_id: str) -> bool:
        """Sync defects/issues from Codebeamer"""
        try:
            if requests is None:
                logger.warning("requests package not available; skipping Codebeamer defects sync")
                return False
            logger.info(f"Syncing defects for project {project_id}")
            
            # Codebeamer API endpoint for defects
            url = f"{self.base_url}/api/v3/projects/{project_id}/defects"
            
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            defects = response.json().get('items', [])
            
            # Transform to KPI format
            df_data = []
            for defect in defects:
                df_data.append({
                    'DEFECT_ID': defect.get('id'),
                    'PROJECT_ID': project_id,
                    'TITLE': defect.get('name'),
                    'SEVERITY': defect.get('severity'),
                    'STATUS': defect.get('status'),
                    'FOUND_DATE': defect.get('created'),
                    'ASSIGNED_TO': defect.get('assignee'),
                })
            
            # Save to CSV
            output_path = self.data_dir / "metrics" / "defects.csv"
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
            
            logger.info(f"Successfully synced {len(df_data)} defects")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync defects: {e}")
            return False
    
    def sync_test_cases(self, project_id: str) -> bool:
        """Sync test cases from Codebeamer"""
        try:
            if requests is None:
                logger.warning("requests package not available; skipping Codebeamer test cases sync")
                return False
            logger.info(f"Syncing test cases for project {project_id}")
            
            # Codebeamer API endpoint for test cases
            url = f"{self.base_url}/api/v3/projects/{project_id}/test-cases"
            
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            test_cases = response.json().get('items', [])
            
            # Transform to KPI format
            df_data = []
            for test in test_cases:
                df_data.append({
                    'TEST_ID': test.get('id'),
                    'PROJECT_ID': project_id,
                    'TEST_CASE_NAME': test.get('name'),
                    'STATUS': test.get('status'),
                    'EXECUTION_DATE': test.get('executed_date'),
                    'COMPONENT': test.get('component'),
                })
            
            # Save to CSV
            output_path = self.data_dir / "metrics" / "test_execution.csv"
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
            
            logger.info(f"Successfully synced {len(df_data)} test cases")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync test cases: {e}")
            return False
    
    def sync_all(self) -> bool:
        """Sync all data from Codebeamer"""
        if not self.cb_config.get('enabled'):
            logger.info("Codebeamer integration is disabled")
            return False
        
        success = True
        
        for project in self.cb_config.get('projects', []):
            project_id = project.get('codebeamer_id')
            sync_opts = self.cb_config.get('sync_options', {})
            
            if sync_opts.get('requirements'):
                success &= self.sync_requirements(project_id)
            
            if sync_opts.get('defects'):
                success &= self.sync_defects(project_id)
            
            if sync_opts.get('test_cases'):
                success &= self.sync_test_cases(project_id)
        
        return success


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync = CodebeamerSync()
    sync.sync_all()
