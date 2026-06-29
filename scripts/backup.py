"""
backup.py
---------
Automated database backup script for KPI Hub.
Creates timestamped copies of kpihub.db in data/backups/ and cleans up backups older than 30 days.
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta

def create_backup():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    db_file = data_dir / "kpihub.db"
    backup_dir = data_dir / "backups"

    if not db_file.exists():
        print(f"Database file {db_file} not found. Skipping backup.")
        return

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_dir / f"kpihub_backup_{timestamp}.db"

    shutil.copy2(db_file, backup_file)
    print(f"[+] Backup created successfully: {backup_file.name}")

    # Cleanup backups older than 30 days
    cutoff_date = datetime.now() - timedelta(days=30)
    for old_backup in backup_dir.glob("kpihub_backup_*.db"):
        file_mtime = datetime.fromtimestamp(old_backup.stat().st_mtime)
        if file_mtime < cutoff_date:
            old_backup.unlink()
            print(f"[-] Removed old backup: {old_backup.name}")

if __name__ == "__main__":
    create_backup()
