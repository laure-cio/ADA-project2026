
"""Step 5 - Station coordinates for the old (2013-2019) trips."""
import zipfile
from pathlib import Path

import pandas as pd


def load_station_files(inventory, raw_dir="data/raw"):
    """Read the 8 station files and stack them into one table."""
    tables = []
    station_files = inventory[inventory["family"] == "stations"]
    for row in station_files.itertuples():
        with zipfile.ZipFile(Path(raw_dir) / row.zip) as zf:
            with zf.open(row.csv) as f:
                df = pd.read_csv(f, usecols=["id", "name", "latitude", "longitude"])
        df["source_file"] = row.csv
        tables.append(df)
    return pd.concat(tables, ignore_index=True)

def stations_from_2020_trips(interim_dir="data/interim"):
    """Station positions from 2020 trips (Jan-Nov 2020 still use the old numeric IDs).

    For each numeric station ID: median start position and most frequent name.
    """
    import glob
    files = [f for f in glob.glob(f"{interim_dir}/*.parquet")
             if "2020_Q1" in f or any(f"2020{m:02d}-divvy" in f for m in range(4, 12))]
    trips = pd.concat(pd.read_parquet(f, columns=["start_station_id", "start_station_name",
                                                   "start_lat", "start_lng"])
                      for f in files)
    trips["id"] = pd.to_numeric(trips["start_station_id"], errors="coerce")
    trips = trips.dropna(subset=["id"])
    trips[["start_lat", "start_lng"]] = trips[["start_lat", "start_lng"]].astype(float)
    return trips.groupby("id").agg(
        name=("start_station_name", lambda s: s.mode().iloc[0]),
        latitude=("start_lat", "median"),
        longitude=("start_lng", "median"),
        n_trips=("start_lat", "size"),
    ).reset_index()
    
    
def build_station_table(stations_raw, stations_2020, missing_ids):
    """One position per old station ID.

    Official station files first (latest file for each station),
    then 2020 trip positions for stations created in 2018-2019.
    """
    official = (stations_raw.drop_duplicates("id", keep="last")
                [["id", "name", "latitude", "longitude"]]
                .assign(source="station_file"))
    from_2020 = (stations_2020[stations_2020["id"].isin(missing_ids)]
                 [["id", "name", "latitude", "longitude"]]
                 .assign(source="2020_trips"))
    table = pd.concat([official, from_2020], ignore_index=True)
    table["id"] = table["id"].astype(int)
    table["name"] = table["name"].str.replace(r"\s*\(\*\)", "", regex=True)
    return table   