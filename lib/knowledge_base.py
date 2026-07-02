"""
lib/knowledge_base.py
---------------------
Knowledge base search engine for engineering standards, ASPICE process guidelines,
and lessons-learned query resolution.
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Retrieve standards dynamically from compliance profile
def search_knowledge_base(query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search the engineering knowledge base for query matches.
    Returns structured result objects with standard reference and description.
    """
    if not query:
        return []

    from lib.profile_loader import get_active_profile
    profile = get_active_profile()
    standards_catalog = profile.get("standards_catalog", {})

    results = []
    clean_query = query.lower().strip()

    for std_name, topics in standards_catalog.items():
        if domain and domain.lower() not in std_name.lower():
            continue
        std_name_lower = std_name.lower()
        for code, desc in topics.items():
            code_lower = code.lower()
            desc_lower = desc.lower()
            if clean_query in std_name_lower or clean_query in code_lower or clean_query in desc_lower:
                results.append({
                    "standard": std_name,
                    "code": code,
                    "summary": desc,
                    "relevance": "HIGH"
                })
            elif any(term in desc_lower for term in clean_query.split() if len(term) > 1):
                results.append({
                    "standard": std_name,
                    "code": code,
                    "summary": desc,
                    "relevance": "MEDIUM"
                })

    return results
