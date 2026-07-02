"""
Slack and Microsoft Teams notification helper.
Posts real alerts via configured webhooks when CPI or SPI drops below threshold.
"""
import logging
import json
from typing import List, Optional
import requests

logger = logging.getLogger(__name__)

def send_slack_alert(message: str, webhook_url: str) -> bool:
    """Post an alert message to a Slack webhook."""
    if not webhook_url:
        logger.warning("Slack webhook URL not provided.")
        return False
    try:
        payload = {"text": message}
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code == 200:
            logger.info("Successfully posted alert to Slack.")
            return True
        else:
            logger.error(f"Slack webhook returned status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False

def send_teams_alert(message: str, webhook_url: str) -> bool:
    """Post an alert message to a Microsoft Teams webhook."""
    if not webhook_url:
        logger.warning("Teams webhook URL not provided.")
        return False
    try:
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Medium",
                                "weight": "Bolder",
                                "text": "🚨 KPI Hub Performance Alert"
                            },
                            {
                                "type": "TextBlock",
                                "text": message,
                                "wrap": True
                            }
                        ],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.2"
                    }
                }
            ]
        }
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code in [200, 201, 202]:
            logger.info("Successfully posted alert to Microsoft Teams.")
            return True
        else:
            logger.error(f"Teams webhook returned status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Teams alert: {e}")
        return False

class SlackNotifier:
    def __init__(self, config_path: str = "integrations/config.yaml"):
        self.config = {}
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            pass
        self.cfg = self.config.get('slack', {})

    def send(self, message: str, channels: List[str] = None) -> bool:
        if not self.cfg.get('enabled'):
            logger.info("Slack notifications are disabled")
            return False
        webhook = self.cfg.get('webhook_url')
        if not webhook:
            return False
        return send_slack_alert(message, webhook)
