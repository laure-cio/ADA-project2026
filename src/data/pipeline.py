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

def run_steps_4_to_7(stations, interim_dir="data/interim", out_dir="data/clean"):
    """Convert values, add positions, apply the cleaning rules to every file.

    Saves each clean file in data/clean/ and returns:
    - log: rows removed by each rule, per file
    - daily: trips before and after cleaning, per day (to check the cleaning per day)
    """
    from src.data.clean import add_values, apply_rules
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    logs, daily = [], []
    files = sorted(Path(interim_dir).glob("*__*.parquet"))
    for i, f in enumerate(files, start=1):
        df = add_values(pd.read_parquet(f), stations)
        before = df["started_at"].dt.date.value_counts()
        clean, log = apply_rules(df)
        after = clean["started_at"].dt.date.value_counts()
        clean.to_parquet(Path(out_dir) / f.name, index=False)
        logs.append({"file": f.name, **log})
        daily.append(pd.DataFrame({"before": before, "after": after}).fillna(0))
        print(f"{i}/{len(files)} {f.name}: {log['rows_before']:,} -> {log['rows_after']:,}")
    daily = pd.concat(daily).groupby(level=0).sum()
    return pd.DataFrame(logs), daily

def remove_cross_file_duplicates(clean_dir="data/clean"):
    """Remove trips that also appear in the previous file (in time order).

    The copy in the earlier file is kept; the one in the later file is removed.
    Returns how many trips were removed from each file.
    """
    files = sorted(Path(clean_dir).glob("*__*.parquet"))
    first_date = {f: pd.read_parquet(f, columns=["started_at"])["started_at"].min() for f in files}
    files = sorted(files, key=first_date.get)
    removed = {}
    for f1, f2 in zip(files[:-1], files[1:]):
        ids1 = set(pd.read_parquet(f1, columns=["trip_id"])["trip_id"])
        df2 = pd.read_parquet(f2)
        dup = df2["trip_id"].isin(ids1)
        if dup.any():
            df2[~dup].to_parquet(f2, index=False)
            removed[f2.name] = int(dup.sum())
    return removed