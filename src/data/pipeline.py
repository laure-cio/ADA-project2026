"""Run the cleaning steps on every file and save intermediate results."""
from pathlib import Path

import pandas as pd

from src.data.harmonize import load_harmonized
from src.data.convert import parse_dates


def run_steps_1_to_3(inventory, raw_dir="data/raw", out_dir="data/interim"):
    """Harmonize + parse dates for every trip file, save each as parquet.

    Returns a log with, for each file: rows, failed dates, first and last date.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    log = []
    trip_files = inventory[inventory["family"] != "stations"]
    for i, row in enumerate(trip_files.itertuples(), start=1):
        df = load_harmonized(row.zip, row.csv, row.family, raw_dir)
        df, n_failed = parse_dates(df)
        out_name = Path(row.csv).stem + "__" + Path(row.zip).stem + ".parquet"
        df.to_parquet(Path(out_dir) / out_name, index=False)
        log.append({
            "zip": row.zip, "csv": row.csv, "family": row.family,
            "n_rows": len(df), "failed_dates": n_failed,
            "first": df["started_at"].min(), "last": df["started_at"].max(),
            "interim_file": out_name,
        })
        print(f"{i}/{len(trip_files)} {row.csv}: {len(df):,} rows, {n_failed} failed")
    return pd.DataFrame(log)