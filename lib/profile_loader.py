"""
lib/profile_loader.py
---------------------
Loader for industry-specific compliance profiles (YAML).
Caches profile configurations dynamically to minimize disk I/O.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global cache for the active profile
_ACTIVE_PROFILE_CACHE = None
_LAST_CONFIGURED_PROFILE_NAME = None

def get_active_profile(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load and return the active compliance profile configuration dictionary.
    Falls back to 'automotive' on any error.
    """
    global _ACTIVE_PROFILE_CACHE, _LAST_CONFIGURED_PROFILE_NAME

    # 1. Load general configuration to find the active profile name
    config_path = Path("integrations/config.yaml")
    profile_name = "automotive"  # Default fallback

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
                profile_name = cfg.get("general", {}).get("compliance_profile", "automotive")
        except Exception as e:
            logger.warning(f"Failed to read compliance_profile from {config_path}: {e}")

    # Check cache validity
    if not force_reload and _ACTIVE_PROFILE_CACHE is not None and _LAST_CONFIGURED_PROFILE_NAME == profile_name:
        return _ACTIVE_PROFILE_CACHE

    # 2. Load the specific profile file
    profile_filename = f"{profile_name}.yaml"
    profile_path = Path("profiles") / profile_filename

    # Fallback checking
    if not profile_path.exists():
        logger.warning(f"Profile {profile_path} not found. Falling back to automotive.")
        profile_path = Path("profiles") / "automotive.yaml"
        profile_name = "automotive"

    profile_data = {}
    if profile_path.exists():
        try:
            with open(profile_path, "r") as f:
                profile_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load compliance profile {profile_path}: {e}")

    # 3. Apply default values if fields are missing in the loaded YAML
    default_profile = {
        "name": "Automotive (ASPICE & ISO 26262)",
        "labels": {
            "portfolio_health": "Portfolio Health Index (PHI)",
            "requirements": "ASPICE Requirement",
            "quality_verification": "Verification & Test Status",
            "critical_defects": "Critical Defects",
            "critical_risks": "Critical Risks"
        },
        "rules": {
            "resource_overallocation_penalties": {
                "Critical": 3.0,
                "Default": 1.0,
                "Integration": 2.0,
                "Safety": 4.0,
                "Testing": 1.5
            },
            "traceability_severity_weights": {
                "Communication": 2.0,
                "Control": 3.5,
                "Documentation": 1.0,
                "Durability": 2.0,
                "Electrical": 3.5,
                "Mechanical": 3.0,
                "Motor": 3.0,
                "Reliability": 2.0,
                "Safety": 5.0,
                "Software": 4.0,
                "System": 4.0,
                "Thermal": 3.0
            }
        },
        "standards_catalog": {}
    }

    # Deep merge labels and rules with defaults to guarantee structure completeness
    merged_data = default_profile.copy()
    if profile_data:
        merged_data["name"] = profile_data.get("name", default_profile["name"])
        merged_data["labels"] = {**default_profile["labels"], **profile_data.get("labels", {})}
        
        default_rules = default_profile["rules"]
        loaded_rules = profile_data.get("rules", {})
        merged_data["rules"] = {
            "resource_overallocation_penalties": {
                **default_rules["resource_overallocation_penalties"],
                **loaded_rules.get("resource_overallocation_penalties", {})
            },
            "traceability_severity_weights": {
                **default_rules["traceability_severity_weights"],
                **loaded_rules.get("traceability_severity_weights", {})
            }
        }
        merged_data["standards_catalog"] = profile_data.get("standards_catalog", default_profile["standards_catalog"])

    # Update cache
    _ACTIVE_PROFILE_CACHE = merged_data
    _LAST_CONFIGURED_PROFILE_NAME = profile_name

    return _ACTIVE_PROFILE_CACHE
