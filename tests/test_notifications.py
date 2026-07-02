import pytest
import pandas as pd
from lib.notifications import check_and_dispatch_evm_alerts
import lib.notifications as notifications

def test_check_and_dispatch_evm_alerts(monkeypatch):
    slack_alerts_sent = []
    teams_alerts_sent = []
    
    # Mock webhook senders
    def mock_send_slack(message, webhook_url):
        slack_alerts_sent.append((message, webhook_url))
        return True
        
    def mock_send_teams(message, webhook_url):
        teams_alerts_sent.append((message, webhook_url))
        return True
        
    # Mock config loader to ensure alerts are enabled
    def mock_load_config():
        return {
            "slack": {
                "enabled": True,
                "webhook_url": "https://hooks.slack.com/services/mock",
                "cpi_alert_threshold": 0.95,
                "spi_alert_threshold": 0.95
            },
            "teams": {
                "enabled": True,
                "webhook_url": "https://outlook.office.com/webhook/mock",
                "cpi_alert_threshold": 0.95,
                "spi_alert_threshold": 0.95
            }
        }
        
    monkeypatch.setattr(notifications, "_load_notify_config", mock_load_config)
    import integrations.slack_notify as sn
    monkeypatch.setattr(sn, "send_slack_alert", mock_send_slack)
    monkeypatch.setattr(sn, "send_teams_alert", mock_send_teams)
    
    # Create sample per-project EVM data where P001 is below threshold
    pevm_df = pd.DataFrame([
        {
            "PROJECT_ID": "P001",
            "PV": 1000.0,
            "EV": 800.0,
            "AC": 1000.0,
            "CPI": 0.8,
            "SPI": 0.8,
            "EAC": 1250.0,
            "VAC": -250.0,
            "CPI_Status": "Critical",
            "SPI_Status": "Critical"
        },
        {
            "PROJECT_ID": "P002",
            "PV": 1000.0,
            "EV": 1000.0,
            "AC": 950.0,
            "CPI": 1.05,
            "SPI": 1.0,
            "EAC": 950.0,
            "VAC": 50.0,
            "CPI_Status": "Healthy",
            "SPI_Status": "Healthy"
        }
    ])
    
    check_and_dispatch_evm_alerts(pevm_df)
    
    # Verify P001 triggered alerts (CPI and SPI)
    assert len(slack_alerts_sent) == 2
    assert len(teams_alerts_sent) == 2
    
    assert any("P001" in item[0] and "CPI" in item[0] for item in slack_alerts_sent)
    assert any("P001" in item[0] and "SPI" in item[0] for item in slack_alerts_sent)
    
    assert any("P001" in item[0] and "CPI" in item[0] for item in teams_alerts_sent)
    assert any("P001" in item[0] and "SPI" in item[0] for item in teams_alerts_sent)
