"""
Azure DevOps Integration (placeholder)
Provides a minimal sync_all() that prepares directories and logs activity.
"""
import logging
from pathlib import Path
try:
    import yaml
except Exception:
    yaml = None

logger = logging.getLogger(__name__)


class AzureDevOpsSync:
    def __init__(self, config_path: str = "integrations/config.yaml"):
        if yaml is not None:
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

        self.ad_config = self.config.get('azure_devops', {})
        self.data_dir = Path("data")

    def sync_all(self) -> bool:
        if not self.ad_config.get('enabled'):
            logger.info("Azure DevOps integration is disabled")
            return False

        logger.info("Azure DevOps sync (placeholder) started")
        # Ensure output dirs exist
        (self.data_dir / "projects").mkdir(parents=True, exist_ok=True)
        # Placeholder: write empty CSV to indicate run
        try:
            import pandas as pd
            df = pd.DataFrame([])
            (self.data_dir / "projects" / "azure_devops_work_items.csv").write_text(df.to_csv(index=False))
        except Exception:
            logger.debug("pandas not available or write failed; skipping CSV write")

        logger.info("Azure DevOps sync (placeholder) complete")
        return True
