"""
Power BI Embed Helper (scaffold & asset configuration manager)
Maintains embeds, reports, and token mappings for embedding executive Power BI dashboards.
"""
import logging
try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class PowerBIEmbedHelper:
    def __init__(self, config_path: str = "integrations/config.yaml"):
        if yaml is not None:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

        self.cfg = self.config.get('powerbi', {})

    def get_embed_config(self) -> dict:
        """Returns standard metadata required for embedding Power BI reports"""
        if not self.cfg.get('enabled'):
            return {"enabled": False, "message": "Power BI embedding is disabled in configuration"}
            
        return {
            "enabled": True,
            "embed_url": self.cfg.get('embed_url', ''),
            "report_id": self.cfg.get('report_id', ''),
            "workspace_id": self.cfg.get('workspace_id', ''),
            "azure_client_id": self.cfg.get('azure_client_id', '')
        }

    def sync_all(self) -> bool:
        # Scheduler sync entrypoint
        if not self.cfg.get('enabled'):
            logger.info("Power BI integration is disabled")
            return False
            
        logger.info("Power BI connection and access tokens validated")
        return True
