"""Do events change the number of trips in their cell?

A simple baseline to explore the events (for P3, the anomaly scores of the
negative binomial model replace it):
- "normal" for a cell and a day = median of the same weekday 1 to 4 weeks
  before and after, leaving out holidays and the days with a big event in
  that cell (at least 3 such days are needed, otherwise no normal);
- ratio = trips / normal, for each cell and for the whole city;
- relative ratio = cell ratio / city ratio, with the city compared on the same
  days as the cell, so that a rainy or hot day, which changes the whole city,
  does not look like an event effect.
"""
import warnings

import numpy as np
import pandas as pd

OFFSETS = [-28, -21, -14, -7, 7, 14, 21, 28]
MIN_NEIGHBOURS = 3
BIG = ("Very large",)              # events of 5,000+ people, left out of the normal
MAIN_CELL = 0.9                    # a group of events is named after a cell if this share of its days is there
YEARS = (2022, 2025)
HOLIDAY_FLAGS = ["is_holiday", "is_major_holiday", "is_holiday_eve", "is_winter_break",
                 "is_thanksgiving_week"]


def load_daily_counts(path="data/daily_counts_cells.parquet", years=(2021, 2026)):
    """Trips per day: a table with one column per cell, and the city total.

    One year of margin on each side, so that the 2022-2025 days have neighbours.
    The calendar and the event lists only cover 2022-2025, so the margin days
    are not filtered.
    """
    d = pd.read_parquet(path, columns=["date", "cell_id", "n_trips"])
    d["date"] = pd.to_datetime(d["date"])
    d = d[d["date"].dt.year.between(*years)]
    cells = d.pivot(index="date", columns="cell_id", values="n_trips").asfreq("D").fillna(0)
    return cells, cells.sum(axis=1)


def holiday_dates(path="data/external/calendar.csv"):
    """Holidays, their eves, winter break and Thanksgiving week (from the calendar)."""
    cal = pd.read_csv(path, parse_dates=["date"])
    return pd.DatetimeIndex(cal.loc[cal[HOLIDAY_FLAGS].any(axis=1), "date"])


def holiday_labels(path="data/external/calendar.csv"):
    """Name of the holiday (or holiday period) of each day, "" otherwise."""
    cal = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    label = cal["holiday_name"].where(cal["is_holiday"], "").fillna("")
    for flag, name in [("is_holiday_eve", "eve of a holiday"), ("is_thanksgiving_week", "Thanksgiving week"),
                       ("is_winter_break", "winter break")]:
        label = label.mask(label.eq("") & cal[flag], name)
    return label


def event_days(events, index, columns, sizes=BIG):
    """Table like the trip table: True where the cell has an event that day."""
    mask = pd.DataFrame(False, index=index, columns=columns)
    e = events[events["size"].isin(sizes)]
    for date, cell in set(zip(pd.to_datetime(e["date"]), e["cell_id"])):
        if date in mask.index and cell in mask.columns:
            mask.loc[date, cell] = True
    return mask


def normal_level(trips, skip=None):
    """Median of the same weekday 1 to 4 weeks before and after.

    trips: Series or DataFrame with a daily index. skip: same shape, True for
    the days left out of the median (they still get a normal level).
    """
    clean = trips if skip is None else trips.where(~skip)
    shifted = np.stack([clean.shift(-o).to_numpy(dtype=float) for o in OFFSETS])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)    # no neighbour left -> NaN
        med = np.nanmedian(shifted, axis=0)
    med[(~np.isnan(shifted)).sum(axis=0) < MIN_NEIGHBOURS] = np.nan
    if isinstance(trips, pd.Series):
        return pd.Series(med, index=trips.index)
    return pd.DataFrame(med, index=trips.index, columns=trips.columns)


def relative_ratios(cells, city, events, holidays=()):
    """Ratios to normal for every day: a dict of date x cell tables.

    Keys: "relative" (cell ratio / city ratio on the same comparison days),
    "cell", "city" (a Series: the city against its own comparison days),
    "normal" (normal number of trips) and "skip" (days with a big event in
    the cell, or a holiday).
    holidays: dates left out of the normal of every cell and of the city.
    """
    off = cells.index.isin(pd.to_datetime(holidays))
    events_mask = event_days(events, cells.index, cells.columns).to_numpy()
    skip = pd.DataFrame(events_mask | off[:, None], index=cells.index, columns=cells.columns)
    normal = normal_level(cells, skip)
    cell_ratio = cells / normal.where(normal > 0)
    city_ratio = city / normal_level(city, pd.Series(off, index=city.index))
    # the city on the same comparison days as each cell, so that their weather cancels out
    city_table = pd.DataFrame({c: city for c in cells.columns})
    return {"relative": cell_ratio / (city_table / normal_level(city_table, skip)),
            "cell": cell_ratio, "city": city_ratio, "normal": normal, "skip": skip}


def lookup(table, rows, cols):
    """Values of a table at the given (row label, column label) pairs."""
    i = table.index.get_indexer(rows)
    j = table.columns.get_indexer(cols)
    values = table.to_numpy(dtype=float)[i, j]
    return np.where((i < 0) | (j < 0), np.nan, values)


def noise_range(r):
    """10% and 90% of the relative ratio on days without a big event or a
    holiday, for each cell and month (2022-2025): how much a normal day moves."""
    rel = r["relative"].where(~r["skip"])
    rel = rel[rel.index.year.isin(range(YEARS[0], YEARS[1] + 1))]
    by_month = rel.groupby(rel.index.month)
    return by_month.quantile(0.1), by_month.quantile(0.9)


def add_ratios(events, r):
    """The events table with the ratios of its cell and day."""
    e = events.copy()
    dates = pd.to_datetime(e["date"])
    for key in ("relative", "cell", "normal"):
        e[key] = lookup(r[key], dates, e["cell_id"])
    e["city"] = r["city"].reindex(dates).to_numpy()
    low, high = noise_range(r)
    e["noise_low"] = lookup(low, dates.dt.month, e["cell_id"])
    e["noise_high"] = lookup(high, dates.dt.month, e["cell_id"])
    return e


def event_effects(events, r, group="event", cell_col="cell_name", n_boot=2000, seed=0):
    """Median ratios on the days of each event (or group of events).

    cell_col: column used to name the event's cell in the result ("several
    cells" if no cell has at least MAIN_CELL of the days).
    low, high: 95% bootstrap interval of the median relative ratio.
    noise_low, noise_high: normal day-to-day range (10%-90%) of the same cells
    and months. above_noise: share of the event days above that range
    (10% expected by chance).
    """
    e = add_ratios(events, r).dropna(subset=["relative"])
    rng = np.random.default_rng(seed)
    rows = []
    for name, g in e.groupby(group):
        x = g["relative"].to_numpy()
        boot = np.median(rng.choice(x, (n_boot, len(x))), axis=1)
        where = g[cell_col].value_counts(normalize=True)
        rows.append({
            group: name, "cell": where.index[0] if where.iloc[0] >= MAIN_CELL else "several cells",
            "days": len(x),
            "relative": np.median(x),
            "low": np.percentile(boot, 2.5), "high": np.percentile(boot, 97.5),
            "noise_low": g["noise_low"].median(), "noise_high": g["noise_high"].median(),
            "above_noise": (x > g["noise_high"]).mean(),
            "cell_ratio": g["cell"].median(), "city_ratio": g["city"].median(),
            "normal_trips": g["normal"].median(),
        })
    return pd.DataFrame(rows).sort_values("relative", ascending=False).reset_index(drop=True)


def top_anomalies(r, n=30, min_normal=100, highest=True):
    """The n cell-days furthest from normal, 2022-2025.

    A cell-day is high only if the cell is above normal both in its own trips
    and compared with the city, so it is ranked by the smaller of the two ratios
    (the larger one for the lowest days). Otherwise a storm that empties the city
    would make a cell that loses a little less look like a rise.
    Only cell-days with a normal level of at least min_normal trips, because
    in very quiet cells a few trips more or less already make a big ratio.
    """
    both = np.minimum if highest else np.maximum
    score = both(r["relative"], r["cell"]).where(r["normal"] >= min_normal)
    score = score[score.index.year.isin(range(YEARS[0], YEARS[1] + 1))]
    s = (score.rename_axis("date").rename_axis("cell_id", axis=1).reset_index()
              .melt(id_vars="date", value_name="score").dropna())
    s = s.sort_values("score", ascending=not highest).head(n).reset_index(drop=True)
    s["relative"] = lookup(r["relative"], s["date"], s["cell_id"])
    s["cell_ratio"] = lookup(r["cell"], s["date"], s["cell_id"])
    return s.drop(columns="score")


def explain(anomalies, events, names=None, holidays=None):
    """Add the events found in the same cell on the same day (and the holiday,
    if holidays, a Series from holiday_labels, is given)."""
    e = events.assign(date=pd.to_datetime(events["date"]))
    found = e.groupby(["date", "cell_id"])["event"].agg(lambda x: ", ".join(sorted(set(x))))
    a = anomalies.copy()
    a["events"] = [found.get((d, c), "") for d, c in zip(a["date"], a["cell_id"])]
    if holidays is not None:
        a["holiday"] = a["date"].map(holidays).fillna("")
    if names is not None:
        a.insert(2, "cell_name", a["cell_id"].map(names))
    return a


def match_rate(r, events, n=100, min_normal=100):
    """Share of the top-n anomalies with an event in their cell that day, compared
    with chance: the share of days with an event in the same cell, month and weekday."""
    has = event_days(events, r["relative"].index, r["relative"].columns,
                     sizes=events["size"].unique())
    top = top_anomalies(r, n=n, min_normal=min_normal)
    hit = np.mean(lookup(has.astype(float), top["date"], top["cell_id"]))
    eligible = (r["normal"] >= min_normal) & r["relative"].notna()
    eligible = eligible[eligible.index.year.isin(range(YEARS[0], YEARS[1] + 1))]
    days = has.reindex_like(eligible).astype(float).where(eligible)
    chance = np.mean([days.loc[(days.index.month == d.month) & (days.index.dayofweek == d.dayofweek), c].mean()
                      for d, c in zip(top["date"], top["cell_id"])])
    return {"top": n, "with_event": hit, "chance": chance, "times_chance": hit / chance}
