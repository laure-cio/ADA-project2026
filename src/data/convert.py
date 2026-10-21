"""Step 3 - Convert text dates to real datetimes."""
import re

import pandas as pd

# Date formats found in the Divvy files: (pattern of the text, format for pandas)
DATE_FORMATS = [
    (r"^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}$",       "%m/%d/%Y %H:%M"),     # 6/30/2014 23:57
    (r"^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2}$", "%m/%d/%Y %H:%M:%S"),  # 9/30/2016 23:59:58
    (r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$",             "%Y-%m-%d %H:%M"),     # 2013-06-27 12:11
    (r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",        "ISO8601"),            # 2018-07-01 00:00:03(.289)
]


def detect_date_format(values):
    """Return the pandas format matching the first non-empty date of a column."""
    first = values.dropna().iloc[0].strip()
    for pattern, fmt in DATE_FORMATS:
        if re.match(pattern, first):
            return fmt
    raise ValueError(f"Unknown date format: {first!r}")


def parse_dates(df, columns=("started_at", "ended_at")):
    """Convert the date columns of one harmonized file to datetimes.

    Returns the dataframe and the number of values that could not be converted.
    """
    n_failed = 0
    for col in columns:
        fmt = detect_date_format(df[col])
        converted = pd.to_datetime(df[col].str.strip(), format=fmt, errors="coerce")
        n_failed += converted.isna().sum() - df[col].isna().sum()
        df[col] = converted
    return df, int(n_failed)