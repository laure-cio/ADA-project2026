"""Helpers for the descriptive statistics (section 2 of results.ipynb)."""

import numpy as np
def distance_to_reference(profiles, ref_years=(2022, 2025)):
    """For each year (row): sum over categories (columns) of |share(year) - mean share over the
    reference years|, in % points. Small = same rhythm as the reference period."""
    shares = 100 * profiles.div(profiles.sum(axis=1), axis=0)
    reference = shares.loc[ref_years[0]:ref_years[1]].mean()
    return (shares - reference).abs().sum(axis=1)

def cv_per_group(cells, slot=None):
    """Coefficient of variation of counts across similar cells (same zone, month, weekday/weekend,
    and time slot if given), with the CV expected from pure chance (Poisson: 1/sqrt(mean))."""
    d = cells.copy()
    d["month"] = d["date"].dt.to_period("M")
    d["weekend"] = d["date"].dt.dayofweek >= 5
    keys = ["zone_id", "month", "weekend"] + ([slot] if slot else [])
    g = d.groupby(keys, observed=True)["n_trips"].agg(["mean", "std"])
    g = g[g["mean"] > 0]
    g["cv"] = g["std"] / g["mean"]
    g["cv_poisson"] = 1 / np.sqrt(g["mean"])
    return g