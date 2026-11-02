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

def hourly_counts(clean_dir="data/clean"):
    """Number of trips per hour, by user type and bike type (read file by file)."""
    parts = []
    for f in sorted(glob.glob(f"{clean_dir}/*__*.parquet")):
        df = pd.read_parquet(f, columns=["started_at", "user_type", "bike_type"])
        df["hour"] = df["started_at"].dt.floor("h")
        parts.append(df.groupby(["hour", "user_type", "bike_type"]).size())
    counts = pd.concat(parts).groupby(level=[0, 1, 2]).sum()
    return counts.rename("n_trips").reset_index()


def active_stations_per_month(clean_dir="data/clean", min_trips=10):
    """Number of stations with at least `min_trips` starting trips, per month."""
    parts = []
    for f in sorted(glob.glob(f"{clean_dir}/*__*.parquet")):
        df = pd.read_parquet(f, columns=["started_at", "start_station_name"])
        df = df.dropna(subset=["start_station_name"])          # e-bikes left outside a station
        df["month"] = df["started_at"].dt.to_period("M")
        parts.append(df.groupby(["month", "start_station_name"]).size())
    per_station = pd.concat(parts).groupby(level=[0, 1]).sum()
    active = per_station[per_station >= min_trips]
    return active.groupby(level=0).size().rename("n_active_stations")