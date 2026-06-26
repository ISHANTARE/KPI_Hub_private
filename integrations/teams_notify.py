"""
Microsoft Teams Integration (scaffold & webhook sender)
Sends alerts, KPIs updates, and action item notifications to Teams channels.
"""
import logging
import json
try:
    import urllib.request as urllib_request
except ImportError:
    urllib_request = None
try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class TeamsNotifier:
    def __init__(self, config_path: str = "integrations/config.yaml"):
        if yaml is not None:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

        self.cfg = self.config.get('teams', {})

    def send_notification(self, title: str, text: str) -> bool:
        if not self.cfg.get('enabled'):
            logger.info("MS Teams notification integration is disabled")
            return False

        webhook_url = self.cfg.get('webhook_url')
        if not webhook_url or webhook_url == "YOUR_WEBHOOK_URL_HERE":
            logger.warning("MS Teams webhook URL is not configured")
            return False

        logger.info(f"Sending Teams notification: {title}")
        
        # Format MS Teams Office 365 Connector Card payload
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "4b53bc",  # Teams purple color
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "activitySubtitle": "KPI Hub System Update",
                "text": text
            }]
        }
        
        if urllib_request is not None:
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib_request.Request(
                    webhook_url, 
                    data=data, 
                    headers={'Content-Type': 'application/json'}
                )
                with urllib_request.urlopen(req, timeout=5) as response:
                    res_code = response.getcode()
                    if res_code == 200:
                        logger.info("Notification sent successfully to Teams")
                        return True
                    else:
                        logger.warning(f"Teams returned status code: {res_code}")
                        return False
            except Exception as e:
                logger.error(f"Error posting to Teams webhook: {e}")
                return False
        else:
            logger.warning("urllib.request not available; cannot send HTTP request")
            return False

    def sync_all(self) -> bool:
        # Scheduler sync entrypoint
        if not self.cfg.get('enabled'):
            logger.info("MS Teams integration is disabled")
            return False
            
        logger.info("Teams webhook integration check complete")
        return True
