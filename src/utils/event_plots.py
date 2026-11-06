"""Plots for the events part (section 4.3 of results.ipynb).

A "cell" is one of the 37 zones of the grid: one neighbourhood (community
area), or a group of small neighbourhoods merged together ("Group 19").
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

from src.data.events import category
from src.models.event_effects import YEARS, lookup

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
LAND = "#f0efec"
LAND_2 = "#dddbd2"
# One color per group, checked for colour-blind readers (blue, orange, aqua)
COLORS = {"Sports games": "#2a78d6", "Big events": "#eb6834", "Concerts": "#1baf7a"}
TICKS = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, 8]


def use_style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT_2, "axes.titlecolor": TEXT,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": TEXT_2, "ytick.labelcolor": TEXT_2,
        "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 2, "lines.solid_capstyle": "round",
        "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "semibold",
        "axes.titlelocation": "left", "legend.frameon": False,
    })


def times_axis(ax, axis="x", ticks=TICKS):
    """Log scale labelled as multiples of normal (x0.5, x1, x2...)."""
    getattr(ax, f"set_{axis}scale")("log")
    a = getattr(ax, f"{axis}axis")
    a.set_major_locator(FixedLocator(ticks))
    a.set_minor_locator(NullLocator())
    a.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}"))


def category_legend(ax, cats, **kw):
    handles = [Line2D([], [], marker="o", linestyle="", markersize=8, markerfacecolor=COLORS[c],
                      markeredgecolor=SURFACE, label=c) for c in cats]
    return ax.legend(handles=handles, **kw)


def titles(fig, title, subtitle):
    """Title and one line of explanation above the whole figure."""
    fig.suptitle(title, x=0.01, y=0.995, ha="left", va="top", fontsize=12,
                 fontweight="semibold", color=TEXT)
    fig.text(0.01, 0.955, subtitle, ha="left", va="top", fontsize=9.5, color=TEXT_2)


def cell_shapes(cells_path):
    """(cell_id, cell_name, list of polygons) for each cell."""
    shapes = []
    for f in json.load(open(cells_path))["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        shapes.append((f["properties"]["cell_id"], f["properties"]["cell_name"],
                       [np.array(p[0]) for p in polys]))
    return shapes


def centroid(xy):
    """Centre of a polygon (shoelace formula)."""
    x, y = xy[:, 0], xy[:, 1]
    cross = x * np.roll(y, -1) - np.roll(x, -1) * y
    a = cross.sum() / 2
    return (((x + np.roll(x, -1)) * cross).sum() / (6 * a),
            ((y + np.roll(y, -1)) * cross).sum() / (6 * a))


def map_axes(ax):
    ax.set_aspect(1 / np.cos(np.radians(41.85)))
    ax.autoscale_view()
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def plot_cells(cells_path="data/external/cells.geojson"):
    """The 37 cells of the grid, with their names."""
    fig, ax = plt.subplots(figsize=(7, 8.5))
    for cell_id, name, polys in cell_shapes(cells_path):
        group = name.startswith("Group")
        ax.add_collection(PatchCollection([Polygon(p, closed=True) for p in polys],
                                          facecolor=LAND_2 if group else LAND,
                                          edgecolor="#a9a79f", linewidth=0.7))
        big = max(polys, key=lambda p: np.ptp(p[:, 0]) * np.ptp(p[:, 1]))
        x, y = centroid(big)
        label = name.split(" (")[0].replace(" ", "\n") if group else name.replace(" ", "\n")
        ax.text(x, y, label, ha="center", va="center", fontsize=6.5, color=TEXT, linespacing=0.95)
    map_axes(ax)
    ax.legend(handles=[Patch(facecolor=LAND, edgecolor="#a9a79f", label="One neighbourhood"),
                       Patch(facecolor=LAND_2, edgecolor="#a9a79f",
                             label="Group of small neighbourhoods")],
              loc="lower left")
    ax.set_title("Our grid: Chicago split into 37 cells")
    return fig


def plot_event_map(events, cells_path="data/external/cells.geojson", labels=None):
    """Cells of the grid and event places, sized by number of event-days."""
    patches = [Polygon(p, closed=True) for _, _, polys in cell_shapes(cells_path) for p in polys]
    e = events.assign(category=category(events))
    venues = e.groupby(["venue", "lat", "lon", "category"]).size().rename("days").reset_index()
    fig, ax = plt.subplots(figsize=(7, 8.5))
    ax.add_collection(PatchCollection(patches, facecolor=LAND, edgecolor="#c3c2b7", linewidth=0.6))
    for cat in ["Concerts", "Sports games", "Big events"]:
        v = venues[venues["category"] == cat]
        ax.scatter(v["lon"], v["lat"], s=20 + 25 * np.sqrt(v["days"]), color=COLORS[cat],
                   edgecolors=SURFACE, linewidths=1.2, alpha=0.9, zorder=3)
    for venue, (dx, dy, ha) in (labels or {}).items():
        x, y = venues.loc[venues["venue"] == venue, ["lon", "lat"]].iloc[0]
        ax.annotate(venue, (x, y), (x + dx, y + dy), ha=ha, va="center", fontsize=8.5, color=TEXT,
                    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8, shrinkA=0, shrinkB=4))
    map_axes(ax)
    leg = category_legend(ax, ["Big events", "Sports games", "Concerts"], loc="lower left",
                          title="Event type", alignment="left")
    ax.add_artist(leg)
    sizes = [Line2D([], [], marker="o", linestyle="", color=MUTED, markeredgecolor=SURFACE,
                    markersize=np.sqrt(20 + 25 * np.sqrt(n)), label=f"{n} days") for n in (1, 25, 300)]
    ax.legend(handles=sizes, loc="lower left", bbox_to_anchor=(0, 0.17), title="Event-days 2022-2025",
              alignment="left", labelspacing=1.2)
    ax.set_title("Where the events are: one dot per place, on the 37 cells")
    return fig


def plot_event_calendar(events):
    """Event-days per month and per weekday (average per year)."""
    e = events.assign(category=category(events), date=pd.to_datetime(events["date"]))
    n_years = YEARS[1] - YEARS[0] + 1
    order = ["Sports games", "Concerts", "Big events"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [12, 7]})
    for ax, key, labels in [
        (axes[0], e["date"].dt.month, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                                       "Sep", "Oct", "Nov", "Dec"]),
        (axes[1], e["date"].dt.dayofweek, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
    ]:
        counts = pd.crosstab(key, e["category"]).reindex(columns=order).fillna(0) / n_years
        counts = counts.reindex(range(1, 13) if len(labels) == 12 else range(7), fill_value=0)
        bottom = np.zeros(len(counts))
        for cat in order:
            ax.bar(np.arange(len(counts)), counts[cat], bottom=bottom, width=0.6, color=COLORS[cat],
                   edgecolor=SURFACE, linewidth=1, label=cat)
            bottom += counts[cat].to_numpy()
        ax.set_xticks(np.arange(len(labels)), labels)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", length=0)
    axes[0].set_ylabel("Event-days per year")
    axes[0].set_title("Per month")
    axes[1].set_title("Per weekday")
    axes[1].legend(loc="upper left", reverse=True)
    fig.suptitle("When the events are: mostly in summer and on weekends", x=0.01, ha="left",
                 fontsize=12, fontweight="semibold", color=TEXT)
    fig.tight_layout()
    return fig


def plot_example(cells, r, cell, start, end, days, label, title):
    """Daily trips of one cell next to its normal, with the event days marked."""
    trips = cells.loc[start:end, cell]
    normal = r["normal"].loc[start:end, cell]
    rel = r["relative"].loc[start:end, cell]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 4.6), sharex=True,
                                 gridspec_kw={"height_ratios": [2, 1]})
    for ax in (a1, a2):
        for d in pd.to_datetime(days):
            if trips.index[0] <= d <= trips.index[-1]:
                ax.axvspan(d - pd.Timedelta(hours=12), d + pd.Timedelta(hours=12),
                           color=COLORS["Big events"], alpha=0.15, linewidth=0)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
    a1.plot(trips.index, trips, color=COLORS["Sports games"], label="Trips that day")
    a1.plot(normal.index, normal, color=MUTED, linewidth=1.5,
            label="Normal (same weekday, ±1-4 weeks)")
    a1.set_ylabel("Trips per day\nin the cell")
    handles, _ = a1.get_legend_handles_labels()
    handles.append(Patch(color=COLORS["Big events"], alpha=0.3, label=label))
    a1.legend(handles=handles, loc="upper left", ncols=3)
    a1.set_ylim(0, 1.3 * max(trips.max(), normal.max()))
    a2.plot(rel.index, rel, color=COLORS["Sports games"])
    a2.axhline(1, color=MUTED, linewidth=1)
    a2.set_ylabel("Compared with\nnormal (×1)")
    wide = rel.max() / rel.min() > 4
    times_axis(a2, "y", ticks=[0.5, 1, 2, 4, 8] if wide else TICKS)
    a2.set_ylim(min(0.5, 0.9 * rel.min()), max(2, 1.1 * rel.max()))
    a1.set_title(title)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_effects(effects):
    """One row per event: median relative ratio, its 95% interval, and the
    normal day-to-day range of the same cell."""
    eff = effects.sort_values("relative").reset_index(drop=True)
    y = np.arange(len(eff))
    fig, ax = plt.subplots(figsize=(9.5, 0.3 * len(eff) + 2))
    ax.barh(y, eff["noise_high"] - eff["noise_low"], left=eff["noise_low"], height=0.55,
            color=GRID, linewidth=0)
    ax.hlines(y, eff["low"], eff["high"], color=TEXT_2, linewidth=1.5)
    ax.scatter(eff["relative"], y, s=64, c=eff["category"].map(COLORS), edgecolors=SURFACE,
               linewidths=1.5, zorder=3)
    ax.axvline(1, color=MUTED, linewidth=1)
    times_axis(ax, "x")
    ax.set_xlim(0.5, 10)
    ax.set_yticks(y, eff["group"] + "  ·  " + eff["cell"] + "  ·  " + eff["days"].astype(str) + " days")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.set_xlabel("Trips in the event's cell on event days (×1 = a normal day there)")
    handles = [Line2D([], [], marker="o", linestyle="", markersize=8, markerfacecolor=COLORS[c],
                      markeredgecolor=SURFACE, label=c) for c in COLORS]
    handles += [Line2D([], [], color=TEXT_2, linewidth=1.5, label="95% interval of the median"),
                Patch(color=GRID, label="Normal ups and downs of the cell (10-90%)")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.3, -0.05), ncols=3)
    titles(fig, "Which events bring more bike trips to their cell?",
           "Each row: event  ·  its cell (one of the 37 zones of our grid)  ·  number of days. "
           "The change of the whole city that day is taken out.")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def plot_detectability(effects, labels=None):
    """Effect of each event against the normal number of trips in its cell.

    labels: {group: (dx, dy)} offsets in points for the names to show.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(effects["normal_trips"], effects["relative"], s=20 + 8 * np.sqrt(effects["days"]),
               c=effects["category"].map(COLORS), edgecolors=SURFACE, linewidths=1.2, zorder=3)
    for group, (dx, dy) in (labels or {}).items():
        row = effects[effects["group"] == group].iloc[0]
        ax.annotate(group, (row["normal_trips"], row["relative"]), (dx, dy),
                    textcoords="offset points", fontsize=8.5, color=TEXT_2,
                    ha="left" if dx >= 0 else "right", va="center",
                    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8, shrinkA=0, shrinkB=3))
    ax.set_xscale("log")
    ax.set_xlabel("Trips on a normal day in the event's cell (log scale)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    times_axis(ax, "y")
    ax.set_ylabel("Trips on event days (×1 = normal)")
    ax.axhline(1, color=MUTED, linewidth=1)
    ax.grid()
    ax.set_axisbelow(True)
    category_legend(ax, list(COLORS), loc="upper right")
    ax.set_title("A crowd is easier to see in a quiet cell than in a busy one")
    fig.tight_layout()
    return fig


def plot_game_days(r, events, teams, cell_col="cell_name"):
    """Relative ratio of the stadium cell on game days and on other days of the
    same months (2022-2025), one pair of boxes per team."""
    rel = r["relative"]
    in_years = rel.index.year.isin(range(YEARS[0], YEARS[1] + 1))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    names = []
    for i, team in enumerate(teams):
        g = events[events["event"] == f"{team} home game"]
        cell = g["cell_id"].mode()[0]
        on = lookup(rel, pd.to_datetime(g["date"]), g["cell_id"])
        months = rel.index.month.isin(pd.to_datetime(g["date"]).dt.month.unique())
        game = rel.index.isin(pd.to_datetime(g["date"]))
        off = rel.loc[in_years & months & ~game & ~r["skip"][cell].to_numpy(), cell]
        for data, pos, color in [(off.dropna(), 3 * i, LAND), (on[~np.isnan(on)], 3 * i + 1, COLORS["Sports games"])]:
            ax.boxplot(data, positions=[pos], widths=0.7, patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor=color, edgecolor=TEXT_2, linewidth=1),
                       medianprops=dict(color=TEXT, linewidth=1.5),
                       whiskerprops=dict(color=TEXT_2, linewidth=1), capprops=dict(color=TEXT_2, linewidth=1))
        names.append(f"{team}\n{g[cell_col].mode()[0]}")
    ax.set_xticks([3 * i + 0.5 for i in range(len(teams))], names)
    ax.axhline(1, color=MUTED, linewidth=1)
    times_axis(ax, "y")
    ax.set_ylabel("Trips in the stadium's cell\n(×1 = normal day)")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0)
    ax.legend(handles=[Patch(facecolor=LAND, edgecolor=TEXT_2, label="Other days, same months"),
                       Patch(facecolor=COLORS["Sports games"], edgecolor=TEXT_2, label="Home game days")],
              loc="upper right")
    ax.set_title("Home games: outdoor stadiums show up in their cell, indoor arenas barely")
    fig.tight_layout()
    return fig
