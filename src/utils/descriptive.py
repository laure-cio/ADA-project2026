"""Helpers for the descriptive statistics (section 2 of results.ipynb)."""


def distance_to_reference(profiles, ref_years=(2022, 2025)):
    """For each year (row): sum over categories (columns) of |share(year) - mean share over the
    reference years|, in % points. Small = same rhythm as the reference period."""
    shares = 100 * profiles.div(profiles.sum(axis=1), axis=0)
    reference = shares.loc[ref_years[0]:ref_years[1]].mean()
    return (shares - reference).abs().sum(axis=1)