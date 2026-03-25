"""
Orchestration entry point.
Reads config → loads data → preprocesses → models → evaluates → saves.
"""

import os
import warnings
import pandas as pd
from Config import SMALL_POOL_THRESHOLD, WL_SUBSAMPLE_PERCENT, LP_MIN_FRAC_OF_WL
from Loggings import PipelineLogger
from Utils import safe_split
from Initialization import read_parquet
from Pre_processing import prepare_data, preprocess
from Modeling import (
    PropensitySubsetSelector,
    transform_features,
    xgboost_weights,
    weighted_sample,
    subset_match_via_lp,
)
from Evaluation import merge_before_after, plot_categorical_distributions, plot_numerical_distributions

# ──────────────────────────────────────────────
# Suppress noisy warnings
# ──────────────────────────────────────────────
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)


def main (table_name, table_path, index_column, type_column, P1_LIST, P2_LIST, P3_LIST, output_path):
    # ══════════════════════════════════════════
    # 0. Configuration 
    # ══════════════════════════════════════════
    p1 = safe_split(P1_LIST)
    p2 = safe_split(P2_LIST)
    p3 = safe_split(P3_LIST)

    # ══════════════════════════════════════════
    # 1. Initialize logger + tracing
    # ══════════════════════════════════════════
    logger = PipelineLogger(name=table_name)
    logger.start_tracing()
    logger.step_start("Total_Pipeline")

    logger.info(f"{'─' * 60}")
    logger.info(f"  Run: {table_name}")
    logger.info(f"{'─' * 60}")

    # ══════════════════════════════════════════
    # 2. Read data
    # ══════════════════════════════════════════
    table_df, _ = read_parquet(table_path, index_column, type_column, logger)

    # ══════════════════════════════════════════
    # 3. Data preparation (split PL/WL, identify columns)
    # ══════════════════════════════════════════
    pl_df, wl_df, cols_to_keep, num_cols, cat_cols, to_be_encoded = prepare_data(
        table_df, type_column, logger,
        prioritized_cols=[], exclusion_keywords=[],
    )

    # ══════════════════════════════════════════
    # 4. Preprocessing (outliers, encoding, downcasting)
    # ══════════════════════════════════════════
    processed_PL, processed_WL, ordinal_encoder = preprocess(
        pl_df[cols_to_keep], wl_df[cols_to_keep],
        num_cols, to_be_encoded, logger,
    )

    # ══════════════════════════════════════════
    # 5. Modeling (Option 1 or 2 based on pool size)
    # ══════════════════════════════════════════
    if len(processed_PL) <= SMALL_POOL_THRESHOLD:
        logger.info(f"PSM + MILP (pool size {len(processed_PL):,})")

        selector = PropensitySubsetSelector(
            num_cols, cat_cols, p1, p2, p3,
            logger=logger,
        )
        selected_subset = selector.run(processed_PL, processed_WL)
        subset_df = processed_PL.loc[selected_subset.index]

    else:
        logger.info(f"XGBoost + LP (pool size {len(processed_PL):,})")

        X, y = transform_features(processed_PL, processed_WL, num_cols, cat_cols, logger)
        weights = xgboost_weights(X, y, len(processed_PL), logger)
        pre_pool = weighted_sample(weights, processed_PL, processed_WL, logger,
                                   subsample_pct=WL_SUBSAMPLE_PERCENT)

        selected_pl = subset_match_via_lp(
            pre_pool, processed_WL, index_column,
            cat_cols, num_cols, logger,
            min_frac_of_wl=LP_MIN_FRAC_OF_WL,
        )
        subset_df = processed_PL.loc[selected_pl]

    # ══════════════════════════════════════════
    # 6. Evaluation
    # ══════════════════════════════════════════
    variances = merge_before_after(processed_PL, subset_df, processed_WL, num_cols, cat_cols)
    logger.info(f"\n{variances.to_string()}")

    selected_MP_IDs = pd.DataFrame({
        f"WL {index_column}": processed_WL.index,
    }).assign(**{f"PL {index_column}": pd.Series(subset_df.index)})

    # ══════════════════════════════════════════
    # 7. Save results
    # ══════════════════════════════════════════
    os.makedirs(output_path, exist_ok=True)
    selected_MP_IDs.to_csv(f"{output_path}/{table_name}_result.csv")
    variances.to_csv(f"{output_path}/{table_name}_variances.csv")

    cat_fig = plot_categorical_distributions(processed_WL, subset_df, cat_cols)
    num_fig = plot_numerical_distributions(processed_WL, subset_df, num_cols)
    cat_fig.savefig(f"{output_path}/{table_name}_cat_dist.png", dpi=300, bbox_inches="tight")
    num_fig.savefig(f"{output_path}/{table_name}_Num_dist.png", dpi=300, bbox_inches="tight")

    logger.info("Results saved")

    # ══════════════════════════════════════════
    # 8. Final summary
    # ══════════════════════════════════════════
    logger.step_end("Total_Pipeline")
    current_mb, peak_mb = logger.stop_tracing()
    logger.info(f"Memory — current: {current_mb:.2f} MB, peak: {peak_mb:.2f} MB")


if __name__ == "__main__":
    table_name = "Random_Request"
    table_path = "/hadoop/inetwork/iPred/Matching_Pair/Data/zip_files/part-00000-fb220605-e16c-4c83-b364-717bf4b3d67f-c000.snappy.parquet"
    index_column = "CONTRACT_KEY"
    type_column = "LIST_TYP"
    P1_LIST = "M_1_TOTAL_ARPU_ALLOCATED_TIERS;M_1_FLEX_ALLOCATED_AMOUNT_TIER;M_1_MI_MBS_TIERS;M_1_BUNDLE_CARDS_AMOUNT_TIERS;M_1_MI_MONTHLY_AMOUNT_TIER;M_1_VOICE_ACTIVITY_FLAG;M_0_ASSIGNMENT_MIX;M_1_TOTAL_ARPU_ALLOCATED;M_1_MI_ALLOCATED_ARPU;M_1_BC_AMOUNT;M_1_FLEX_PAYING_AMOUNT;M_1_MI_MONTHLY_AMOUNT;M_1_MI_MBS"
    P2_LIST = "M_2_TOTAL_ARPU_ALLOCATED_TIERS;M_2_FLEX_ALLOCATED_AMOUNT_TIER;M_2_MI_MBS_TIERS;M_2_BUNDLE_CARDS_AMOUNT_TIERS;M_1_FLEX_PAYING_TRX_TIERS;M_1_BC_TRX_TIERS;M_1_MI_MONTHLY_TRX_TIERS;M_2_TOTAL_ARPU_ALLOCATED;M_2_MI_ALLOCATED_ARPU;M_2_MI_MBS"
    P3_LIST = "M_2_MI_MONTHLY_AMOUNT_TIER;M_2_VOICE_ACTIVITY_FLAG;M_2_FLEX_PAYING_TRX_TIERS;M_2_BC_TRX_TIERS;M_2_BC_AMOUNT;M_2_FLEX_PAYING_AMOUNT;M_2_MI_MONTHLY_AMOUNT"


    output_path = f"/hadoop/inetwork/iPred/Matching_Pair/Data/Results/Requests/{table_name}"

    main(table_name, table_path, index_column, type_column, P1_LIST, P2_LIST, P3_LIST, output_path)