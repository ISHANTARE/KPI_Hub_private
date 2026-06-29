"""
bootstrap.py
-------------
Initializes the data directory structure and populates missing runtime CSV files
from seed data templates in data/seed/ if they do not already exist.
"""

import shutil
from pathlib import Path

def bootstrap_data():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    seed_dir = data_dir / "seed"

    if not seed_dir.exists():
        print("Seed directory does not exist. Skipping bootstrap.")
        return

    print("Checking data files against seed templates...")
    copied_count = 0

    for seed_file in seed_dir.rglob("*.csv"):
        rel_path = seed_file.relative_to(seed_dir)
        target_file = data_dir / rel_path

        if not target_file.exists():
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(seed_file, target_file)
            print(f"  [+] Created from seed: {rel_path}")
            copied_count += 1

    print(f"Bootstrap complete. {copied_count} file(s) restored/created.")

if __name__ == "__main__":
    bootstrap_data()
