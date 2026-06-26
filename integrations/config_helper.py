"""
Configuration helper: loads `integrations/config.yaml` and applies environment variable overrides.

Environment variable conventions (examples):
- CODEBEAMER_URL, CODEBEAMER_TOKEN, CODEBEAMER_USERNAME, CODEBEAMER_PASSWORD
- JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
- AZURE_DEVOPS_ORG, AZURE_DEVOPS_PAT
"""
import os
try:
    import yaml
except Exception:
    yaml = None
from pathlib import Path
from typing import Dict


def load_config(config_path: str = "integrations/config.yaml") -> Dict:
    cfg = {}
    try:
        if yaml is not None:
            with open(config_path, 'r') as f:
                cfg = yaml.safe_load(f) or {}
        else:
            # PyYAML not installed; skip loading file and return empty config
            cfg = {}
    except FileNotFoundError:
        cfg = {}

    # Apply environment overrides for common integrations
    # Codebeamer
    cb = cfg.get('codebeamer', {})
    cb['url'] = os.getenv('CODEBEAMER_URL', cb.get('url'))
    cb['api_token'] = os.getenv('CODEBEAMER_TOKEN', cb.get('api_token'))
    cb['username'] = os.getenv('CODEBEAMER_USERNAME', cb.get('username'))
    cb['password'] = os.getenv('CODEBEAMER_PASSWORD', cb.get('password'))
    cfg['codebeamer'] = cb

    # Jira
    jira = cfg.get('jira', {})
    jira['url'] = os.getenv('JIRA_URL', jira.get('url'))
    jira['username'] = os.getenv('JIRA_USERNAME', jira.get('username'))
    jira['api_token'] = os.getenv('JIRA_API_TOKEN', jira.get('api_token'))
    cfg['jira'] = jira

    # Azure DevOps
    ad = cfg.get('azure_devops', {})
    ad['organization'] = os.getenv('AZURE_DEVOPS_ORG', ad.get('organization'))
    ad['pat_token'] = os.getenv('AZURE_DEVOPS_PAT', ad.get('pat_token'))
    cfg['azure_devops'] = ad

    # OpenAI
    openai_cfg = cfg.get('openai', {})
    openai_cfg['api_key'] = os.getenv('OPENAI_API_KEY', openai_cfg.get('api_key'))
    cfg['openai'] = openai_cfg

    return cfg
