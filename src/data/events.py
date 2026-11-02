"""One table with all the events 2022-2025, one row per event and day.

Columns: date, event, type, venue, lat, lon, area (neighbourhood), cell_id,
cell_name, capacity, size, source. A cell is one of the 37 zones of the grid:
one neighbourhood, or a group of small ones ("Group 19 (3 areas)").
The events are used to explain the anomalies, not to define them.

Inputs:
- data/external/big_events.csv             8 big recurring festivals and races
- data/external/more_events.csv            parades, races, other festivals,
                                           stadium concerts, protests, DNC
- data/external/baseball_home_games.csv    Cubs and White Sox
- data/external/pro_sports_home_games.csv  Bears, Bulls, Blackhawks, Sky, Fire
- data/concerts/data/chicago_concerts.csv + chicago_venues.csv  (Gresi)
- data/external/cells.geojson              the 37 cells of the grid
Every date in big_events.csv and more_events.csv has its own source link.
"""
import json

import numpy as np
import pandas as pd
from matplotlib.path import Path

YEARS = (2022, 2025)

# Position (lat, lon) of the places that are not in Gresi's venue list.
# Points on the lakefront are moved slightly inland, because the cell
# outlines stop at the shore.
PLACES = {
    "Wrigley Field": (41.9484, -87.6553),
    "Rate Field (White Sox)": (41.8299, -87.6338),
    "Soldier Field": (41.8623, -87.6167),
    "United Center": (41.8807, -87.6742),
    "Wintrust Arena": (41.8531, -87.6215),
    "Grant Park": (41.8758, -87.6189),
    "Millennium Park": (41.8826, -87.6226),
    "Union Park": (41.8846, -87.6655),
    "Douglass Park": (41.8606, -87.6995),
    "North Avenue Beach": (41.9160, -87.6300),           # moved inland, into Lincoln Park
    "Lake Shore Drive": (41.8758, -87.6189),             # Bike the Drive starts in Grant Park
    "Pride route (Lake View)": (41.9400, -87.6440),      # Broadway & Belmont, middle of the route
    "Daley Plaza": (41.8840, -87.6301),
    "Columbus Drive": (41.8790, -87.6200),
    "State Street": (41.8840, -87.6278),
    "Jackson Park": (41.7834, -87.5805),
    "Humboldt Park": (41.9020, -87.7010),
    "Little Village (26th St)": (41.8443, -87.7186),     # middle of the route (Albany to Kostner)
    "Beverly (Western Ave)": (41.7030, -87.6825),        # 105th St, start of the route (in Beverly)
    "Randolph Street (West Loop)": (41.8844, -87.6512),  # Taste of Randolph
    "McCormick Place": (41.8516, -87.6170),              # Marathon expo
}

# Capacity (people) of the stadiums and arenas.
CAPACITY = {
    "Wrigley Field": 41649,
    "Rate Field (White Sox)": 40615,
    "Soldier Field": 61500,
    "United Center": 20917,
    "Wintrust Arena": 10387,
}

# Venue capacities from Gresi's notebook (data/concerts/Events_concerts.ipynb).
CONCERT_CAPACITY = {
    "Aragon Ballroom": 4500, "The Beat Kitchen": 275, "Empty Bottle": 400,
    "House of Blues": 1800, "Metro": 1150, "Sleeping Village": 300,
    "Concord Music Hall": 1600, "Thalia Hall": 900, "Reggie's": 600,
    "1st Ward / Chop Shop": 500, "Subterranean": 550, "Lincoln Hall": 507,
    "Chicago Theatre": 3553, "Millennium Park": 11000,
    "Huntington Bank Pavilion": 22000, "Union Park": 6000, "Radius": 3800,
    "Auditorium Theatre": 4000, "Bottom Lounge": 700, "Riviera Theater": 2500,
    "Vic Theatre": 1400, "Salt Shed": 3600, "Park West": 900,
    "Avondale Music Hall": 550, "Cubby Bear": 500, "Credit Union 1 Arena": 10000,
    "Schubas Tavern": 550, "Cole's": 100, "Ramova Theatre": 1400,
    "Epiphany Center for the Arts": 740, "Athenaeum Theatre": 950,
    "Douglass Park": 50000, "Grant Park": 35000, "Comrade": 60,
    "House of Vans": 850, "Cobra Lounge": 300, "Burlington": 150,
    "Goose Island Brewery": 90, "Hideout": 150, "GMan Tavern": 150,
    "Constellation": 250, "Golden Dagger": 100, "City Winery": 350,
    "Music Joint": 150, "Live Wire Lounge": 150, "Fireside Bowl": 140,
}

# Fixes to Gresi's concert list
VENUE_FIX = {"Douglas Park": "Douglass Park", "Riot Fest": "Douglass Park"}
STREET_FESTIVALS = {                       # "Unknown Venue" rows, placed by festival
    "Square Roots Festival": "Old Town School of Folk Music",
    "Taste Of Randolph Street": "Randolph Street (West Loop)",
}
OUTSIDE_CHICAGO = {"Allstate Arena"}       # Rosemont: no Divvy stations
STADIUMS = {"Soldier Field", "Wrigley Field"}   # concerts there come from more_events.csv

# Venue names used by the MLB and ESPN schedules -> names used here.
# Games played elsewhere (Tokyo, London, Bridgeview) are left out.
GAME_VENUES = {
    "Wrigley Field": "Wrigley Field",
    "Guaranteed Rate Field": "Rate Field (White Sox)",
    "Rate Field": "Rate Field (White Sox)",
    "Soldier Field": "Soldier Field",
    "United Center": "United Center",
    "Wintrust Arena": "Wintrust Arena",
}

BIG_EVENT_TYPES = {"Chicago Marathon": "race", "NASCAR Street Race": "race",
                   "Air & Water Show": "show"}


def load_cells(path="data/external/cells.geojson", id_key="cell_id", name_key="cell_name"):
    """Outline (list of matplotlib Paths) and name of each cell (or zone)."""
    geo = json.load(open(path))
    cells, names = {}, {}
    for f in geo["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        cells[f["properties"][id_key]] = [Path(np.array(p[0])) for p in polys]
        names[f["properties"][id_key]] = f["properties"][name_key]
    return cells, names


def cell_table(data="data/"):
    """The 37 cells and the neighbourhoods (community areas) in each one."""
    _, zones = load_cells(data + "external/zones.geojson", "zone_id", "zone_name")
    z = pd.read_csv(data + "zone_to_cell.csv")
    z["area"] = z["zone_id"].map(zones)
    return (z.groupby(["cell_id", "cell_name"])["area"]
             .agg(lambda a: ", ".join(a)).rename("neighbourhoods").reset_index())


def cell_label(events):
    """Readable name of the event's cell: the cell name, or for a merged
    cell ("Group 19 (3 areas)") the neighbourhood of the event + the group."""
    group = events["cell_name"].str.startswith("Group")
    short = events["cell_name"].str.split(" (", regex=False).str[0]
    return events["cell_name"].mask(group, events["area"] + " (" + short + ")")


def cell_of(lat, lon, cells):
    """Id of the cell containing the point (lat, lon), or None."""
    for cell_id, paths in cells.items():
        if any(p.contains_point((lon, lat)) for p in paths):
            return cell_id
    return None


def size_class(capacity):
    """Same classes as in Gresi's notebook."""
    if pd.isna(capacity):
        return "Unknown"
    if capacity < 300:
        return "Small"
    if capacity < 1000:
        return "Medium"
    if capacity < 5000:
        return "Large"
    return "Very large"


def curated_events(data="data/"):
    """Hand-made lists: one row per day, all with 10,000+ people."""
    big = pd.read_csv(data + "external/big_events.csv")
    big["type"] = big["event"].map(BIG_EVENT_TYPES).fillna("festival")
    more = pd.read_csv(data + "external/more_events.csv")
    rows = []
    for w in pd.concat([big, more]).itertuples():
        for day in pd.date_range(w.start_date, w.end_date):
            rows.append({"date": day, "event": w.event, "type": w.type,
                         "venue": w.place, "source": w.source})
    return pd.DataFrame(rows).assign(size="Very large")


def sports_games(data="data/"):
    """Home games of the 7 pro teams, in their Chicago stadium."""
    mlb = pd.read_csv(data + "external/baseball_home_games.csv").assign(source="MLB Stats API")
    pro = pd.read_csv(data + "external/pro_sports_home_games.csv").assign(source="ESPN API")
    games = pd.concat([mlb, pro])
    games = games[games["venue"].isin(GAME_VENUES)]
    return pd.DataFrame({
        "date": pd.to_datetime(games["date"]),
        "event": games["team"] + " home game",
        "type": "sport",
        "venue": games["venue"].map(GAME_VENUES),
        "source": games["source"],
    })


def gresi_concerts(curated, data="data/"):
    """Gresi's concert list (showspace.org), without what the other lists cover."""
    c = pd.read_csv(data + "concerts/data/chicago_concerts.csv", parse_dates=["date"])
    c["venue"] = c["venue"].replace(VENUE_FIX)
    unknown = c["venue"] == "Unknown Venue"
    c.loc[unknown, "venue"] = c.loc[unknown, "special_event"].map(STREET_FESTIVALS)
    c = c.dropna(subset=["venue"])                        # "less fest": place unknown
    c = c[~c["venue"].isin(OUTSIDE_CHICAGO | STADIUMS)]
    # sets played inside a festival of the curated list (Riot Fest, Lollapalooza...)
    festival_days = set(zip(curated["date"], curated["venue"]))
    c = c[[(d, v) not in festival_days for d, v in zip(c["date"], c["venue"])]]
    street = c["special_event"].isin(STREET_FESTIVALS)
    return pd.DataFrame({
        "date": c["date"],
        "event": c["special_event"].where(street, c["headliner"]),
        "type": np.where(street, "festival", "concert"),
        "venue": c["venue"],
        "source": "showspace.org (Gresi)",
    })


def category(events):
    """Three groups for the plots: sports games, big events, concerts."""
    return pd.Series(np.select(
        [events["type"].eq("sport"), events["source"].str.startswith("http")],
        ["Sports games", "Big events"], "Concerts"), index=events.index)


def effect_group(events):
    """Name used to summarise the effect of each event (or group of events)."""
    groups = events["event"].where(events["type"] != "sport", events["event"] + "s")
    groups = groups.mask(events["type"].eq("stadium concert"), "Concerts at " + events["venue"])
    groups = groups.mask(events["type"].eq("protest"), "Protests (10,000+)")
    gresi = events["source"].str.contains("Gresi")
    size = events["size"].str.lower().replace("unknown", "unknown-size")
    groups = groups.mask(gresi & events["type"].eq("concert"), "Concerts, " + size + " venues")
    groups = groups.mask(gresi & events["type"].eq("festival"), "Street festivals")
    return groups


def build_events_table(data="data/"):
    """All the events 2022-2025 with their position, cell and size."""
    cells, names = load_cells(data + "external/cells.geojson")
    curated = curated_events(data)
    events = pd.concat([curated, sports_games(data), gresi_concerts(curated, data)],
                       ignore_index=True)
    events = events[events["date"].dt.year.between(*YEARS)]
    events = events.drop_duplicates(["date", "event", "venue"])   # e.g. doubleheaders

    venues = pd.read_csv(data + "concerts/data/chicago_venues.csv").drop_duplicates("venue")
    pos = {v: (la, lo) for v, la, lo in venues[["venue", "latitude", "longitude"]].values}
    pos.update(PLACES)
    events["lat"] = events["venue"].map(lambda v: pos[v][0])
    events["lon"] = events["venue"].map(lambda v: pos[v][1])
    zones, zone_names = load_cells(data + "external/zones.geojson", "zone_id", "zone_name")
    area = {v: zone_names.get(cell_of(la, lo, zones)) for v, (la, lo) in pos.items()}
    events["area"] = events["venue"].map(area)            # neighbourhood (community area)
    cell = {v: cell_of(la, lo, cells) for v, (la, lo) in pos.items()}
    events["cell_id"] = events["venue"].map(cell).astype("Int64")
    events["cell_name"] = events["cell_id"].map(names)

    events["capacity"] = events["venue"].map({**CONCERT_CAPACITY, **CAPACITY})
    events["size"] = events["size"].fillna(events["capacity"].map(size_class))
    events["date"] = events["date"].dt.strftime("%Y-%m-%d")
    cols = ["date", "event", "type", "venue", "lat", "lon", "area", "cell_id", "cell_name",
            "capacity", "size", "source"]
    return events[cols].sort_values(["date", "event"]).reset_index(drop=True)


if __name__ == "__main__":
    events = build_events_table()
    events.to_csv("data/external/events.csv", index=False)
    print(len(events), "event-days,", events["cell_id"].isna().sum(), "without a cell")
    print(events.groupby("type").size().to_string())
