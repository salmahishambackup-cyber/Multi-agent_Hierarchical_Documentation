"""
Data loading and column identification.
Reads Parquet files and classifies columns into numerical / categorical.
"""

import gc
import pandas as pd
from Config import COLUMNS_TO_DROP
from Loggings import PipelineLogger


def read_parquet(file_path, index_column, type_column, logger: PipelineLogger):
    """
    Read a Parquet file with pyarrow backend, set the index,
    and return the DataFrame plus the list of feature columns.
    """
    logger.step_start("read_parquet")

    df = pd.read_parquet(
        file_path,
        dtype_backend="pyarrow",
        engine="pyarrow",
        memory_map=True,
    )
    if index_column in df.columns:
        df.set_index(index_column, inplace=True)

    feature_cols = [c for c in df.columns if type_column not in c]

    logger.info(f"Loaded DataFrame with shape {df.shape}")
    gc.collect()
    logger.step_end("read_parquet")

    return df, feature_cols


def identify_column_types(df, logger: PipelineLogger, exclusion_keywords=None):
    """
    Classify columns into numerical and categorical.
    Drops predefined housekeeping columns in-place.

    Returns:
        num_cols, cat_cols, to_be_encoded
    """
    exclusion_keywords = exclusion_keywords or []
    df.drop(columns=COLUMNS_TO_DROP, errors="ignore", inplace=True)

    cols = df.columns

    # Flag / Mix columns are always categorical
    flag_cols = list(cols[cols.str.contains("Flag", case=False, na=False)])
    mix_cols = list(cols[cols.str.contains("Mix", case=False, na=False)])

    # Non-numeric, non-decimal[pyarrow] columns → categorical candidates
    to_be_encoded = []
    for col, dtype in df.dtypes.items():
        dtype_str = str(dtype)
        if ("decimal" in dtype_str and "[pyarrow]" in dtype_str):
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        to_be_encoded.append(col)

    cat_candidates = set(to_be_encoded) | set(flag_cols) | set(mix_cols)

    # Apply exclusion keywords
    if exclusion_keywords:
        ek = tuple(k.lower() for k in exclusion_keywords)
        cat_cols = [c for c in cat_candidates if not any(k in c.lower() for k in ek)]
        num_cols = [c for c in cols if c not in cat_candidates and not any(k in c.lower() for k in ek)]
    else:
        cat_cols = list(cat_candidates)
        num_cols = [c for c in cols if c not in cat_candidates]

    logger.info(f"Identified {len(num_cols)} numerical and {len(cat_cols)} categorical features")
    logger.info(f"Flag columns: {flag_cols}")
    logger.info(f"To be encoded: {to_be_encoded}")

    gc.collect()
    return num_cols, cat_cols, to_be_encoded