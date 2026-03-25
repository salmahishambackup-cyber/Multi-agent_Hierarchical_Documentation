"""
Centralized configuration: constants, seeds, resource limits, and runtime parameters.
All magic numbers and environment settings live here.
"""

import os
import random
import numpy as np

# ──────────────────────────────────────────────
# Reproducibility
# ──────────────────────────────────────────────
GLOBAL_SEED = 42
random.seed(GLOBAL_SEED)
np.random.seed(GLOBAL_SEED)
os.environ["PYTHONHASHSEED"] = str(GLOBAL_SEED)

# ──────────────────────────────────────────────
# Resource Limits
# ──────────────────────────────────────────────
RAM_LIMIT_GB = 50
RAM_LIMIT_BYTES = RAM_LIMIT_GB * 1024 ** 3

try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (RAM_LIMIT_BYTES, RAM_LIMIT_BYTES))
except (ImportError, AttributeError, ValueError):
    pass

# ──────────────────────────────────────────────
# Pipeline Thresholds
# ──────────────────────────────────────────────
SMALL_POOL_THRESHOLD = 500_000          # PL rows below this → Option 1 (PSM+MILP)
OUTLIER_MB_THRESHOLD = 100_000          # MB columns capped at this
OUTLIER_ARPU_THRESHOLD = 1_000          # ARPU columns capped at this
MAX_PROPENSITY_WEIGHT = 10.0            # Density-ratio weight cap
MILP_TIME_LIMIT = 30                    # Seconds per MILP solve
WL_SUBSAMPLE_PERCENT = 0.25             # Weighted sampling fraction (Option 2)
LP_MIN_FRAC_OF_WL = 0.05                # LP minimum subset as fraction of WL

# ──────────────────────────────────────────────
# Columns Always Dropped
# ──────────────────────────────────────────────
COLUMNS_TO_DROP = ['YEARMO', 'MP_TYPE', 'COHORT_YEARMO']

# ──────────────────────────────────────────────
# Type Normalization Mapping
# ──────────────────────────────────────────────
TYPE_NORMALIZATION_MAP = {
    "MP": "PL", "PL_94": "PL", "PL_97": "PL",
    "CG1": "PL", "CG2": "PL",
    "WL_94": "WL", "WL_97": "WL",
}