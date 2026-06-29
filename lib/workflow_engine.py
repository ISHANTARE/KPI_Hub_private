"""
lib/workflow_engine.py
-----------------------
ASPICE Process Gate Workflow Engine for KPI Hub.
Enforces state transitions (PLANNED -> IN_PROGRESS -> REVIEW -> COMPLETED)
and validates work product completion before advancing phases.
"""

import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "PLANNED": ["IN_PROGRESS"],
    "IN_PROGRESS": ["REVIEW", "PLANNED"],
    "REVIEW": ["COMPLETED", "IN_PROGRESS"],
    "COMPLETED": ["IN_PROGRESS"]  # Allowed if reopened
}

def validate_transition(current_state: str, new_state: str, item_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Validate whether a transition from current_state to new_state is permissible under ASPICE gates.
    Returns (is_valid, reason_message).
    """
    curr = current_state.upper() if current_state else "PLANNED"
    target = new_state.upper() if new_state else "PLANNED"

    if curr == target:
        return True, "No state change."

    allowed = ALLOWED_TRANSITIONS.get(curr, [])
    if target not in allowed:
        return False, f"Invalid ASPICE transition: Cannot move from {curr} directly to {target}. Allowed: {', '.join(allowed)}."

    # Gate validation when moving to COMPLETED
    if target == "COMPLETED" and item_data:
        open_findings = item_data.get("OPEN_FINDINGS", 0)
        try:
            if int(open_findings) > 0:
                return False, f"Gate Violation: Cannot complete item with {open_findings} open quality findings."
        except (ValueError, TypeError):
            pass

    return True, f"Transition from {curr} to {target} approved."
