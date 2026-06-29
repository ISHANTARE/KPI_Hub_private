"""
lib/audit.py
-------------
Centralized audit logging module for tracking data edits and system events.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd

def log_data_edit(role: str, file_path: str, action: str = "File Saved") -> None:
    """Append one audit row to data/resources/data_edit_log.csv and SQLite audit_log."""
    log_file = Path('data/resources/data_edit_log.csv')
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if not log_file.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("TIMESTAMP,ROLE,FILE_EDITED,ACTION\n")
            
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp_str},{role},{file_path},{action}\n")

    try:
        from lib.database import save_dataframe_to_db
        new_entry = pd.DataFrame([{
            "TIMESTAMP": timestamp_str,
            "ROLE": role,
            "FILE_EDITED": file_path,
            "ACTION": action
        }])
        save_dataframe_to_db("data_edit_log", new_entry, if_exists="append")
    except Exception:
        pass
