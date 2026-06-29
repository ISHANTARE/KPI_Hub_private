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

# Standard domain knowledge catalog for offline / fallback lookup
STANDARDS_CATALOG: Dict[str, Dict[str, str]] = {
    "ASPICE": {
        "SYS.1": "SYS.1 Requirements Elicitation: Gather, analyze, and baseline customer requirements.",
        "SYS.2": "SYS.2 System Requirements Analysis: Specify functional and non-functional system requirements with bidirectional traceability.",
        "SYS.3": "SYS.3 System Architectural Design: Establish system architecture allocating requirements to system elements.",
        "SWE.1": "SWE.1 Software Requirements Analysis: Specify software requirements derived from system design.",
        "SWE.6": "SWE.6 Software Qualification Test: Test software against requirements and verify functionality.",
    },
    "ISO 26262": {
        "ASIL A": "ASIL A: Lowest safety integrity level. Standard verification procedures.",
        "ASIL B": "ASIL B: Medium safety integrity level. Requires formal fault tree and hazard analysis.",
        "ASIL C": "ASIL C: High safety integrity level. Redundant monitoring and strict test coverage required.",
        "ASIL D": "ASIL D: Highest safety integrity level. Demands hardware redundancy and full ASIL D compliance metrics.",
    }
}

def search_knowledge_base(query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search the engineering knowledge base for query matches.
    Returns structured result objects with standard reference and description.
    """
    if not query:
        return []

    results = []
    clean_query = query.lower().strip()

    for std_name, topics in STANDARDS_CATALOG.items():
        if domain and domain.lower() not in std_name.lower():
            continue
        for code, desc in topics.items():
            code_lower = code.lower()
            desc_lower = desc.lower()
            if clean_query in code_lower or clean_query in desc_lower:
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
