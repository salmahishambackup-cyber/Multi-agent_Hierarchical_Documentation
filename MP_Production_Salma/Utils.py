"""
Small, stateless helper functions shared across modules.
No heavy imports — keeps the dependency footprint minimal.
"""

import pandas as pd


def safe_split(val, sep=";"):
    """Split a delimited string into a list, handling NaN/None gracefully."""
    if pd.isna(val):
        return []
    return [x for x in str(val).split(sep) if x]


def best_int_dtype(n_categories):
    """Return the smallest nullable integer dtype that fits *n_categories* codes."""
    if n_categories <= 127:
        return "Int8"
    elif n_categories <= 32_767:
        return "Int16"
    return "Int32"