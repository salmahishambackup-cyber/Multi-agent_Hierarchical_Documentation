"""
Variance evaluation and distribution plotting.
"""

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from Loggings import PipelineLogger


# ═══════════════════════════════════════════════
# Variance Calculations
# ═══════════════════════════════════════════════

def _calc_numerical_variance(subset, whitelist, num_cols):
    results = {}
    for col in num_cols:
        avg_sub = pd.to_numeric(subset[col], errors="coerce").mean()
        avg_wl = pd.to_numeric(whitelist[col], errors="coerce").mean()

        if pd.isna(avg_sub) or pd.isna(avg_wl) or avg_wl == 0:
            score = 0
        else:
            score = 1 - (avg_sub / avg_wl)

        results[col] = {
            "KPI": col,
            "Given_formula": f"{abs(round(score * 100))}%",
        }
    return pd.DataFrame.from_dict(results, orient="index").reset_index(drop=True)


def _calc_categorical_variance(subset, whitelist, cat_cols):
    results = {}
    for col in cat_cols:
        dist_sub = subset[col].value_counts(normalize=True).sort_index()
        dist_wl = whitelist[col].value_counts(normalize=True).sort_index()

        dist_sub = dist_sub.reindex(dist_wl.index, fill_value=0)
        dist_wl = dist_wl.reindex(dist_sub.index, fill_value=0)

        score = (dist_sub - dist_wl).abs().sum()
        results[col] = f"{abs(round(score * 100))}%"

    return pd.DataFrame(
        list(results.items()), columns=["KPI", "Given_formula"]
    ).reset_index(drop=True)


def calc_variance(subset, whitelist, num_cols, cat_cols):
    """Compute combined numerical + categorical variance metrics."""
    num_df = _calc_numerical_variance(subset, whitelist, num_cols)
    cat_df = _calc_categorical_variance(subset, whitelist, cat_cols)
    combined = (
        pd.concat([num_df, cat_df], axis=0)
        .sort_values(by="KPI")
        .reset_index(drop=True)
    )
    combined["Given_formula"] = (
        combined["Given_formula"].str.replace("%", "", regex=False).astype(float)
    )
    return combined


def evaluate(subset, whitelist, num_cols, cat_cols, logger: PipelineLogger):
    """Evaluate subset vs whitelist and log pass/fail summary."""
    pct = (len(subset) / len(whitelist)) * 100
    logger.info(f"Subset is {pct:.1f}% of whitelist ({len(subset)} / {len(whitelist)})")

    var_df = calc_variance(subset, whitelist, num_cols, cat_cols)

    passed = (var_df["Given_formula"] <= 1).sum()
    needs_work = var_df["Given_formula"].isin([2, 3]).sum()
    failed = (var_df["Given_formula"] > 3).sum()

    logger.info(f"Passed (≤1%): {passed}")
    logger.info(f"Needs enhancement (2-3%): {needs_work}")
    logger.info(f"Not matching (>3%): {failed}")

    if failed > 0:
        logger.info(var_df[var_df["Given_formula"] > 3].to_string())

    return var_df


def merge_before_after(pl_df, subset_df, wl_df, num_cols, cat_cols):
    """Side-by-side variance comparison: full PL vs selected subset."""
    before = calc_variance(pl_df, wl_df, num_cols, cat_cols).rename(
        columns={"Given_formula": "Var Before"}
    )
    after = calc_variance(subset_df, wl_df, num_cols, cat_cols).rename(
        columns={"Given_formula": "Var After"}
    )
    return before.merge(after, on="KPI", how="outer")


# ═══════════════════════════════════════════════
# Distribution Plots
# ═══════════════════════════════════════════════

def plot_numerical_distributions(wl_df, pl_df, num_cols, bins=50):
    """Histogram comparison of WL vs PL for each numerical column."""
    start = time.time()
    n_cols_plot = 3
    n_rows = (len(num_cols) + n_cols_plot - 1) // n_cols_plot
    fig, axes = plt.subplots(n_rows, n_cols_plot, figsize=(15, 3 * n_rows))

    if n_rows == 1:
        axes = [axes] if n_cols_plot == 1 else axes
    else:
        axes = axes.flatten()

    for i, col in enumerate(num_cols):
        if i >= len(axes):
            break
        if col not in wl_df.columns or col not in pl_df.columns:
            continue

        wl_data = wl_df[col].dropna()
        pl_data = pl_df[col].dropna()

        axes[i].hist(pl_data, bins=bins, alpha=0.6, label="PL",
                     density=True, color="red", edgecolor="black", linewidth=0.5)
        axes[i].hist(wl_data, bins=bins, alpha=0.6, label="WL",
                     density=True, color="blue", edgecolor="black", linewidth=0.5)

        wl_mean, pl_mean = wl_data.mean(), pl_data.mean()
        axes[i].axvline(pl_mean, color="red", linestyle="--", linewidth=1.5,
                        label=f"PL mean: {pl_mean:.2f}")
        axes[i].axvline(wl_mean, color="blue", linestyle="--", linewidth=1.5,
                        label=f"WL mean: {wl_mean:.2f}")

        axes[i].set_title(col)
        axes[i].legend(fontsize=8)
        axes[i].tick_params(axis="x", rotation=45)

    for i in range(len(num_cols), len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    plt.show()
    print(f"Numerical plots took: {time.time() - start:.2f}s")
    return fig


def plot_categorical_distributions(wl_df, pl_df, cat_cols, top_n=15):
    """Bar-chart comparison of WL vs PL for each categorical column."""
    start = time.time()
    n_cols_plot = 4
    n_rows = (len(cat_cols) + n_cols_plot - 1) // n_cols_plot
    fig, axes = plt.subplots(n_rows, n_cols_plot, figsize=(16, 3 * n_rows))

    if n_rows == 1:
        axes = [axes] if n_cols_plot == 1 else axes.flatten()
    else:
        axes = axes.flatten()

    for i, col in enumerate(cat_cols):
        if i >= len(axes) or col not in wl_df.columns:
            continue

        wl_pct = (wl_df[col].value_counts(normalize=True) * 100).head(top_n)
        pl_pct = (pl_df[col].value_counts(normalize=True) * 100).head(top_n)

        all_cats = wl_pct.index.union(pl_pct.index)
        plot_df = pd.DataFrame({
            "WL (%)": wl_pct.reindex(all_cats, fill_value=0),
            "PL (%)": pl_pct.reindex(all_cats, fill_value=0),
        })

        plot_df.plot(kind="bar", ax=axes[i], alpha=0.8, color=["blue", "red"])
        axes[i].set_title(f"{col} Distribution (%)")
        axes[i].set_ylabel("Percentage (%)")
        axes[i].tick_params(axis="x", rotation=45)
        axes[i].legend()
        axes[i].grid(axis="y", alpha=0.3)
        for container in axes[i].containers:
            axes[i].bar_label(container, fmt=" %.0f%%", label_type="edge",
                              fontsize=8, rotation=90)

    for i in range(len(cat_cols), len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    plt.show()
    print(f"Categorical plots took: {time.time() - start:.2f}s")
    return fig