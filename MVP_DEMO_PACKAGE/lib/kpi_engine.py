"""KPI calculation engine for MVP"""
import pandas as pd
import numpy as np


def calculate_portfolio_kpis(projects_df: pd.DataFrame, tests_df: pd.DataFrame, defects_df: pd.DataFrame) -> dict:
    """Calculate portfolio-level KPIs"""
    
    # Portfolio Health Score (average of project health scores)
    portfolio_health = projects_df['HEALTH_SCORE'].mean() if not projects_df.empty else 0
    
    # On-Time Delivery %
    if not projects_df.empty:
        on_time = (len(projects_df[projects_df['SCHEDULE_STATUS'] == 'GREEN']) / len(projects_df)) * 100
    else:
        on_time = 0
    
    # Quality Score (based on defect count)
    if not defects_df.empty:
        critical_count = len(defects_df[defects_df['SEVERITY'] == 'CRITICAL'])
        quality_score = max(0, 100 - (critical_count * 5))
    else:
        quality_score = 100
    
    # Test Pass Rate
    if not tests_df.empty:
        passed = len(tests_df[tests_df['STATUS'] == 'PASSED'])
        total = len(tests_df)
        test_pass_rate = (passed / total * 100) if total > 0 else 0
    else:
        test_pass_rate = 0
    
    return {
        'portfolio_health': round(portfolio_health, 1),
        'on_time_delivery': round(on_time, 1),
        'quality_score': round(quality_score, 1),
        'test_pass_rate': round(test_pass_rate, 1),
    }


def get_status_label(score: float) -> str:
    """Get status label based on score"""
    if score >= 90:
        return "Excellent 🟢"
    elif score >= 75:
        return "Healthy 🔵"
    elif score >= 60:
        return "Watchlist 🟡"
    else:
        return "Critical 🔴"
