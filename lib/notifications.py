"""
lib/notifications.py
--------------------
Notification service for KPI Hub.

Supports Teams (webhook) and Email (SMTP).
Config is read from integrations/config.yaml via config_helper.
Logs every send attempt — success or failure — to a CSV audit file.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Log file path — resolved relative to project root regardless of CWD
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = _PROJECT_ROOT / "data" / "resources" / "notification_log.csv"


def _load_notify_config() -> dict:
    """Load notification-relevant sections from integrations/config.yaml."""
    try:
        from integrations.config_helper import load_config
        cfg = load_config(str(_PROJECT_ROOT / "integrations" / "config.yaml"))
        return cfg
    except Exception as e:
        logger.warning(f"[notifications] Could not load config: {e}")
        return {}


def init_log():
    """Ensure the notification log CSV exists with the correct schema."""
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(columns=["TIMESTAMP", "RECIPIENT", "CHANNEL", "EVENT_TYPE", "STATUS", "DETAILS"])
        df.to_csv(LOG_FILE, index=False)


def notify(person_name: str, event_type: str, payload: dict, channel: str = "Teams") -> bool:
    """
    Send a notification to a person via Teams, Email, or Both.

    Parameters
    ----------
    person_name : str
        Recipient name — looked up in data/resources/org_mapping.csv.
    event_type  : str
        Identifier such as 'REBALANCE_ACCEPTED' or 'PHASE_MISMATCH'.
    payload     : dict
        Key/value pairs rendered into the message body.
    channel     : str
        'Teams', 'Email', or 'Both'.
    """
    init_log()

    # ── 1. Lookup recipient in org_mapping ──────────────────────────────
    try:
        org_path = _PROJECT_ROOT / "data" / "resources" / "org_mapping.csv"
        org_df = pd.read_csv(org_path)
        person_match = org_df[org_df["TEAM_MEMBER"] == person_name]
        if person_match.empty:
            _log_notification(person_name, channel, event_type, "FAILED",
                              f"Person '{person_name}' not found in org_mapping")
            return False

        person_row = person_match.iloc[0]
        email    = str(person_row.get("EMAIL", "")).strip()
        teams_id = str(person_row.get("TEAMS_ID", "")).strip()

        if not email or email.lower() == "nan":
            email = ""
        if not teams_id or teams_id.lower() == "nan":
            teams_id = ""

    except Exception as e:
        _log_notification(person_name, channel, event_type, "FAILED",
                          f"Failed to read org_mapping: {e}")
        return False

    # ── 2. Render message ────────────────────────────────────────────────
    message = f"**{event_type}**\n\n"
    for k, v in payload.items():
        message += f"- {k}: {v}\n"

    # ── 3. Send ──────────────────────────────────────────────────────────
    cfg     = _load_notify_config()
    success = True

    if channel in ("Teams", "Both"):
        success &= _send_teams(person_name, event_type, message, teams_id, cfg)

    if channel in ("Email", "Both"):
        success &= _send_email(person_name, event_type, message, email, cfg)

    return success


# ── Teams ────────────────────────────────────────────────────────────────────

def _send_teams(person_name: str, event_type: str, message: str,
                teams_id: str, cfg: dict) -> bool:
    teams_cfg   = cfg.get("teams", {})
    webhook_url = teams_cfg.get("webhook_url", "").strip()

    if not teams_cfg.get("enabled", False):
        _log_notification(person_name, "Teams", event_type, "SKIPPED",
                          "Teams integration disabled in config")
        return True  # not a failure — deliberately off

    if not webhook_url or webhook_url.startswith("YOUR_"):
        _log_notification(person_name, "Teams", event_type, "SKIPPED",
                          "Teams webhook_url not configured")
        return True

    try:
        import requests  # optional dependency
        payload = {
            "text": message,
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": event_type,
            "themeColor": "0076D7",
            "sections": [{"text": message}],
        }
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        _log_notification(person_name, "Teams", event_type, "SUCCESS",
                          f"Delivered to webhook (recipient alias: {teams_id})")
        return True
    except Exception as e:
        _log_notification(person_name, "Teams", event_type, "FAILED", str(e))
        logger.error(f"[notifications] Teams send failed for {person_name}: {e}")
        return False


# ── Email ────────────────────────────────────────────────────────────────────

def _send_email(person_name: str, event_type: str, message: str,
                email: str, cfg: dict) -> bool:
    email_cfg = cfg.get("email", {})

    if not email_cfg.get("enabled", False):
        _log_notification(person_name, "Email", event_type, "SKIPPED",
                          "Email integration disabled in config")
        return True

    smtp_server   = email_cfg.get("smtp_server", "").strip()
    smtp_port     = int(email_cfg.get("smtp_port", 587))
    sender_email  = email_cfg.get("sender_email", "").strip()
    sender_pw     = email_cfg.get("sender_password", "").strip()

    if not smtp_server or not sender_email or not sender_pw or sender_pw.startswith("YOUR_"):
        _log_notification(person_name, "Email", event_type, "SKIPPED",
                          "SMTP credentials not fully configured")
        return True

    if not email:
        _log_notification(person_name, "Email", event_type, "FAILED",
                          f"No email address for {person_name}")
        return False

    try:
        msg                    = MIMEMultipart("alternative")
        msg["Subject"]         = f"KPI Hub Notification: {event_type}"
        msg["From"]            = sender_email
        msg["To"]              = email
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_pw)
            server.sendmail(sender_email, [email], msg.as_string())

        _log_notification(person_name, "Email", event_type, "SUCCESS",
                          f"Sent to {email}")
        return True
    except Exception as e:
        _log_notification(person_name, "Email", event_type, "FAILED", str(e))
        logger.error(f"[notifications] Email send failed for {person_name}: {e}")
        return False


# ── Audit log ────────────────────────────────────────────────────────────────

def _log_notification(recipient: str, channel: str, event_type: str,
                       status: str, details: str):
    new_row = pd.DataFrame([{
        "TIMESTAMP":  datetime.now().isoformat(),
        "RECIPIENT":  recipient,
        "CHANNEL":    channel,
        "EVENT_TYPE": event_type,
        "STATUS":     status,
        "DETAILS":    details,
    }])
    if LOG_FILE.exists():
        df_log = pd.read_csv(LOG_FILE)
        df_log = pd.concat([df_log, new_row], ignore_index=True)
    else:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        df_log = new_row
    df_log.to_csv(LOG_FILE, index=False)
