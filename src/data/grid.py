"""Zones, hybrid grid and trips per cell (section 3 of results.ipynb)."""
import geopandas as gpd
import pandas as pd


def load_zones(path="data/external/community_areas.geojson"):
    """Chicago's 77 community areas: zone_id, zone_name, geometry (City of Chicago Data Portal, igwz-8jzy)."""
    zones = gpd.read_file(path)
    zones = (zones[["area_numbe", "community", "geometry"]]
             .rename(columns={"area_numbe": "zone_id", "community": "zone_name"}))
    zones["zone_id"] = zones["zone_id"].astype(int)
    zones["zone_name"] = zones["zone_name"].str.title()          # "ROGERS PARK" -> "Rogers Park"
    return zones.sort_values("zone_id").reset_index(drop=True)


def daily_zone_table(zone_hourly, start="2022-01-01", end="2025-12-31", n_zones=77):
    """Trips per day: one row per day, one column per zone (zone-days with 0 trips included)."""
    zh = zone_hourly[(zone_hourly["zone_id"] > 0)
                     & (zone_hourly["hour"] >= start) & (zone_hourly["hour"] < pd.Timestamp(end) + pd.Timedelta(days=1))]
    daily = zh.groupby([zh["hour"].dt.normalize().rename("date"), "zone_id"])["n_trips"].sum().unstack()
    return daily.reindex(index=pd.date_range(start, end, freq="D"), columns=range(1, n_zones + 1), fill_value=0).fillna(0)


def build_hybrid_grid(daily, zones, target=90, min_trips=20, months=range(4, 11)):
    """Hybrid grid: merge neighbouring quiet zones (quietest first) until each cell has at least
    `min_trips` trips on `target` % of the days in `months` (default April–October).
    Groups are only merged with quiet neighbours. Returns (zone_to_cell, cells still below the target)."""
    zm = zones.to_crs(epsg=26916).set_index("zone_id")
    zone_name = zones.set_index("zone_id")["zone_name"]
    geom = zm.geometry.make_valid().buffer(5)                     # neighbours = outlines touching (5 m tolerance)
    neighbours = {z: set(zm.index[geom.intersects(geom[z])]) - {z} for z in zm.index}
    in_months = daily.index.month.isin(months)

    def pct_days_ok(zone_list):
        return 100 * (daily.loc[in_months, zone_list].sum(axis=1) >= min_trips).mean()

    groups = {z: [z] for z in zm.index}                           # start: every zone is its own group

    def group_of(z):
        return next(g for g, members in groups.items() if z in members)

    stuck = set()                                                 # quiet groups with no quiet neighbour left
    while True:
        scores = {g: pct_days_ok(m) for g, m in groups.items()}
        failing = {g: s for g, s in scores.items() if s < target}
        to_fix = {g: s for g, s in failing.items() if g not in stuck}
        if not to_fix:
            break
        g = min(to_fix, key=to_fix.get)                                    # the quietest group
        nb = {group_of(n) for z in groups[g] for n in neighbours[z]} - {g}  # its neighbouring groups
        candidates = [h for h in nb if h in failing]                       # only quiet neighbours
        if not candidates:
            stuck.add(g)
            continue
        h = min(candidates, key=lambda k: daily[groups[k]].values.sum())   # the neighbour with fewest trips
        groups[g] += groups.pop(h)
        stuck.discard(h)

    below = pd.DataFrame([{"cell": ", ".join(zone_name[groups[g]]), "% days ok": round(pct_days_ok(groups[g]))}
                          for g in stuck if g in groups])

    rows = []
    for k, members in enumerate(sorted(groups.values(), key=min), start=1):
        name = zone_name[members[0]] if len(members) == 1 else f"Group {k} ({len(members)} areas)"
        rows += [{"zone_id": z, "cell_id": k, "cell_name": name} for z in members]
    return pd.DataFrame(rows), below


def cell_outlines(zones, zone_to_cell):
    """One outline per cell (union of its zones), for maps."""
    return zones.merge(zone_to_cell, on="zone_id").dissolve(by="cell_id").reset_index()


def daily_counts_cells(zone_hourly, zone_to_cell):
    """Trips per cell per day (cell-days with 0 trips included); zone 0 (outside Chicago) is left out."""
    zh = zone_hourly[zone_hourly["zone_id"] > 0].copy()
    zh["date"] = zh["hour"].dt.normalize()
    counts = (zh.merge(zone_to_cell[["zone_id", "cell_id"]], on="zone_id")
                .groupby(["date", "cell_id"])[["n_trips", "n_casual", "n_electric"]].sum())
    cell_names = zone_to_cell[["cell_id", "cell_name"]].drop_duplicates()
    dates = pd.date_range(zh["date"].min(), zh["date"].max(), freq="D")
    grid = pd.MultiIndex.from_product([dates, cell_names["cell_id"]], names=["date", "cell_id"])
    return counts.reindex(grid, fill_value=0).reset_index().merge(cell_names, on="cell_id")