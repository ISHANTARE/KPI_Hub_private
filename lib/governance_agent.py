import pandas as pd
from typing import Dict, List, Any

class GovernanceAnalyzer:
    """Analyzes data across requirements, issues, and test cases to identify governance gaps."""

    def analyze_traceability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-references requirements, issues, and tests.
        Returns a dictionary containing traceability scores and specific gaps.
        """
        results = {
            "score": 100,
            "gaps": [],
            "summary": {}
        }
        
        reqs = data.get('requirements')
        tests = data.get('tests')
        issues = data.get('issues')
        
        if reqs is None or reqs.empty:
            return results
            
        total_reqs = len(reqs)
        untested_reqs = 0
        unlinked_reqs = 0
        
        for _, req in reqs.iterrows():
            req_id = str(req.get('REQUIREMENT_ID', ''))
            trace_test = str(req.get('TRACE_TEST_CASE', 'N/A')).strip()
            trace_design = str(req.get('TRACE_DESIGN', 'N/A')).strip()
            status = str(req.get('STATUS', '')).upper()
            
            # Gap 1: Approved requirements without test cases
            if status == 'APPROVED' and (trace_test == 'N/A' or trace_test == ''):
                untested_reqs += 1
                results['gaps'].append({
                    "type": "Missing Test Validation",
                    "item": req_id,
                    "description": f"Requirement {req_id} ({req.get('REQUIREMENT_TEXT')[:30]}...) is APPROVED but has no linked test cases."
                })
                
            # Gap 2: Open requirements with no design/issue tracking
            if status == 'OPEN' and (trace_design == 'N/A' or trace_design == ''):
                unlinked_reqs += 1
                results['gaps'].append({
                    "type": "Untracked Requirement",
                    "item": req_id,
                    "description": f"Requirement {req_id} is OPEN but has no linked design or tracking ticket."
                })
                
        # Calculate scores
        penalty = (untested_reqs * 2) + (unlinked_reqs * 1)
        results['score'] = max(0, 100 - (penalty * 100 / max(1, total_reqs)))
        
        results['summary'] = {
            "total_requirements": total_reqs,
            "untested_approved": untested_reqs,
            "unlinked_open": unlinked_reqs
        }
        
        return results
