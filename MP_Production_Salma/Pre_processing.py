"""
Data preparation, PL/WL splitting, encoding, outlier filtering, and type downcasting.
"""

import gc
import numpy as np
import pandas as pd

from Config import (
    TYPE_NORMALIZATION_MAP,
    OUTLIER_MB_THRESHOLD,
    OUTLIER_ARPU_THRESHOLD,
)
from Loggings import PipelineLogger
from Utils import best_int_dtype
from Initialization import identify_column_types


# ═══════════════════════════════════════════════
# PL / WL Splitting
# ═══════════════════════════════════════════════

def _determine_split_column(df, split_on):
    split_col = "TYPE_INDEX" if "TYPE_INDEX" in df.columns else split_on
    if split_col not in df.columns:
        raise ValueError(f"Split column '{split_col}' not found in DataFrame")
    return split_col


def _keep_prioritized_columns(df, split_col, prioritized_cols):
    if not prioritized_cols:
        return df
    keep_set = set(prioritized_cols + [split_col])
    return df.loc[:, df.columns.intersection(keep_set)]


def _normalize_split_column(df, split_col):
    df[split_col] = df[split_col].replace(TYPE_NORMALIZATION_MAP)
    return df


def _split_pl_wl(df, split_col):
    s = df[split_col].astype(str, copy=False).str.upper()
    pl_mask = s.eq("PL").to_numpy()

    pl_df = df.loc[pl_mask].copy()
    wl_df = df.loc[~pl_mask].copy()

    pl_df.drop(columns=[split_col], inplace=True, errors="ignore")
    wl_df.drop(columns=[split_col], inplace=True, errors="ignore")

    del df, s, pl_mask
    gc.collect()
    return pl_df, wl_df


def _remove_constant_mix_cols(pl_df, cat_cols):
    mix_cols = [c for c in cat_cols if "MIX" in c.upper() and c in pl_df.columns]
    if not mix_cols:
        return cat_cols
    nunique = pl_df[mix_cols].nunique(dropna=True)
    constant = nunique[nunique == 1].index.tolist()
    if constant:
        cat_cols = [c for c in cat_cols if c not in constant]
    return cat_cols


def prepare_data(df, split_on, logger: PipelineLogger,
                 prioritized_cols=None, exclusion_keywords=None):
    """
    Full data-preparation pipeline:
      1. Determine split column
      2. Keep prioritized columns (if any)
      3. Normalize type labels
      4. Split into PL / WL
      5. Identify num / cat columns
      6. Remove constant MIX columns
    """
    logger.step_start("Data_preparation")
    prioritized_cols = prioritized_cols or []
    exclusion_keywords = exclusion_keywords or []

    split_col = _determine_split_column(df, split_on)
    df = _keep_prioritized_columns(df, split_col, prioritized_cols)
    df = _normalize_split_column(df, split_col)

    pl_df, wl_df = _split_pl_wl(df, split_col)
    logger.info(f"PL shape: {pl_df.shape}, WL shape: {wl_df.shape}")

    num_cols, cat_cols, to_be_encoded = identify_column_types(
        wl_df, logger, exclusion_keywords
    )
    cat_cols = _remove_constant_mix_cols(pl_df, cat_cols)
    to_be_encoded = list(set(cat_cols))
    cols_to_keep = list({*num_cols, *cat_cols})

    logger.step_end("Data_preparation")
    return pl_df, wl_df, cols_to_keep, num_cols, cat_cols, to_be_encoded


# ═══════════════════════════════════════════════
# Categorical Encoding
# ═══════════════════════════════════════════════

class CatEncoder:
    """Stores category mappings and supports inverse transform."""

    def __init__(self, cat_map):
        self.categories_ = cat_map

    def inverse_transform(self, df):
        df = df.copy()
        for col, cats in self.categories_.items():
            if col not in df:
                continue
            codes = pd.to_numeric(df[col], errors="coerce").astype("Int32")
            valid = (codes >= 0) & (codes < len(cats))
            out = pd.Series(pd.NA, index=df.index, dtype="object")
            out[valid] = cats.take(codes[valid].to_numpy())
            df[col] = out
        return df


def _build_categories(pl_series, wl_series):
    return pd.Index(pd.concat([pl_series, wl_series], ignore_index=True).unique())


def _encode_series(series, categories, dtype):
    codes = pd.Categorical(series, categories=categories).codes
    return pd.Series(codes, index=series.index).mask(lambda x: x < 0).astype(dtype)


def _encode_cat_features(pl_df, wl_df, cat_cols, logger: PipelineLogger):
    logger.info(f"Encoding {len(cat_cols)} categorical columns")
    cat_map = {}

    for col in cat_cols:
        if col not in pl_df or col not in wl_df:
            logger.warning(f"Skipping missing column: {col}")
            continue

        pl_s = pl_df[col].fillna("None")
        wl_s = wl_df[col].fillna("None")
        cats = _build_categories(pl_s, wl_s)
        cat_map[col] = cats

        dtype = best_int_dtype(len(cats))
        pl_df[col] = _encode_series(pl_s, cats, dtype)
        wl_df[col] = _encode_series(wl_s, cats, dtype)

    return pl_df, wl_df, CatEncoder(cat_map)


# ═══════════════════════════════════════════════
# Outlier Filtering
# ═══════════════════════════════════════════════

def _build_outlier_mask(df, mb_cols, arpu_cols):
    def _all_le(df, cols, thr):
        if not cols:
            return np.ones(len(df), dtype=bool)
        return (df[cols].to_numpy(copy=False) <= thr).all(axis=1)

    mask = _all_le(df, mb_cols, OUTLIER_MB_THRESHOLD) & _all_le(df, arpu_cols, OUTLIER_ARPU_THRESHOLD)

    # Skip filtering if index is customer_key or rnk
    if df.index.name and df.index.name.lower() in ("customer_key", "rnk"):
        mask = np.ones(len(df), dtype=bool)
    return mask


# ═══════════════════════════════════════════════
# Full Preprocessing Pipeline
# ═══════════════════════════════════════════════

def preprocess(pl_df, wl_df, num_cols, to_be_encoded, logger: PipelineLogger):
    """
    End-to-end preprocessing:
      1. Outlier filtering (MB / ARPU thresholds)
      2. Downcast numerics to float32
      3. Encode categorical columns
    """
    logger.step_start("Data_Preprocessing")
    logger.info(f"Shapes before: PL={pl_df.shape}, WL={wl_df.shape}")

    # 1) Outlier masks
    mb_cols = [c for c in (num_cols or []) if "_MB" in c and c in pl_df.columns and c in wl_df.columns]
    arpu_cols = [c for c in (num_cols or []) if "_ARPU" in c and c in pl_df.columns and c in wl_df.columns]

    pl_mask = _build_outlier_mask(pl_df, mb_cols, arpu_cols)
    wl_mask = _build_outlier_mask(wl_df, mb_cols, arpu_cols)
    logger.info(f"Outliers filtered: PL={(~pl_mask).sum()}, WL={(~wl_mask).sum()}")

    pl_df = pl_df.loc[pl_mask]
    wl_df = wl_df.loc[wl_mask]

    # 2) Downcast numerics
    for c in num_cols:
        if c in pl_df.columns and c in wl_df.columns:
            try:
                pl_df[c] = pl_df[c].astype("float32", copy=False)
                wl_df[c] = wl_df[c].astype("float32", copy=False)
            except Exception:
                pl_df[c] = pl_df[c].to_numpy(dtype=np.float32, copy=True)
                wl_df[c] = wl_df[c].to_numpy(dtype=np.float32, copy=True)

    # 3) Encode categoricals
    enc_cols = [c for c in (to_be_encoded or []) if c in pl_df.columns and c in wl_df.columns]
    if enc_cols:
        try:
            pl_df[enc_cols] = pl_df[enc_cols].astype("object", copy=False)
            wl_df[enc_cols] = wl_df[enc_cols].astype("object", copy=False)
        except Exception as e:
            logger.warning(f"Column cast failed: {e}")

        pl_df, wl_df, encoder = _encode_cat_features(pl_df, wl_df, enc_cols, logger)
    else:
        logger.warning("No categorical columns to encode")
        encoder = None

    logger.info(f"Shapes after: PL={pl_df.shape}, WL={wl_df.shape}")
    logger.step_end("Data_Preprocessing")
    return pl_df, wl_df, encoder