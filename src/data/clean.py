"""Steps 4-6 - Convert values, add station positions, remove bad rows."""
import pandas as pd

from src.data.convert import convert_durations

# R2 - Technical stations (testing, warehouse, depot, repair), checked by hand
TECHNICAL_STATIONS = {
    "WATSON TESTING - DIVVY", "Base - 2132 W Hubbard", "Base - 2132 W Hubbard Warehouse",
    "HUBBARD ST BIKE CHECKING (LBS-WH-TEST)", "DIVVY CASSETTE REPAIR MOBILE STATION",
    "DIVVY Map Frame B/C Station", "Hubbard St Depot", "Hubbard St Depot Public Rack",
    "SCOOTERS CLASSIC - 2132 W Hubbard ST", "OH Charging Stx - Test",
    "STAFF & VISITORS @ West Chicago Warehouse", "BBB ~ Divvy Parts Testing",
    "Hastings Test Station", "Hastings WH 2", "hubbard_test_lws",
    "Throop/Hastings Mobile Station", "OH - BONFIRE - TESTING",
    "Pawel Bialowas - Test- PBSC charging station", "TS ~ DIVVY PARTS TESTING",
    "Special Events", "LBS - BBB La Magie",
}

# R4 - Rough box around Chicago (includes Evanston in the north)
LAT_MIN, LAT_MAX = 41.60, 42.10
LNG_MIN, LNG_MAX = -88.00, -87.50

USER_TYPES = {"Subscriber": "member", "Customer": "casual", "Dependent": "member",
              "member": "member", "casual": "casual"}

BIKE_TYPES = {"docked_bike": "classic", "classic_bike": "classic",
              "electric_bike": "electric"}


def add_values(df, stations):
    """Convert values to the common format and add positions to old trips."""
    df, _ = convert_durations(df)                                   # Step 4
    df["user_type"] = df["user_type"].map(USER_TYPES)               # unknown -> NaN
    df["bike_type"] = df["bike_type"].map(BIKE_TYPES).fillna("classic")  # old trips = classic
    for side in ["start", "end"]:
        df[f"{side}_station_name"] = df[f"{side}_station_name"].str.replace(
            r"\s*\(\*\)", "", regex=True)
        df[f"{side}_lat"] = pd.to_numeric(df[f"{side}_lat"], errors="coerce")
        df[f"{side}_lng"] = pd.to_numeric(df[f"{side}_lng"], errors="coerce")
        # Step 5 - old trips have no GPS: take the position of their station
        ids = pd.to_numeric(df[f"{side}_station_id"], errors="coerce")
        no_gps = df[f"{side}_lat"].isna()
        df.loc[no_gps, f"{side}_lat"] = ids[no_gps].map(stations.set_index("id")["latitude"])
        df.loc[no_gps, f"{side}_lng"] = ids[no_gps].map(stations.set_index("id")["longitude"])
    df["has_station"] = df["start_station_name"].notna()
    return df


def apply_rules(df):
    """Remove bad rows. Each row is counted under the first rule that removes it."""
    rules = {
        "R1_duration": (df["duration_s"] < 60) | (df["duration_s"] > 24 * 3600),
        "R2_technical_station": (df["start_station_name"].isin(TECHNICAL_STATIONS)
                                 | df["end_station_name"].isin(TECHNICAL_STATIONS)),
        "R3_no_start_position": df["start_lat"].isna() | df["start_lng"].isna(),
        "R4_outside_chicago": ~(df["start_lat"].between(LAT_MIN, LAT_MAX)
                                & df["start_lng"].between(LNG_MIN, LNG_MAX)),
        "R5_duplicate_trip_id": df["trip_id"].duplicated(),
    }
    removed = pd.Series(False, index=df.index)
    log = {"rows_before": len(df)}
    for name, mask in rules.items():
        new = mask & ~removed            # only rows not already removed by a previous rule
        log[name] = int(new.sum())
        removed |= new
    log["rows_after"] = int((~removed).sum())
    log["unknown_user_type"] = int(df.loc[~removed, "user_type"].isna().sum())
    return df[~removed], log