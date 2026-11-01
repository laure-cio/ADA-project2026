"""External datasets used to explain the anomalies (2022-2025).

Each function downloads one source and returns a table with one row per
event or per day, with dates as YYYY-MM-DD (same format as the trip data).
"""
import io
import json
import re

import numpy as np
import pandas as pd
import requests
from matplotlib.path import Path

YEARS = [2022, 2023, 2024, 2025]
CHICAGO_PORTAL = "https://data.cityofchicago.org/resource"


def storm_events(years=YEARS):
    """NOAA Storm Events for Cook County (storms, heat, snow, floods...).

    Source: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
    """
    base = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    listing = requests.get(base, timeout=60).text
    parts = []
    for year in years:
        name = re.search(rf"StormEvents_details-ftp_v1\.0_d{year}_c\d+\.csv\.gz", listing).group(0)
        df = pd.read_csv(base + name, compression="gzip", low_memory=False)
        df = df[(df["STATE"] == "ILLINOIS") & df["CZ_NAME"].str.contains("COOK", na=False)]
        parts.append(df)
    df = pd.concat(parts)
    begin = pd.to_datetime(df["BEGIN_DATE_TIME"], format="%d-%b-%y %H:%M:%S")
    end = pd.to_datetime(df["END_DATE_TIME"], format="%d-%b-%y %H:%M:%S")
    return pd.DataFrame({
        "date": begin.dt.strftime("%Y-%m-%d"),
        "end_date": end.dt.strftime("%Y-%m-%d"),
        "event_type": df["EVENT_TYPE"],
        "zone": df["CZ_NAME"],
        "injuries": df["INJURIES_DIRECT"] + df["INJURIES_INDIRECT"],
        "deaths": df["DEATHS_DIRECT"] + df["DEATHS_INDIRECT"],
        "lat": df["BEGIN_LAT"],
        "lon": df["BEGIN_LON"],
        "narrative": df["EPISODE_NARRATIVE"],
    }).sort_values("date").reset_index(drop=True)


def storms_in_chicago(storms, cells_path="data/external/cells.geojson"):
    """Keep the storm events that concern the city of Chicago.

    Events with a position (storms, hail, floods...) are kept if they fall in
    one of the 37 cells. Events without a position (snow, cold, heat...) are
    given per forecast zone: only "Central Cook County", which contains
    Chicago, is kept.
    """
    geo = json.load(open(cells_path))
    paths = []
    for f in geo["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        paths += [Path(np.array(p[0])) for p in polys]

    def in_city(row):
        return any(p.contains_point((row["lon"], row["lat"])) for p in paths)

    located = storms["lat"].notna()
    keep = located & storms[located].apply(in_city, axis=1).reindex(storms.index, fill_value=False)
    keep |= ~located & (storms["zone"] == "CENTRAL COOK COUNTY")
    return storms[keep].reset_index(drop=True)


def baseball_home_games(years=YEARS):
    """Cubs (Wrigley Field) and White Sox home games, regular season.

    Source: MLB Stats API, https://statsapi.mlb.com
    """
    teams = {112: "Cubs", 145: "White Sox"}
    rows = []
    for year in years:
        for team_id, team in teams.items():
            url = (f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}"
                   f"&season={year}&gameType=R&hydrate=venue(location)")
            for day in requests.get(url, timeout=60).json()["dates"]:
                for g in day["games"]:
                    if g["teams"]["home"]["team"]["id"] != team_id:
                        continue
                    if g["status"]["detailedState"] in ("Postponed", "Cancelled"):
                        continue
                    coords = g["venue"].get("location", {}).get("defaultCoordinates", {})
                    start = pd.Timestamp(g["gameDate"]).tz_convert("America/Chicago")
                    rows.append({
                        "date": start.strftime("%Y-%m-%d"),
                        "start_hour": start.hour,
                        "team": team,
                        "venue": g["venue"]["name"],
                        "lat": coords.get("latitude"),
                        "lon": coords.get("longitude"),
                    })
    return pd.DataFrame(rows).drop_duplicates().sort_values("date").reset_index(drop=True)


def cta_daily_ridership(start="2022-01-01", end="2025-12-31"):
    """Daily CTA bus and train boardings (transit disruptions, city activity).

    Source: Chicago Data Portal, dataset 6iiy-9s97
    """
    params = {
        "$where": f"service_date between '{start}T00:00:00' and '{end}T00:00:00'",
        "$order": "service_date",
        "$limit": 50000,
    }
    r = requests.get(f"{CHICAGO_PORTAL}/6iiy-9s97.csv", params=params, timeout=120)
    df = pd.read_csv(io.StringIO(r.text))
    df["date"] = pd.to_datetime(df["service_date"]).dt.strftime("%Y-%m-%d")
    return df[["date", "day_type", "bus", "rail_boardings", "total_rides"]]


def park_big_events(start="2022-01-01", end="2025-12-31"):
    """Chicago Park District permits for big events (10,000+ people).

    Careful: a permit covers set-up and tear-down days too (the 2023 Marathon
    permit runs from 21 Sep to 13 Oct, the race was on 8 Oct). Use it to know
    *where* big events happen, not their exact day.
    Source: Chicago Data Portal, dataset pk66-w54g
    """
    params = {
        "$where": (f"reservation_start_date between '{start}T00:00:00' and '{end}T00:00:00' "
                   "and event_type in ('Permit - Event 6/10,000+', "
                   "'Permit - Festival/Performance/12,001+ Event')"),
        "$limit": 50000,
    }
    r = requests.get(f"{CHICAGO_PORTAL}/pk66-w54g.csv", params=params, timeout=120)
    df = pd.read_csv(io.StringIO(r.text))
    df["date"] = pd.to_datetime(df["reservation_start_date"]).dt.strftime("%Y-%m-%d")
    df["end_date"] = pd.to_datetime(df["reservation_end_date"]).dt.strftime("%Y-%m-%d")
    return (df.groupby(["event_description", "park_facility_name"])
              .agg(first_day=("date", "min"), last_day=("end_date", "max"))
              .reset_index().sort_values("first_day").reset_index(drop=True))
