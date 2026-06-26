"""
Integration Scheduler
Automatically syncs data from various sources on a schedule

Usage:
    python integrations/scheduler.py

This runs continuously and syncs data based on configured intervals
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from integrations.codebeamer_sync import CodebeamerSync
from integrations.jira_sync import JiraSync
from integrations.azure_devops_sync import AzureDevOpsSync
from integrations.monday_sync import MondaySync
from integrations.asana_sync import AsanaSync
from integrations.slack_notify import SlackNotifier
from integrations.email_notify import EmailNotifier
from integrations.config_helper import load_config

# Setup logging (must be before any logger usage)
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# New Integrations (optional — failures are non-fatal)
try:
    from integrations.github_sync import GitHubSync
    from integrations.teams_notify import TeamsNotifier
    from integrations.confluence_sync import ConfluenceSync
    from integrations.sharepoint_sync import SharePointSync
    from integrations.powerbi_helper import PowerBIEmbedHelper
    from integrations.polarion_doors_sync import PolarionDoorsSync
    from integrations.test_mgmt_sync import TestManagementSync
    from integrations.outlook_calendar_sync import OutlookCalendarSync
    from integrations.kb_rag_sync import KnowledgeBaseSync
except ImportError as e:
    logger.warning(f"Optional integration import skipped: {e}")


class IntegrationScheduler:
    """Manages scheduled syncs from various data sources"""
    
    def __init__(self, config_path: str = "integrations/config.yaml"):
        """Initialize scheduler with configuration"""
        self.config = self._load_config(config_path)
        # Try to import schedule module; scheduling features are optional for --once runs
        try:
            import schedule as schedule_module
            self.schedule = schedule_module
            self._schedule_enabled = True
        except Exception:
            logger.warning("`schedule` package not available; continuous scheduling disabled")
            self.schedule = None
            self._schedule_enabled = False
        self.codebeamer = CodebeamerSync(config_path)
        self.jira = JiraSync(config_path)
        # Optional integrations
        try:
            self.azure_devops = AzureDevOpsSync(config_path)
        except Exception:
            self.azure_devops = None

        try:
            self.monday = MondaySync(config_path)
        except Exception:
            self.monday = None

        try:
            self.asana = AsanaSync(config_path)
        except Exception:
            self.asana = None

        # New integrations
        try: self.github = GitHubSync(config_path)
        except Exception: self.github = None

        try: self.teams = TeamsNotifier(config_path)
        except Exception: self.teams = None

        try: self.confluence = ConfluenceSync(config_path)
        except Exception: self.confluence = None

        try: self.sharepoint = SharePointSync(config_path)
        except Exception: self.sharepoint = None

        try: self.powerbi = PowerBIEmbedHelper(config_path)
        except Exception: self.powerbi = None

        try: self.polarion_doors = PolarionDoorsSync(config_path)
        except Exception: self.polarion_doors = None

        try: self.test_management = TestManagementSync(config_path)
        except Exception: self.test_management = None

        try: self.outlook_calendar = OutlookCalendarSync(config_path)
        except Exception: self.outlook_calendar = None

        try: self.knowledge_base = KnowledgeBaseSync(config_path)
        except Exception: self.knowledge_base = None

        # Notification helpers
        try:
            self.slack = SlackNotifier(config_path)
        except Exception:
            self.slack = None

        try:
            self.email = EmailNotifier(config_path)
        except Exception:
            self.email = None
        # Only configure scheduled jobs if schedule is available
        if self._schedule_enabled:
            self._schedule_jobs()
    
    def _load_config(self, config_path: str) -> dict:
        """Load YAML configuration"""
        try:
            return load_config(config_path)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _schedule_jobs(self):
        """Schedule sync jobs based on config"""
        
        # Codebeamer sync
        cb_config = self.config.get('codebeamer', {})
        if cb_config.get('enabled'):
            interval = cb_config.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.sync_codebeamer)
            logger.info(f"Scheduled Codebeamer sync every {interval} minutes")
        
        # Jira sync
        jira_config = self.config.get('jira', {})
        if jira_config.get('enabled'):
            interval = jira_config.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.sync_jira)
            logger.info(f"Scheduled Jira sync every {interval} minutes")
        
        # Daily report at 8:00 AM
        self.schedule.every().day.at("08:00").do(self.send_daily_report)
        logger.info("Scheduled daily report at 08:00")

        # Resource utilization check (daily at 09:00 AM)
        self.schedule.every().day.at("09:00").do(self.check_resource_utilization)
        logger.info("Scheduled resource utilization check at 09:00")

        # Azure DevOps sync
        ad_config = self.config.get('azure_devops', {})
        if ad_config.get('enabled') and self.azure_devops:
            interval = ad_config.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.azure_devops.sync_all)
            logger.info(f"Scheduled Azure DevOps sync every {interval} minutes")

        # Monday.com sync
        monday_cfg = self.config.get('monday_com', {})
        if monday_cfg.get('enabled') and self.monday:
            interval = monday_cfg.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.monday.sync_all)
            logger.info(f"Scheduled Monday.com sync every {interval} minutes")

        # Asana sync
        asana_cfg = self.config.get('asana', {})
        if asana_cfg.get('enabled') and self.asana:
            interval = asana_cfg.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.asana.sync_all)
            logger.info(f"Scheduled Asana sync every {interval} minutes")

        # GitHub sync
        github_cfg = self.config.get('github', {})
        if github_cfg.get('enabled') and self.github:
            interval = github_cfg.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.github.sync_all)
            logger.info(f"Scheduled GitHub sync every {interval} minutes")

        # Confluence sync
        conf_cfg = self.config.get('confluence', {})
        if conf_cfg.get('enabled') and self.confluence:
            interval = conf_cfg.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.confluence.sync_all)
            logger.info(f"Scheduled Confluence sync every {interval} minutes")

        # SharePoint sync
        sp_cfg = self.config.get('sharepoint', {})
        if sp_cfg.get('enabled') and self.sharepoint:
            interval = sp_cfg.get('sync_interval', 120)
            self.schedule.every(interval).minutes.do(self.sharepoint.sync_all)
            logger.info(f"Scheduled SharePoint sync every {interval} minutes")

        # Polarion/DOORS sync
        pd_cfg = self.config.get('polarion_doors', {})
        if pd_cfg.get('enabled') and self.polarion_doors:
            interval = pd_cfg.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.polarion_doors.sync_all)
            logger.info(f"Scheduled Polarion/DOORS sync every {interval} minutes")

        # Test Management sync
        tm_cfg = self.config.get('test_management', {})
        if tm_cfg.get('enabled') and self.test_management:
            interval = tm_cfg.get('sync_interval', 60)
            self.schedule.every(interval).minutes.do(self.test_management.sync_all)
            logger.info(f"Scheduled Test Management sync every {interval} minutes")

        # Outlook Calendar sync
        cal_cfg = self.config.get('outlook_calendar', {})
        if cal_cfg.get('enabled') and self.outlook_calendar:
            interval = cal_cfg.get('sync_interval', 120)
            self.schedule.every(interval).minutes.do(self.outlook_calendar.sync_all)
            logger.info(f"Scheduled Outlook Calendar sync every {interval} minutes")

        # Knowledge Base sync
        kb_cfg = self.config.get('knowledge_base', {})
        if kb_cfg.get('enabled') and self.knowledge_base:
            interval = kb_cfg.get('sync_interval', 180)
            self.schedule.every(interval).minutes.do(self.knowledge_base.sync_all)
            logger.info(f"Scheduled Knowledge Base sync every {interval} minutes")

        # Power BI verification
        pbi_cfg = self.config.get('powerbi', {})
        if pbi_cfg.get('enabled') and self.powerbi:
            self.schedule.every(24).hours.do(self.powerbi.sync_all)
            logger.info("Scheduled Power BI token refresh daily")
    
    def sync_codebeamer(self):
        """Sync Codebeamer data"""
        try:
            logger.info("Starting Codebeamer sync...")
            start_time = datetime.now()
            
            success = self.codebeamer.sync_all()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            status = "[SUCCESS]" if success else "[FAILED]"
            logger.info(f"Codebeamer sync {status} ({elapsed:.2f}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"Codebeamer sync error: {e}")
            return False
    
    def sync_jira(self):
        """Sync Jira data"""
        try:
            logger.info("Starting Jira sync...")
            start_time = datetime.now()
            
            success = self.jira.sync_all()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            status = "[SUCCESS]" if success else "[FAILED]"
            logger.info(f"Jira sync {status} ({elapsed:.2f}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"Jira sync error: {e}")
            return False
    
    def send_daily_report(self):
        """Send daily KPI report via email (if enabled)."""
        try:
            email_config = self.config.get('email', {})
            if not email_config.get('enabled'):
                return

            logger.info("Generating daily report...")

            # ── Build report body from live CSV data ────────────────────
            body_lines = [
                f"KPI Hub — Daily Report  ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                "=" * 60,
                "",
            ]

            try:
                import pandas as pd

                # Portfolio health summary
                proj_path = Path('data/projects/projects_status.csv')
                if proj_path.exists():
                    df = pd.read_csv(proj_path)
                    total = len(df)
                    on_track = len(df[df.get('STATUS', pd.Series()).str.upper() == 'ON_TRACK']) if 'STATUS' in df.columns else 'N/A'
                    body_lines += [
                        "Portfolio",
                        f"  Total projects : {total}",
                        f"  On-track       : {on_track}",
                        "",
                    ]

                # Open critical risks
                risk_path = Path('data/risks/risk_register.csv')
                if risk_path.exists():
                    df = pd.read_csv(risk_path)
                    open_critical = 0
                    if 'STATUS' in df.columns and 'SEVERITY' in df.columns:
                        open_critical = len(df[
                            (df['STATUS'].str.upper() == 'OPEN') &
                            (df['SEVERITY'].str.upper().isin(['HIGH', 'CRITICAL']))
                        ])
                    body_lines += [
                        "Risks",
                        f"  Open high/critical : {open_critical}",
                        "",
                    ]

                # Test pass rate
                test_path = Path('data/metrics/test_execution.csv')
                if test_path.exists():
                    df = pd.read_csv(test_path)
                    if 'STATUS' in df.columns and len(df) > 0:
                        passed = len(df[df['STATUS'].str.upper() == 'PASSED'])
                        rate   = round(passed / len(df) * 100, 1)
                        body_lines += [
                            "Testing",
                            f"  Test pass rate : {rate}%  ({passed}/{len(df)})",
                            "",
                        ]

                # Resource overallocation
                res_path = Path('data/resources/resource_allocation.csv')
                if res_path.exists():
                    df = pd.read_csv(res_path)
                    if 'ALLOCATION_STATUS' in df.columns:
                        over = len(df[df['ALLOCATION_STATUS'].str.upper() == 'OVERALLOCATED'])
                        body_lines += [
                            "Resources",
                            f"  Overallocated  : {over}",
                            "",
                        ]

            except Exception as exc:
                body_lines += [f"(Error building data summary: {exc})", ""]

            body_lines.append("—")
            body_lines.append("Sent by KPI Hub Integration Scheduler.")
            body = "\n".join(body_lines)

            if self.email:
                recipients = email_config.get('daily_report_recipients', [])
                subject = f"KPI Hub Daily Report — {datetime.now().strftime('%Y-%m-%d')}"
                self.email.send(subject, body, recipients)

            # Send Slack notification if configured
            slack_cfg = self.config.get('slack', {})
            if slack_cfg.get('enabled') and self.slack:
                self.slack.send("KPI Hub: Daily report generated and sent.")

            logger.info("Daily report sent.")

        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")

    def check_resource_utilization(self):
        """Check for over or underutilized resources and send email alerts."""
        try:
            import pandas as pd
            
            email_config = self.config.get('email', {})
            if not email_config.get('enabled') or not self.email:
                return

            resources_file = Path('data/resources/resource_allocation.csv')
            if not resources_file.exists():
                logger.warning("Resource allocation file not found.")
                return

            df = pd.read_csv(resources_file)
            
            # Remove '%' and convert to float
            df['UTIL_NUM'] = df['UTILIZATION_PCT'].astype(str).str.rstrip('%').astype(float)
            
            # Get thresholds from config
            res_config = self.config.get('resources', {}).get('risk_thresholds', {})
            over_threshold = float(res_config.get('overallocated_pct', 120))
            under_threshold = float(res_config.get('underutilized_pct', 50))
            
            # Find outliers
            overallocated = df[(df['UTIL_NUM'] >= over_threshold) | (df['ALLOCATION_STATUS'].str.upper() == 'OVERALLOCATED')]
            underutilized = df[(df['UTIL_NUM'] <= under_threshold) | (df['ALLOCATION_STATUS'].str.upper() == 'UNDERUTILIZED')]
            
            if overallocated.empty and underutilized.empty:
                logger.info("No resource utilization issues detected.")
                return

            # Build email body
            body = "Automated Resource Utilization Alert\n\n"
            
            if not overallocated.empty:
                body += f"--- Overallocated Resources (Threshold: {over_threshold}%) ---\n"
                for _, row in overallocated.iterrows():
                    body += f"- {row['TEAM_MEMBER']} ({row['ROLE']}): {row['UTILIZATION_PCT']} Utilized (Project: {row['PROJECT_ID']})\n"
                body += "\n"
                
            if not underutilized.empty:
                body += f"--- Underutilized Resources (Threshold: {under_threshold}%) ---\n"
                for _, row in underutilized.iterrows():
                    body += f"- {row['TEAM_MEMBER']} ({row['ROLE']}): {row['UTILIZATION_PCT']} Utilized (Project: {row['PROJECT_ID']})\n"
                body += "\n"
                
            body += "Please review resource allocations to ensure balanced workloads.\n"
            
            recipients = email_config.get('daily_report_recipients', [])
            subject = "Alert: Resource Utilization Outliers Detected"
            
            self.email.send(subject, body, recipients)
            logger.info("Resource utilization alert email sent.")
            
        except Exception as e:
            logger.error(f"Failed to check resource utilization: {e}")
    
    def run(self):
        """Run the scheduler (blocking)"""
        logger.info("=" * 60)
        logger.info("KPI Hub Integration Scheduler started")
        logger.info("=" * 60)
        
        # Run initial sync on startup
        self.sync_codebeamer()
        self.sync_jira()
        if getattr(self, 'azure_devops', None):
            try:
                self.azure_devops.sync_all()
            except Exception as e:
                logger.error(f"Azure DevOps initial sync error: {e}")

        if getattr(self, 'monday', None):
            try:
                self.monday.sync_all()
            except Exception as e:
                logger.error(f"Monday initial sync error: {e}")

        if getattr(self, 'asana', None):
            try:
                self.asana.sync_all()
            except Exception as e:
                logger.error(f"Asana initial sync error: {e}")

        # New integrations initial syncs
        for attr in ['github', 'teams', 'confluence', 'sharepoint', 'powerbi', 'polarion_doors', 'test_management', 'outlook_calendar', 'knowledge_base']:
            client = getattr(self, attr, None)
            if client:
                try:
                    client.sync_all()
                except Exception as e:
                    logger.error(f"{attr.replace('_', ' ').title()} initial sync error: {e}")
        
        # If schedule is not available, inform user and return after initial sync
        if not self._schedule_enabled:
            logger.warning("`schedule` not available; run with --once for single sync cycles")
            return

        # Keep scheduler running
        while True:
            try:
                self.schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def run_once(self):
        """Run a single sync cycle (useful for testing)"""
        logger.info("Running single sync cycle...")
        cb_result = True
        jira_result = True

        try:
            cb_result = self.sync_codebeamer()
        except Exception as e:
            logger.error(f"Error during Codebeamer sync: {e}")
            cb_result = False

        try:
            jira_result = self.sync_jira()
        except Exception as e:
            logger.error(f"Error during Jira sync: {e}")
            jira_result = False

        # Optional syncs
        try:
            if getattr(self, 'azure_devops', None):
                self.azure_devops.sync_all()
        except Exception as e:
            logger.error(f"Error during Azure DevOps sync: {e}")

        try:
            if getattr(self, 'monday', None):
                self.monday.sync_all()
        except Exception as e:
            logger.error(f"Error during Monday.com sync: {e}")

        try:
            if getattr(self, 'asana', None):
                self.asana.sync_all()
        except Exception as e:
            logger.error(f"Error during Asana sync: {e}")

        # New integrations
        for attr in ['github', 'teams', 'confluence', 'sharepoint', 'powerbi', 'polarion_doors', 'test_management', 'outlook_calendar', 'knowledge_base']:
            client = getattr(self, attr, None)
            if client:
                try:
                    client.sync_all()
                except Exception as e:
                    logger.error(f"Error during {attr.replace('_', ' ').title()} sync: {e}")

        success = bool(cb_result and jira_result)
        logger.info(f"Single sync cycle complete - success={success}")
        return success


# Command line interface
if __name__ == "__main__":
    import sys
    
    scheduler = IntegrationScheduler()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run single sync cycle
        scheduler.run_once()
    else:
        # Run continuously
        scheduler.run()
