"""UI Styling for KPI Hub MVP"""
import streamlit as st


def load_css():
    """Load custom CSS styling"""
    css = """
    <style>
        /* Main color scheme */
        :root {
            --color-success: #10B981;
            --color-warning: #F59E0B;
            --color-danger: #EF4444;
            --color-info: #3B82F6;
        }
        
        /* Status colors */
        .status-green { color: #10B981; font-weight: bold; }
        .status-yellow { color: #F59E0B; font-weight: bold; }
        .status-red { color: #EF4444; font-weight: bold; }
        
        /* KPI cards */
        .kpi-card {
            padding: 20px;
            border-radius: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            margin: 10px 0;
        }
        
        .kpi-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .kpi-label {
            font-size: 14px;
            opacity: 0.9;
        }
        
        /* Health score badges */
        .health-excellent {
            background: #10B981;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
        }
        
        .health-healthy {
            background: #3B82F6;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
        }
        
        .health-watchlist {
            background: #F59E0B;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
        }
        
        .health-critical {
            background: #EF4444;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
        }
        
        /* Table styling */
        table {
            border-collapse: collapse;
            width: 100%;
        }
        
        th {
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def get_status_color(score: float) -> tuple:
    """Map score to status (color, label)"""
    if score >= 90:
        return "🟢 Excellent", "#10B981"
    elif score >= 75:
        return "🔵 Healthy", "#3B82F6"
    elif score >= 60:
        return "🟡 Watchlist", "#F59E0B"
    else:
        return "🔴 Critical", "#EF4444"


def get_schedule_status_color(status: str) -> tuple:
    """Map schedule status to color"""
    status_upper = str(status).upper()
    if status_upper == "GREEN":
        return "🟢 On Track", "#10B981"
    elif status_upper == "YELLOW":
        return "🟡 At Risk", "#F59E0B"
    else:
        return "🔴 Off Track", "#EF4444"
