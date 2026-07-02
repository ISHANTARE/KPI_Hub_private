"""
lib/scenario_engine.py
----------------------
Simulation engine for What-If scenario analysis.
Allows modeling resource transfers between projects and calculating their projected impacts.
"""

import pandas as pd
from typing import Dict, Any, List
from lib.kpi_engine import calculate_kpis

def simulate_resource_move(
    data: Dict[str, pd.DataFrame],
    source_project: str,
    target_project: str,
    resources_to_move: List[str],
    duration_weeks: int
) -> Dict[str, Any]:
    """
    Simulates moving resources from a source project to a target project.
    Does NOT mutate the original data.
    
    Returns a dictionary summarizing the impact:
      - original_kpis: dict
      - simulated_kpis: dict
      - original_util: float
      - simulated_util: float
      - cost_delta: float
      - moved_count: int
    """
    # Create a deep copy of the data dictionary (copying DataFrames)
    sim_data = {k: v.copy() if isinstance(v, pd.DataFrame) else v for k, v in data.items()}
    
    # Get resource allocation DataFrame
    res_df = sim_data.get('resources', pd.DataFrame())
    
    original_kpis = calculate_kpis(data)
    
    if res_df.empty or not resources_to_move:
        return {
            'original_kpis': original_kpis,
            'simulated_kpis': original_kpis,
            'original_util': original_kpis.get('resource_util', 0.0),
            'simulated_util': original_kpis.get('resource_util', 0.0),
            'cost_delta': 0.0,
            'moved_count': 0
        }
        
    # Perform simulation by updating PROJECT_ID for the matching resource rows
    mask = (res_df['PROJECT_ID'] == source_project) & (res_df['TEAM_MEMBER'].isin(resources_to_move))
    moved_count = mask.sum()
    
    if moved_count > 0:
        res_df.loc[mask, 'PROJECT_ID'] = target_project
        
    sim_data['resources'] = res_df
    simulated_kpis = calculate_kpis(sim_data)
    
    # Calculate average utilization changes
    def parse_util(val):
        try:
            s = str(val).replace('%', '').replace('>', '')
            if '(' in s:
                s = s.split('(')[1].replace(')', '')
            return float(s)
        except:
            return 100.0
            
    orig_res = data.get('resources', pd.DataFrame())
    orig_util = orig_res['UTILIZATION_PCT'].apply(parse_util).mean() if not orig_res.empty else 0.0
    sim_util = res_df['UTILIZATION_PCT'].apply(parse_util).mean()
    
    if pd.isna(orig_util): orig_util = 0.0
    if pd.isna(sim_util): sim_util = 0.0
    
    # Estimate cost impact
    cost_rates_df = data.get('cost_rates', pd.DataFrame())
    rate_map = dict(zip(cost_rates_df['ROLE'].str.lower(), cost_rates_df['COST_RATE_MONTHLY'])) if not cost_rates_df.empty else {}
    
    cost_delta = 0.0
    for tm in resources_to_move:
        tm_rows = orig_res[(orig_res['TEAM_MEMBER'] == tm) & (orig_res['PROJECT_ID'] == source_project)]
        for _, row in tm_rows.iterrows():
            role = str(row.get('ROLE', '')).lower()
            monthly_rate = rate_map.get(role, 5000.0)
            cost_delta += (monthly_rate / 4) * duration_weeks
            
    return {
        'original_kpis': original_kpis,
        'simulated_kpis': simulated_kpis,
        'original_util': orig_util,
        'simulated_util': sim_util,
        'cost_delta': cost_delta,
        'moved_count': moved_count
    }
