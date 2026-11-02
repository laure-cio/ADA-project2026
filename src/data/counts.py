"""Daily trip counts from the clean data."""
import glob

import pandas as pd
import geopandas as gpd


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

def zone_hourly_counts(zones, clean_dir="data/clean", max_dist_m=700):
    """Trips per hour and per community area.

    A start position outside every area is given to the nearest area if it is within
    max_dist_m (e-bike positions are rounded to ~1 km); otherwise zone 0 = outside (mainly Evanston).
    """
    zones_m = zones.to_crs(epsg=26916)                      # metric coordinates (UTM 16N)
    parts = []
    for f in sorted(glob.glob(f"{clean_dir}/*__*.parquet")):
        df = pd.read_parquet(f, columns=["started_at", "start_lat", "start_lng", "user_type", "bike_type"])

        # 1. place only the distinct start positions on the map
        coords = df[["start_lat", "start_lng"]].drop_duplicates().reset_index(drop=True)
        points = gpd.GeoDataFrame(coords, crs="EPSG:4326",
                                  geometry=gpd.points_from_xy(coords["start_lng"], coords["start_lat"]))
        joined = gpd.sjoin(points, zones[["zone_id", "geometry"]], how="left", predicate="within")
        joined = joined[~joined.index.duplicated()]

        # 2. positions outside every zone: nearest zone within max_dist_m
        missing = joined.index[joined["zone_id"].isna()]
        if len(missing) > 0:
            near = gpd.sjoin_nearest(points.loc[missing].to_crs(epsg=26916), zones_m[["zone_id", "geometry"]],
                                     how="left", max_distance=max_dist_m)
            near = near[~near.index.duplicated()]
            joined.loc[near.index, "zone_id"] = near["zone_id"].values

        # 3. copy the zone back to every trip
        df = df.merge(joined[["start_lat", "start_lng", "zone_id"]], on=["start_lat", "start_lng"], how="left")
        df["zone_id"] = df["zone_id"].fillna(0).astype(int)

        # 4. count per hour and zone
        df["hour"] = df["started_at"].dt.floor("h")
        df["is_casual"] = df["user_type"] == "casual"
        df["is_electric"] = df["bike_type"] == "electric"
        parts.append(df.groupby(["hour", "zone_id"]).agg(
            n_trips=("hour", "size"), n_casual=("is_casual", "sum"), n_electric=("is_electric", "sum")))
    return pd.concat(parts).groupby(level=[0, 1]).sum().reset_index()   # some hours appear in two files