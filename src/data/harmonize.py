"""Step 1-2 - Read any trip file and rename its columns to the common format."""
import zipfile
from pathlib import Path

import pandas as pd

# The columns every cleaned file will have, in this order
COMMON_COLUMNS = [
    "trip_id",
    "started_at", "ended_at", "duration_s",
    "start_station_id", "start_station_name",
    "end_station_id", "end_station_name",
    "start_lat", "start_lng", "end_lat", "end_lng",
    "user_type", "bike_type",
]

# One renaming dictionary per family: {old name: common name}.
# Only the columns we keep are listed; the others are not loaded.
RENAME = {
    "old_2013": {
        "trip_id": "trip_id",
        "starttime": "started_at",
        "stoptime": "ended_at",
        "tripduration": "duration_s",
        "from_station_id": "start_station_id",
        "from_station_name": "start_station_name",
        "to_station_id": "end_station_id",
        "to_station_name": "end_station_name",
        "usertype": "user_type",
    },
    "old_2014_2016": {
        "trip_id": "trip_id",
        "starttime": "started_at",
        "stoptime": "ended_at",
        "tripduration": "duration_s",
        "from_station_id": "start_station_id",
        "from_station_name": "start_station_name",
        "to_station_id": "end_station_id",
        "to_station_name": "end_station_name",
        "usertype": "user_type",
    },
    "old_2017_2019": {
        "trip_id": "trip_id",
        "start_time": "started_at",
        "end_time": "ended_at",
        "tripduration": "duration_s",
        "from_station_id": "start_station_id",
        "from_station_name": "start_station_name",
        "to_station_id": "end_station_id",
        "to_station_name": "end_station_name",
        "usertype": "user_type",
    },
    "old_long_names": {
        "01 - Rental Details Rental ID": "trip_id",
        "01 - Rental Details Local Start Time": "started_at",
        "01 - Rental Details Local End Time": "ended_at",
        "01 - Rental Details Duration In Seconds Uncapped": "duration_s",
        "03 - Rental Start Station ID": "start_station_id",
        "03 - Rental Start Station Name": "start_station_name",
        "02 - Rental End Station ID": "end_station_id",
        "02 - Rental End Station Name": "end_station_name",
        "User Type": "user_type",
    },
    "new_2020_2026": {
        "ride_id": "trip_id",
        "started_at": "started_at",
        "ended_at": "ended_at",
        "start_station_id": "start_station_id",
        "start_station_name": "start_station_name",
        "end_station_id": "end_station_id",
        "end_station_name": "end_station_name",
        "start_lat": "start_lat",
        "start_lng": "start_lng",
        "end_lat": "end_lat",
        "end_lng": "end_lng",
        "member_casual": "user_type",
        "rideable_type": "bike_type",
    },
}


def load_harmonized(zip_name, csv_name, family, raw_dir="data/raw"):
    """Read one trip CSV and return it with the common column names.

    Everything is read as text: types are converted in the next steps.
    Columns that do not exist in this family (e.g. GPS before 2020) are empty.
    """
    rename = RENAME[family]
    with zipfile.ZipFile(Path(raw_dir) / zip_name) as zf:
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, usecols=list(rename), dtype=str)
    df = df.rename(columns=rename)
    for col in COMMON_COLUMNS:          # add the columns this family does not have
        if col not in df.columns:
            df[col] = pd.NA
    df["source_zip"] = zip_name         # to know where each row comes from
    return df[COMMON_COLUMNS + ["source_zip"]]