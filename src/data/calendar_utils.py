"""
calendar_utils.py
Functions and constants used to build the calendar dataset (calendar.csv)
and to test which calendar variables belong in the model of a "normal" day.

Nothing runs on import: the notebook decides what to call and with which data.
Named calendar_utils (not calendar) so it does not shadow Python's standard `calendar` module.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import holidays                                   # listed in pip_requirements.txt
from scipy import stats
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf

# ----------------------------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------------------------
BUFFER_DAYS = 45            # calendar built beyond the study period: the flag of 31 Dec depends on 1 Jan
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

MAJOR = {                   # flag name: text in holiday_name
    "is_new_year":         "New Year",
    "is_memorial_day":     "Memorial",
    "is_july_4":           "Independence Day",
    "is_labor_day":        "Labor",
    "is_thanksgiving_day": "Thanksgiving",
    "is_christmas":        "Christmas",
}

MINOR = {"MLK Day": "Martin Luther King", "Presidents' Day": "Washington", "Lincoln's Birthday": "Lincoln",
         "Pulaski Day": "Pulaski", "Juneteenth": "Juneteenth", "Columbus Day": "Columbus",
         "Election Day": "Election", "Veterans Day": "Veterans"}

# First and last day off of each CPS break (typed by hand from the CPS calendars)
SCHOOL_BREAKS = {
    "winter": [("2021-12-20", "2022-01-02"), ("2022-12-23", "2023-01-06"), ("2023-12-22", "2024-01-07"),
               ("2024-12-23", "2025-01-03"), ("2025-12-22", "2026-01-02")],
    "spring": [("2022-04-11", "2022-04-15"), ("2023-04-03", "2023-04-07"),
               ("2024-03-25", "2024-03-29"), ("2025-03-24", "2025-03-28")],
}

# Days that are not "ordinary" (excluded from the reference of a day)
NOT_ORDINARY = ["is_holiday", "is_major_holiday", "is_holiday_eve", "is_bridge_day", "is_long_weekend",
                "is_thanksgiving_week", "is_winter_break", "is_spring_break"]

# Columns of calendar.csv, in order
CALENDAR_COLUMNS = (["date", "year", "month", "day_of_week", "dow_n", "is_weekend", "is_holiday", "holiday_name",
                     "is_major_holiday"] + list(MAJOR) +
                    ["is_juneteenth", "is_holiday_eve", "is_bridge_day", "is_long_weekend",
                     "is_thanksgiving_week", "is_winter_break", "is_spring_break"])

# Flags counted per year in the sanity checks
FLAGS_ALL = (["is_holiday", "is_major_holiday"] + list(MAJOR) +
             ["is_holiday_eve", "is_bridge_day", "is_long_weekend",
              "is_thanksgiving_week", "is_winter_break", "is_spring_break"])

# Model
N_HARMONICS = 3
BOOL_FLAGS = (list(MAJOR) + ["is_juneteenth", "is_major_holiday", "is_holiday_eve", "is_bridge_day",
                             "is_long_weekend", "is_thanksgiving_week", "is_winter_break", "is_spring_break"])
SEASON_TERMS = " + ".join(f"sin{k} + cos{k}" for k in range(1, N_HARMONICS + 1))
HOLIDAY_TERMS = "is_christmas + is_thanksgiving_day + is_new_year + is_labor_day + is_thanksgiving_week"

# Known dates that must carry the right flags: (date, column, expected, description)
CHECKS = [
    ("2022-07-04", "is_july_4",            True,  "July 4th 2022"),
    ("2024-06-19", "is_july_4",            False, "Juneteenth 2024 is not July 4th"),
    ("2024-06-19", "is_holiday",           True,  "Juneteenth 2024 is a holiday..."),
    ("2024-06-19", "is_major_holiday",     False, "...but not a major one"),
    ("2023-05-29", "is_memorial_day",      True,  "Memorial Day 2023"),
    ("2025-09-01", "is_labor_day",         True,  "Labor Day 2025"),
    ("2024-11-28", "is_thanksgiving_day",  True,  "Thanksgiving 2024"),
    ("2023-12-25", "is_christmas",         True,  "Christmas 2023"),
    ("2023-01-02", "is_new_year",          True,  "New Year 2023 observed (Monday)"),
    ("2024-03-12", "is_holiday",           False, "ordinary Tuesday"),
    ("2024-03-27", "is_spring_break",      True,  "spring break 2024"),
    ("2024-04-10", "is_spring_break",      False, "after spring break 2024"),
    ("2023-12-27", "is_winter_break",      True,  "winter break 2023"),
    ("2024-11-27", "is_thanksgiving_week", True,  "Wednesday of Thanksgiving week 2024"),
    ("2024-11-27", "is_holiday_eve",       True,  "eve of Thanksgiving 2024"),
    ("2024-11-28", "is_holiday_eve",       False, "Thanksgiving 2024 is not an eve"),
    ("2024-12-24", "is_holiday_eve",       True,  "Christmas Eve 2024 (Tuesday)"),
    ("2025-12-31", "is_holiday_eve",       True,  "New Year's Eve 2025 (needs 1 Jan 2026: buffer)"),
    ("2023-12-31", "is_holiday_eve",       False, "New Year's Eve 2023 is a Sunday, not a working eve"),
    ("2022-05-29", "is_holiday_eve",       False, "Sunday before Memorial Day 2022 is not an eve"),
    ("2022-12-25", "is_holiday_eve",       False, "Christmas 2022 itself is not an eve"),
    ("2024-11-29", "is_bridge_day",        True,  "Friday after Thanksgiving 2024"),
    ("2023-07-03", "is_bridge_day",        True,  "Monday before July 4th 2023 (Tuesday)"),
    ("2024-07-05", "is_bridge_day",        True,  "Friday after July 4th 2024 (Thursday)"),
    ("2025-12-26", "is_bridge_day",        True,  "Friday after Christmas 2025 (Thursday)"),
    ("2025-07-03", "is_bridge_day",        False, "July 4th 2025 is a Friday: no bridge day"),
    ("2024-12-25", "is_long_weekend",      False, "Christmas Day 2024 is not a long weekend"),
    ("2025-08-30", "is_long_weekend",      True,  "Saturday before Labor Day 2025"),
]


# ----------------------------------------------------------------------------------------------
# 1. Building the calendar
# ----------------------------------------------------------------------------------------------
def build_calendar(start, end):
    """One row per day with the holiday flags (one per major holiday, plus Juneteenth)."""
    cal = pd.DataFrame({"date": pd.date_range(start, end, freq="D")})
    il = holidays.US(state="IL", years=range(cal.date.dt.year.min(), cal.date.dt.year.max() + 1))
    d = cal.date.dt.date
    cal["is_holiday"] = d.isin(il)
    cal["holiday_name"] = d.map(il).fillna("")
    not_juneteenth = ~cal.holiday_name.str.contains("Juneteenth")
    for flag, text in MAJOR.items():
        cal[flag] = cal.holiday_name.str.contains(text) & not_juneteenth
    cal["is_juneteenth"] = cal.holiday_name.str.contains("Juneteenth")      # minor holiday, candidate
    cal["is_major_holiday"] = cal[list(MAJOR)].any(axis=1)
    return cal


def add_school_breaks(cal):
    """Add is_winter_break and is_spring_break from SCHOOL_BREAKS."""
    cal = cal.copy()
    for name, periods in SCHOOL_BREAKS.items():
        cal[f"is_{name}_break"] = False
        for s, e in periods:
            cal.loc[(cal.date >= s) & (cal.date <= e), f"is_{name}_break"] = True
    return cal


def add_holiday_context(cal):
    """Eve, bridge day, long weekend and Thanksgiving week."""
    cal = cal.copy().sort_values("date").reset_index(drop=True)
    dow = cal.date.dt.dayofweek
    is_off = cal.is_major_holiday | (dow >= 5)
    working = ~is_off & ~cal.is_holiday                                  # ordinary working day

    # eve: working day just before a major holiday
    cal["is_holiday_eve"] = cal.is_major_holiday.shift(-1, fill_value=False) & working

    # bridge day: holiday on Tuesday -> the Monday before; holiday on Thursday -> the Friday after
    tue_hol = cal.is_major_holiday & (dow == 1)
    thu_hol = cal.is_major_holiday & (dow == 3)
    cal["is_bridge_day"] = (tue_hol.shift(-1, fill_value=False) | thu_hol.shift(1, fill_value=False)) & working

    # long weekend: non-holiday days of a block of 3+ consecutive days off that contains a major holiday
    block = (is_off != is_off.shift()).cumsum()
    block_len = is_off.groupby(block).transform("sum")
    has_hol = cal.is_major_holiday.groupby(block).transform("any")
    cal["is_long_weekend"] = is_off & (block_len >= 3) & has_hol & ~cal.is_major_holiday

    # Thanksgiving week: Monday to Sunday
    tg = cal.loc[cal.is_thanksgiving_day, "date"]
    week_starts = set(tg - pd.to_timedelta(tg.dt.dayofweek, unit="D"))
    cal["is_thanksgiving_week"] = (cal.date - pd.to_timedelta(dow, unit="D")).isin(week_starts)
    return cal


def build_full_calendar(start, end, buffer_days=BUFFER_DAYS):
    """Calendar with all flags, built `buffer_days` beyond [start, end] on each side (not yet cut)."""
    buffer = pd.Timedelta(days=buffer_days)
    return add_holiday_context(add_school_breaks(
        build_calendar(pd.Timestamp(start) - buffer, pd.Timestamp(end) + buffer)))


def finalize_calendar(calendar_full, start, end):
    """Cut the buffer, add the basic time columns, order the columns."""
    cal = calendar_full[(calendar_full.date >= start) & (calendar_full.date <= end)].copy()
    cal["year"] = cal.date.dt.year
    cal["month"] = cal.date.dt.month
    cal["day_of_week"] = cal.date.dt.day_name()
    cal["dow_n"] = cal.date.dt.dayofweek
    cal["is_weekend"] = cal.dow_n >= 5
    return cal[CALENDAR_COLUMNS].reset_index(drop=True)


def build_and_save_calendar(start, end, save_folder, buffer_days=BUFFER_DAYS, filename="calendar.csv"):
    """Whole pipeline in one call: build, cut, save. Returns (calendar_full, calendar)."""
    import os
    os.makedirs(save_folder, exist_ok=True)
    full = build_full_calendar(start, end, buffer_days)
    cal = finalize_calendar(full, start, end)
    cal.to_csv(os.path.join(save_folder, filename), index=False)
    return full, cal


def illinois_holiday_table(start, end):
    """Every Illinois holiday of the period with its weekday (section 1.1)."""
    il = holidays.US(state="IL", years=range(pd.Timestamp(start).year - 1, pd.Timestamp(end).year + 2))
    t = (pd.Series(il, name="holiday").rename_axis("date").reset_index()
           .assign(date=lambda d: pd.to_datetime(d.date)).sort_values("date"))
    t = t[(t.date >= start) & (t.date <= end)]
    t["weekday"] = t.date.dt.day_name()
    return t


# ----------------------------------------------------------------------------------------------
# 1.5 Sanity checks
# ----------------------------------------------------------------------------------------------
def check_structure(cal):
    """One row per day, no gap, no duplicate, no NA (raises AssertionError otherwise)."""
    assert cal.date.is_unique, "duplicated dates"
    assert (cal.date.diff().dropna() == pd.Timedelta(days=1)).all(), "gap in the dates"
    assert not cal.isna().any().any(), "NA values"


def run_checks(cal, checks=CHECKS):
    """Table of known dates with expected vs found flag."""
    ci = cal.set_index("date")
    chk = pd.DataFrame([{"date": d, "check": w, "column": c, "expected": e, "found": bool(ci.loc[d, c])}
                        for d, c, e, w in checks])
    chk["ok"] = np.where(chk.expected == chk.found, "OK", "PROBLEM")
    return chk


def check_context_flags(in_study):
    """Eves and bridge days are working days; long-weekend days are weekend days (raises otherwise)."""
    assert not (in_study[["is_holiday_eve", "is_bridge_day"]].any(axis=1) & (in_study.date.dt.dayofweek >= 5)).any(), \
        "an eve or bridge day falls on a weekend"
    assert not (in_study.is_long_weekend & (in_study.date.dt.dayofweek < 5) & ~in_study.is_holiday).any(), \
        "a long-weekend day is an ordinary weekday"


def list_flagged_days(in_study, cols=("is_holiday_eve", "is_bridge_day", "is_long_weekend")):
    """Print every eve, bridge day and long-weekend day with its weekday (to check by eye)."""
    for col in cols:
        d = in_study[in_study[col]]
        print(f"\n{col}: {len(d)} days")
        print(", ".join(d.date.dt.strftime("%Y-%m-%d %a")))


def flags_per_year(in_study):
    """Number of flagged days per year (a year with 0 of something is suspicious)."""
    return in_study.assign(year=in_study.date.dt.year).groupby("year")[FLAGS_ALL].sum().T


def school_break_table(calendar):
    """Length and number of weekdays inside the study period of each break."""
    rows = []
    for kind, periods in SCHOOL_BREAKS.items():
        for a, b in periods:
            d = calendar[(calendar.date >= a) & (calendar.date <= b)]
            rows.append({"break": kind, "first day": a, "last day": b, "days in study period": len(d),
                         "weekdays": int((~d.is_weekend).sum())})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# 3-4. Reference day, ratios, effect table
# ----------------------------------------------------------------------------------------------
def local_reference(df, excluded, col="n_trips", window=28, min_days=3):
    """Median of `col` over ordinary days with the same weekday within +-window days (flagged days excluded)."""
    t = (df.date - df.date.min()).dt.days.values
    dow, y, ok = df.dow_n.values, df[col].values.astype(float), ~excluded.values
    ref = np.full(len(df), np.nan)
    idx = np.arange(len(df))
    for i in range(len(df)):
        m = ok & (dow == dow[i]) & (np.abs(t - t[i]) <= window) & (idx != i)
        if m.sum() >= min_days:
            ref[i] = np.median(y[m])
    return ref


def add_reference_columns(merged):
    """Add ordinary, ref and ratio to the trips+calendar table (in place) and return the share check."""
    merged["ordinary"] = ~merged[NOT_ORDINARY].any(axis=1)
    merged["ref"] = local_reference(merged, ~merged.ordinary)
    merged["ratio"] = merged.n_trips / merged.ref
    return merged


def add_week_columns(merged):
    """week_ratio (trips / mean of the same complete ISO week), season, month_ratio. In place."""
    iso = merged.date.dt.isocalendar()
    merged["iso_week"] = iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)
    wk_mean = merged.groupby("iso_week").n_trips.transform("mean")
    wk_count = merged.groupby("iso_week").n_trips.transform("count")
    merged["week_ratio"] = np.where(wk_count == 7, merged.n_trips / wk_mean, np.nan)
    merged["season"] = np.select([merged.month.isin([12, 1, 2]), merged.month.isin([6, 7, 8])],
                                 ["Winter (Dec-Feb)", "Summer (Jun-Aug)"], "other")
    merged["month_ratio"] = merged.n_trips / merged.groupby("month").n_trips.transform("median")
    return merged


def occurrences(dates, gap_days=3):
    """Days less than gap_days apart belong to the same occurrence (one break, one holiday weekend...)."""
    d = pd.Series(dates).sort_values()
    return (d.diff().dt.days.fillna(999) > gap_days).cumsum().reindex(pd.Series(dates).index).values


def cluster_bootstrap_ci(values, cluster, n_boot=4000, seed=0):
    """95 % bootstrap CI of the median, resampling whole clusters (occurrences or weeks)."""
    rng = np.random.default_rng(seed)
    groups = [values[cluster == c] for c in np.unique(cluster)]
    meds = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        meds[b] = np.median(np.concatenate([groups[k] for k in pick]))
    return np.percentile(meds, [2.5, 97.5])


def boot_median_ci(values, n_boot=4000, seed=0):
    """95 % bootstrap CI of the median (independent days)."""
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(values, len(values))) for _ in range(n_boot)]
    return np.percentile(meds, [2.5, 97.5])


def boot_median_ratio_ci(a, b, n_boot=5000, seed=0):
    """95 % bootstrap CI of median(a) / median(b)."""
    rng = np.random.default_rng(seed)
    r = [np.median(rng.choice(a, len(a))) / np.median(rng.choice(b, len(b))) for _ in range(n_boot)]
    return np.percentile(r, [2.5, 97.5])


def weekend_season_difference(plot_df, n_boot=4000, seed=0):
    """Summer minus winter weekend ratio, resampling whole weeks. Returns (summer, winter, diff, lo, hi)."""
    rng = np.random.default_rng(seed)
    we = plot_df[plot_df.is_weekend]
    weeks = {s: [g.week_ratio.values for _, g in we[we.season.str.startswith(s)].groupby("iso_week")]
             for s in ["Summer", "Winter"]}
    diffs = []
    for _ in range(n_boot):
        summer = np.concatenate([weeks["Summer"][i] for i in rng.integers(0, len(weeks["Summer"]), len(weeks["Summer"]))])
        winter = np.concatenate([weeks["Winter"][i] for i in rng.integers(0, len(weeks["Winter"]), len(weeks["Winter"]))])
        diffs.append(np.median(summer) - np.median(winter))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    m_s = we[we.season.str.startswith("Summer")].week_ratio.median()
    m_w = we[we.season.str.startswith("Winter")].week_ratio.median()
    return m_s, m_w, m_s - m_w, lo, hi


def weekday_season_table(plot_df):
    """Median week_ratio of each weekday and season with a 95 % bootstrap CI."""
    rows = []
    for (sea, d), g in plot_df.groupby(["season", "day_of_week"]):
        lo, hi = boot_median_ci(g.week_ratio.values)
        rows.append({"season": sea, "day": d, "median": g.week_ratio.median(), "CI low": lo, "CI high": hi, "days": len(g)})
    t = pd.DataFrame(rows)
    t["day"] = pd.Categorical(t.day, DAYS, ordered=True)
    return t.sort_values(["season", "day"]).set_index(["season", "day"]).round(3)


def year_level_table(merged):
    """Level of each year vs the first year, season removed (month_ratio), with a 95 % bootstrap CI."""
    rng = np.random.default_rng(0)
    first = merged.loc[merged.year == merged.year.min(), "month_ratio"].values
    rows = []
    for y, g in merged.groupby("year"):
        v = g.month_ratio.values
        boot = [np.median(rng.choice(v, len(v))) / np.median(rng.choice(first, len(first))) for _ in range(5000)]
        rows.append({"year": y, f"level vs {merged.year.min()}": np.median(v) / np.median(first),
                     "CI low": np.percentile(boot, 2.5), "CI high": np.percentile(boot, 97.5)})
    return pd.DataFrame(rows).set_index("year").round(3)


def effect_table(groups, df, ratio="ratio"):
    """One row per group of days: typical change, cluster-bootstrap 95 % CI, Wilcoxon p (BH-adjusted), verdict.
    groups = list of (label, boolean mask aligned with df)."""
    rows = []
    for label, mask in groups:
        sub = df.loc[mask & df[ratio].notna(), ["date", ratio]]
        if len(sub) == 0:
            continue
        r = sub[ratio].values
        cl = occurrences(sub.date)
        med = np.median(r) - 1
        lo, hi = cluster_bootstrap_ci(r, cl) if len(np.unique(cl)) > 1 else (np.nan, np.nan)
        p = stats.wilcoxon(np.log(r)).pvalue if len(r) >= 6 else np.nan     # too few days -> no test
        same = np.mean((r - 1) * np.sign(med) > 0) if med != 0 else np.nan
        rows.append({"group": label, "days": len(r), "occurrences": len(np.unique(cl)), "typical change": med,
                     "CI low": lo - 1, "CI high": hi - 1, "share of days on same side": same, "p (Wilcoxon)": p})
    out = pd.DataFrame(rows)
    ok = out["p (Wilcoxon)"].notna()
    out["p adjusted (BH)"] = np.nan
    if ok.sum():
        out.loc[ok, "p adjusted (BH)"] = multipletests(out.loc[ok, "p (Wilcoxon)"], method="fdr_bh")[1]
    ci_yes = (out["CI low"] > 0) | (out["CI high"] < 0)
    p_disagrees = out["p adjusted (BH)"].notna() & (out["p adjusted (BH)"] >= 0.05)
    out["clear effect?"] = np.select(
        [out["CI low"].isna(), ci_yes & p_disagrees, ci_yes],
        ["not enough occurrences", "YES (fragile)", "YES"], default="no")
    return out


def fmt_effect(t):
    """Effect table with percentages and short p-values, for display."""
    f = t.copy()
    for c in ["typical change", "CI low", "CI high", "share of days on same side"]:
        f[c] = (f[c] * 100).round(1)
    for c in ["p (Wilcoxon)", "p adjusted (BH)"]:
        f[c] = f[c].map(lambda v: "" if pd.isna(v) else f"{v:.2g}")
    return f.rename(columns={"typical change": "change %", "CI low": "CI low %", "CI high": "CI high %",
                             "share of days on same side": "same side %"})


def effect_plot(groups, effects, title, df, ratio="ratio"):
    """Bars = median change, black line = 95 % CI, grey dots = each day."""
    fig, ax = plt.subplots(figsize=(11, 0.5 * len(effects) + 1.8))
    ypos = np.arange(len(effects))[::-1]
    masks = dict(groups)
    for y, (_, row) in zip(ypos, effects.iterrows()):
        r = (df.loc[masks[row["group"]], ratio].dropna() - 1) * 100
        ax.barh(y, row["typical change"] * 100, height=.55,
                color="#2f6db5" if row["typical change"] < 0 else "#e34948", alpha=.85, zorder=2)
        ax.scatter(r, np.full(len(r), y), s=18, color="#8a8a8a", zorder=4)
        if not np.isnan(row["CI low"]):
            ax.errorbar(row["typical change"] * 100, y,
                        xerr=[[(row["typical change"] - row["CI low"]) * 100], [(row["CI high"] - row["typical change"]) * 100]],
                        fmt="none", ecolor="#1a1a1a", elinewidth=1.8, capsize=4, zorder=5)
        ax.text(1.01, y, f"{row['typical change'] * 100:+.0f} %  ({row['occurrences']} occ.)",
                transform=ax.get_yaxis_transform(), va="center", fontsize=9, color="#4d4d4d")
    ax.axvline(0, color="#4d4d4d", lw=1)
    ax.set_yticks(ypos); ax.set_yticklabels(effects.group)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:+.0f} %")); ax.grid(axis="y", visible=False)
    ax.set_xlabel("trips vs ordinary days of the same weekday nearby   (bar = median, black line = 95 % CI, grey dots = each day)")
    ax.set_title(title, loc="left", fontweight="bold")
    plt.subplots_adjust(right=.78, left=.3, bottom=.16); plt.show()


def holiday_groups(m):
    """The groups of section 4.4 (major holidays and days around them)."""
    return [
        ("New Year's Day",                 m.is_new_year),
        ("Memorial Day",                   m.is_memorial_day),
        ("July 4th",                       m.is_july_4),
        ("Labor Day",                      m.is_labor_day),
        ("Thanksgiving Day",               m.is_thanksgiving_day),
        ("Christmas",                      m.is_christmas),
        ("Eve of a holiday",               m.is_holiday_eve),
        ("Bridge day",                     m.is_bridge_day),
        ("Long weekend (weekend days)",    m.is_long_weekend),
        ("Thanksgiving week (other days)", m.is_thanksgiving_week & ~m.is_thanksgiving_day & ~m.is_bridge_day),
    ]


def minor_groups(m):
    """The groups of section 4.5 (minor holidays, weekdays only)."""
    nm = m.holiday_name.fillna("")
    return [(label, m.is_holiday & ~m.is_major_holiday & ~m.is_weekend & nm.str.contains(text))
            for label, text in MINOR.items()]


def break_groups(m):
    """The groups of section 4.6 (school breaks)."""
    wd = ~m.is_weekend
    winter_only = m.is_winter_break & ~m.is_major_holiday & ~m.is_holiday_eve & ~m.is_bridge_day
    return [
        ("Winter break, weekdays (without holidays)", winter_only & wd),
        ("Winter break, weekends",                    winter_only & ~wd),
        ("Spring break, weekdays",                    m.is_spring_break & wd),
    ]


def break_periods(kind, merged):
    """Breaks with at least 3 days inside the study period."""
    out = []
    for a, b in SCHOOL_BREAKS[kind]:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        if ((merged.date >= a) & (merged.date <= b)).sum() >= 3:
            out.append((a, b))
    return out


def rider_effects_table(groups, merged):
    """Section 4.7: the same effect table for members and casual riders."""
    for col in ["n_member", "n_casual"]:
        merged[f"ratio_{col}"] = merged[col] / local_reference(merged, ~merged.ordinary, col=col)
    rows = []
    for col, label in [("ratio_n_member", "members"), ("ratio_n_casual", "casual")]:
        t = effect_table(groups, merged, ratio=col)[["group", "typical change", "CI low", "CI high", "clear effect?"]]
        rows.append(t.set_index("group").add_prefix(f"{label}: "))
    out = pd.concat(rows, axis=1)
    for c in out.columns:
        if "clear" not in c:
            out[c] = (out[c] * 100).round(1)
    return out


# ----------------------------------------------------------------------------------------------
# 5. Model (negative binomial)
# ----------------------------------------------------------------------------------------------
def add_features(df):
    """Fourier terms, weekend x season, 0/1 flags, year as text."""
    df = df.copy()
    doy = df.date.dt.dayofyear
    for k in range(1, N_HARMONICS + 1):
        df[f"sin{k}"] = np.sin(2 * np.pi * k * doy / 365.25)
        df[f"cos{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
    df["wkend_sin1"] = df.is_weekend.astype(int) * df.sin1
    df["wkend_cos1"] = df.is_weekend.astype(int) * df.cos1
    for c in BOOL_FLAGS:
        df[c] = df[c].astype(int)
    df["year_c"] = df.year.astype(str)
    return df


def core_formulas():
    """Formulas F0..F3 of section 5.1."""
    F0 = f"n_trips ~ C(year_c) + {SEASON_TERMS}"
    F1 = F0 + " + C(day_of_week)"
    F2 = F1 + " + wkend_sin1 + wkend_cos1"
    F3 = F2 + " + " + HOLIDAY_TERMS
    return F0, F1, F2, F3


def fit_nb(formula, data):
    return smf.negativebinomial(formula, data).fit(disp=False, maxiter=500, method="bfgs")


def cv_error(formula, md_df, k=5, block=14):
    """Blocked k-fold CV (14-day blocks): median absolute % error on the held-out days."""
    fold = (np.arange(len(md_df)) // block) % k
    errs = []
    for f in range(k):
        train, test = md_df[fold != f], md_df[fold == f]
        mu = fit_nb(formula, train).predict(test)
        errs.append(np.abs(test.n_trips.values - mu.values) / test.n_trips.values)
    return np.median(np.concatenate(errs)) * 100


def compare(models, md_df):
    """models: list of (name, formula, base); base = name of the model it is compared with (None = no test).
    Returns (table with AIC, BIC, alpha, LR test, CV error; dict of fitted models)."""
    rows, fits = [], {}
    for name_, fo, base in models:
        res = fit_nb(fo, md_df); fits[name_] = res
        row = {"model": name_, "parameters": len(res.params), "AIC": res.aic, "BIC": res.bic, "alpha": res.params["alpha"]}
        if base is not None:
            prev = fits[base]
            lr = 2 * (res.llf - prev.llf)
            row["vs"] = base.split()[0]
            row["ΔAIC"] = res.aic - prev.aic
            row["p (LR test)"] = stats.chi2.sf(lr, len(res.params) - len(prev.params))
        row["CV error %"] = cv_error(fo, md_df)
        rows.append(row)
    return pd.DataFrame(rows).set_index("model"), fits


def keep_rule(cand_table, core_name):
    """Candidate kept if AIC goes down, LR test p < 0.05 and CV error does not go up."""
    cv_core = cand_table.loc[core_name, "CV error %"]
    return np.where(cand_table.index == core_name, "",
                    np.where((cand_table["ΔAIC"] < 0) & (cand_table["p (LR test)"] < 0.05) &
                             (cand_table["CV error %"] <= cv_core), "YES", "no"))
