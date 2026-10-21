"""Step 0 - Inventory of the raw Divvy files."""
import csv
import io
import zipfile
from pathlib import Path

import pandas as pd


def detect_family(columns):
    """Return the format family of a CSV from its column names."""
    cols = set(columns)
    if "ride_id" in cols:
        return "new_2020_2026"
    if "01 - Rental Details Rental ID" in cols:
        return "old_long_names"        # 2018 Q1, 2019 Q2
    if "birthday" in cols:
        return "old_2013"
    if "starttime" in cols:
        return "old_2014_2016"
    if "start_time" in cols:
        return "old_2017_2019"
    if "latitude" in cols:
        return "stations"
    return "unknown"


def build_inventory(raw_dir="data/raw"):
    """List every CSV inside the zip files with its family and column names."""
    rows = []
    for zip_path in sorted(Path(raw_dir).glob("*.zip")):
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv") or "__MACOSX" in name:
                    continue
                with zf.open(name) as f:
                    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
                    columns = [c.strip() for c in next(reader)]
                rows.append({
                    "zip": zip_path.name,
                    "csv": name,
                    "family": detect_family(columns),
                    "n_columns": len(columns),
                    "columns": columns,
                })
    return pd.DataFrame(rows)