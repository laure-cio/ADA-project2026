"""Daily trip counts from the clean data."""
import glob

import pandas as pd


def daily_counts_city(clean_dir="data/clean"):
    """Number of trips per day for the whole city, split by user and bike type."""
    parts = []
    for f in glob.glob(f"{clean_dir}/*__*.parquet"):
        df = pd.read_parquet(f, columns=["started_at", "user_type", "bike_type"])
        df["date"] = df["started_at"].dt.date
        df["is_member"] = df["user_type"] == "member"
        df["is_casual"] = df["user_type"] == "casual"
        df["is_electric"] = df["bike_type"] == "electric"
        parts.append(df.groupby("date").agg(
            n_trips=("date", "size"),
            n_member=("is_member", "sum"),
            n_casual=("is_casual", "sum"),
            n_electric=("is_electric", "sum"),
        ))
    return pd.concat(parts).groupby(level=0).sum().sort_index()