"""
lib/ai_validator.py
-------------------
AI output validation layer for parsing and verifying structured LLM responses
before writing them to the operational database.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

def extract_json_from_llm_output(text: str) -> Optional[Any]:
    """Extract and parse JSON objects or arrays from raw LLM output text."""
    if not text:
        return None
    try:
        # Direct parse attempt
        return json.loads(text)
    except Exception:
        pass

    # Extract markdown block or raw json matching
    try:
        match = re.search(r'```(?:json)?\s*([\[\{].*?[\]\}])\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        match_raw = re.search(r'([\[\{].*?[\]\}])', text, re.DOTALL)
        if match_raw:
            return json.loads(match_raw.group(1))
    except Exception as e:
        logger.warning(f"Failed to extract JSON from LLM output: {e}")
    
    return None

def validate_extracted_data(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """Validate that structured dictionary contains expected keys and non-null content."""
    if not isinstance(data, dict):
        return False
    for key in required_keys:
        if key not in data or data[key] is None:
            return False
    return True
