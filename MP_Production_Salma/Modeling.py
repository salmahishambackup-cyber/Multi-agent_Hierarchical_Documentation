"""
Two modeling pipelines:

(small pool ≤ 500K):  PropensitySubsetSelector  →  PSM + MILP
(large pool > 500K):  XGBoost density ratio + Weighted sampling + LP
"""

import math
import random
import warnings

import numpy as np
import pandas as pd
import pulp
from scipy import sparse
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from xgboost import XGBClassifier

from Config import GLOBAL_SEED, MAX_PROPENSITY_WEIGHT, MILP_TIME_LIMIT, WL_SUBSAMPLE_PERCENT, LP_MIN_FRAC_OF_WL
from Loggings import PipelineLogger


# ═══════════════════════════════════════════════════════════════
# (small pool ≤ 500K): Propensity Score Matching + MILP
# ═══════════════════════════════════════════════════════════════

class PropensitySubsetSelector:
    """PSM-based candidate filtering → MILP distributional matching."""

    def __init__(self, num_cols, cat_cols, p1, p2, p3,
                 logger: PipelineLogger = None, max_weight=MAX_PROPENSITY_WEIGHT):
        self.num_cols = num_cols
        self.cat_cols = cat_cols
        self.priority = {
            c: (3.0 if c in p1 else (2.0 if c in p2 else 1.0))
            for c in num_cols + cat_cols
        }
        self.logger = logger or PipelineLogger("PSS")
        self.max_weight = max_weight
        self.model = LogisticRegression(
            penalty="l2", C=0.1, solver="sag",
            max_iter=50, tol=1e-5,
            random_state=GLOBAL_SEED, n_jobs=-1,
        )

    # ── Feature matrix for MILP ──

    def _build_feature_matrix(self, pool_df, wl_df, max_cat_levels=50):
        idx = pool_df.index
        comps, comp_names, comp_weights = [], [], {}

        for c in self.num_cols:
            if c not in pool_df or c not in wl_df:
                continue
            comps.append(pool_df[c].astype(float).fillna(0.0))
            comp_names.append(c)
            comp_weights[c] = self.priority.get(c, 1.0)

        for c in self.cat_cols:
            if c not in pool_df or c not in wl_df:
                continue
            vc = wl_df[c].fillna("__MISSING__").astype(str).value_counts()
            cats = list(vc.index[:max_cat_levels])
            for cat in cats:
                col_name = f"{c}___{cat}"
                comp_names.append(col_name)
                comp_weights[col_name] = self.priority.get(c, 1.0)
                comps.append(
                    (pool_df[c].fillna("__MISSING__").astype(str) == cat).astype(float)
                )
            if len(vc) > max_cat_levels:
                other_mask = ~pool_df[c].fillna("__MISSING__").astype(str).isin(cats)
                comps.append(other_mask.astype(float))
                comp_names.append(f"{c}___OTHER")
                comp_weights[f"{c}___OTHER"] = self.priority.get(c, 1.0)

        A_df = pd.concat(comps, axis=1) if comps else pd.DataFrame(index=idx)
        A_df.columns, A_df.index = comp_names, idx

        target_means = {}
        for comp in A_df.columns:
            if "___" in comp:
                base, cat = comp.split("___", 1)
                wl_series = wl_df[base].fillna("__MISSING__").astype(str)
                if cat == "OTHER":
                    topk = wl_series.value_counts().index[:max_cat_levels]
                    target_means[comp] = float((~wl_series.isin(topk)).mean())
                else:
                    target_means[comp] = float((wl_series == cat).mean())
            else:
                target_means[comp] = float(wl_df[comp].astype(float).mean())

        return A_df, target_means, comp_weights

    # ── MILP solver ──

    def milp_mean_match(self, pool_df, wl_df, iterate_S_list=None, max_time=MILP_TIME_LIMIT):
        if pool_df.empty:
            return [], float("inf"), None

        A_df, target_means, comp_weights = self._build_feature_matrix(pool_df, wl_df)
        A, idx_list = A_df.to_numpy(float), list(A_df.index)

        wl_n = len(wl_df)
        if iterate_S_list is None:
            iterate_S_list = [
                max(1, math.ceil(0.05 * wl_n)),
                max(1, int(0.35 * wl_n)),
            ]

        best_obj, best_sel, best_model = float("inf"), [], None
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=max_time)

        for S_try in iterate_S_list:
            prob = pulp.LpProblem(f"mean_match_S_{S_try}", pulp.LpMinimize)
            x = pulp.LpVariable.dicts("x", range(len(A)), 0, 1, cat="Binary")
            t = pulp.LpVariable.dicts("t", A_df.columns, 0)

            prob += pulp.lpSum(x[i] for i in x) == S_try
            for ci, cname in enumerate(A_df.columns):
                a_col = A[:, ci]
                expr = pulp.lpSum(a_col[i] * x[i] for i in x) - S_try * target_means[cname]
                prob += expr <= S_try * t[cname]
                prob += expr >= -S_try * t[cname]
            prob += pulp.lpSum(comp_weights[c] * t[c] for c in A_df.columns)
            prob.solve(solver)

            selected = [idx_list[i] for i in range(len(A)) if pulp.value(x[i]) >= 0.5]
            if not selected:
                continue

            sel_mask = [i for i in range(len(A)) if pulp.value(x[i]) >= 0.5]
            A_sel = A[sel_mask, :].mean(axis=0)
            total_dev = sum(
                comp_weights[c] * abs(A_sel[ci] - target_means[c])
                for ci, c in enumerate(A_df.columns)
            )
            if total_dev < best_obj:
                best_obj, best_sel, best_model = total_dev, selected, prob

        return best_sel, best_obj, best_model

    # ── Full pipeline ──

    def run(self, pl_df, wl_df, low=0.01, high=0.75):
        self.logger.step_start("PropensitySubsetSelector")

        if pl_df.empty or wl_df.empty:
            self.logger.error("PL or WL empty.")
            return pd.DataFrame(columns=pl_df.columns)

        # Phase 1: Propensity model
        combined = pd.concat([pl_df, wl_df])
        combined["treatment"] = [0] * len(pl_df) + [1] * len(wl_df)

        X_num = combined[self.num_cols].fillna(0).values
        scaler = StandardScaler().fit(X_num)
        X_num = scaler.transform(X_num)

        if self.cat_cols:
            encoder = OneHotEncoder(handle_unknown="ignore")
            X_cat = encoder.fit_transform(combined[self.cat_cols].astype(str))
            X = hstack([csr_matrix(X_num), X_cat])
        else:
            X = csr_matrix(X_num)

        y = combined["treatment"].values
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            self.model.fit(X, y)

        ps = np.clip(self.model.predict_proba(X)[:, 1], 1e-10, 1 - 1e-10)
        logit = np.log(ps / (1 - ps))

        # Phase 1b: Nearest-neighbor matching
        nn = NearestNeighbors(n_neighbors=2, metric="euclidean", n_jobs=-1)
        nn.fit(logit[: len(pl_df)].reshape(-1, 1))
        dist, idxs = nn.kneighbors(logit[len(pl_df) :].reshape(-1, 1))

        matches = pd.DataFrame({
            "wl_idx": np.repeat(wl_df.index, 2),
            "pool_idx": idxs.flatten(),
            "dist": dist.flatten(),
        })
        matches = matches[matches["dist"] <= high].sort_values("dist").drop_duplicates("pool_idx")

        # FIX 1: index X by the actual matched positions
        matched_positions = matches["pool_idx"].values
        matched_pool = pl_df.iloc[matched_positions]
        self.logger.info(f"PSM matched: {len(matched_pool)} / {len(pl_df)}")

        # Phase 2: Weight → top-K → MILP
        X_matched = X[matched_positions]
        probs_matched = self.model.predict_proba(X_matched)[:, 1]
        weights = np.clip(probs_matched / (1 - probs_matched), 0, self.max_weight)

        topK = min(len(matched_pool), max(1000, 2 * len(wl_df)))
        top_idx = np.argsort(-weights)[:topK]
        candidates = matched_pool.iloc[top_idx]

        selected_idx, best_obj, _ = self.milp_mean_match(candidates, wl_df)

        self.logger.step_end("PropensitySubsetSelector")
        return candidates.loc[selected_idx]


# ═══════════════════════════════════════════════════════════════
# (large pool > 500K): XGBoost + Weighted Sampling + LP
# ═══════════════════════════════════════════════════════════════

def transform_features(pl_df, wl_df, num_cols, cat_cols, logger: PipelineLogger):
    """Build combined feature matrix X and label vector y for density-ratio estimation."""
    logger.step_start("Data_Transformation")

    scaler = StandardScaler().fit(wl_df[num_cols])
    pool_num = scaler.transform(pl_df[num_cols])
    wl_num = scaler.transform(wl_df[num_cols])

    pool_cat = pl_df[cat_cols].to_numpy(dtype=np.float32)
    wl_cat = wl_df[cat_cols].to_numpy(dtype=np.float32)

    X = hstack([
        csr_matrix(np.vstack([pool_num, wl_num])),
        vstack([csr_matrix(pool_cat), csr_matrix(wl_cat)]),
    ])
    y = np.array([0] * len(pl_df) + [1] * len(wl_df))

    logger.step_end("Data_Transformation")
    return X, y


def xgboost_weights(X, y, pool_len, logger: PipelineLogger):
    """Train XGBoost for density-ratio estimation and return importance weights."""
    logger.step_start("XGBoost_prediction")

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method="hist",
    )
    model.fit(csr_matrix(X), y)

    probs = model.predict_proba(csr_matrix(X)[:pool_len])[:, 1]
    weights = (probs / (1 - probs)).clip(max=MAX_PROPENSITY_WEIGHT)

    logger.step_end("XGBoost_prediction")
    return weights


def weighted_sample(weights, pool_df, wl_df, logger: PipelineLogger,
                    subsample_pct=WL_SUBSAMPLE_PERCENT):
    """Draw a weighted random sample from the pool."""
    logger.step_start("Weighted_sampling")

    target_n = int(len(wl_df) * subsample_pct)
    subset = pool_df.sample(n=target_n, weights=weights, replace=False, random_state=0)

    logger.info(f"Sampled {len(subset)} rows from pool of {len(pool_df)}")
    logger.step_end("Weighted_sampling")
    return subset


# ── LP-based subset matching ──

def _build_group_aggregates(pl_df, cat_cols, num_cols):
    pl_df = pl_df.copy()
    pl_df["_row_idx"] = pl_df.index

    if len(cat_cols) == 1:
        pl_df["_grp_key"] = pl_df[cat_cols[0]]
    else:
        pl_df["_grp_key"] = pd.MultiIndex.from_arrays(
            [pl_df[c].values for c in cat_cols]
        ).to_list()

    agg_dict = {c: "sum" for c in num_cols}
    agg_dict["_row_idx"] = "count"

    grouped = (
        pl_df.groupby("_grp_key", sort=True)
        .agg(agg_dict)
        .rename(columns={"_row_idx": "count"})
        .reset_index()
    )
    grouped["grp"] = grouped["_grp_key"]

    raw_groups = pl_df.groupby("_grp_key", sort=False).indices
    groups_to_indices = {k: v.tolist() for k, v in raw_groups.items()}

    return grouped, groups_to_indices


def _compute_wl_targets(wl_df, cat_cols, num_cols, target_n):
    num_targets = {c: float(wl_df[c].mean() * target_n) for c in num_cols}

    cat_targets = {}
    for c in cat_cols:
        counts = wl_df[c].fillna("__MISSING__").value_counts()
        prop = counts / counts.sum()
        for level, p in prop.items():
            cat_targets[(c, level)] = float(p * target_n)

    return num_targets, cat_targets


def _build_constraint_matrix(groups_df, cat_cols, num_cols):
    G = len(groups_df)
    group_keys = list(groups_df["grp"].values)

    rows, cols, data, b, labels = [], [], [], [], []

    for col in num_cols:
        for i in range(G):
            rows.append(len(b))
            cols.append(i)
            data.append(float(groups_df.loc[i, col]))
        b.append(None)
        labels.append(("num", col))

    for c_idx, c in enumerate(cat_cols):
        levels_seen = set()
        for grp in group_keys:
            grp_key = grp if isinstance(grp, tuple) else (grp,)
            levels_seen.add(grp_key[c_idx])

        for level in levels_seen:
            for i, grp in enumerate(group_keys):
                grp_key = grp if isinstance(grp, tuple) else (grp,)
                if grp_key[c_idx] == level:
                    rows.append(len(b))
                    cols.append(i)
                    data.append(float(groups_df.loc[i, "count"]))
            b.append(None)
            labels.append(("cat", c, level))

    A = sparse.csr_matrix((data, (rows, cols)), shape=(len(b), G), dtype=float)
    return A, np.array(b, dtype=float), labels, group_keys


def _solve_lp(groups_df, groups_to_indices, wl_df, cat_cols, num_cols,
              min_frac_of_wl, max_frac_per_group=1.0, tolerance=1e-6):
    group_keys = list(groups_df["grp"].values)
    target_n = max(int(len(wl_df) * min_frac_of_wl), 1)

    A, _, labels, _ = _build_constraint_matrix(groups_df, cat_cols, num_cols)
    C, G = A.shape

    num_targets, cat_targets = _compute_wl_targets(wl_df, cat_cols, num_cols, target_n)

    b = np.zeros(C, dtype=float)
    for i, lab in enumerate(labels):
        if lab[0] == "num":
            b[i] = num_targets[lab[1]]
        else:
            b[i] = cat_targets.get((lab[1], lab[2]), 0.0)

    I_C = sparse.identity(C, format="csr", dtype=float)
    A_eq = sparse.hstack([A, I_C, -I_C], format="csr")
    c = np.concatenate([np.zeros(G), np.ones(C), np.ones(C)])
    bounds = [(0.0, max_frac_per_group)] * G + [(0.0, None)] * (2 * C)

    res = linprog(c=c, A_eq=A_eq, b_eq=b, bounds=bounds, method="highs",
                  options={"tol": tolerance, "presolve": True})

    if not res.success:
        print(f"LP warning: {res.message}")

    x = res.x[:G]
    fracs = {grp: max(0.0, min(float(xi), 1.0)) for xi, grp in zip(x, group_keys)}
    return fracs, target_n


def _sample_from_groups(fracs, groups_to_indices, target_n, rnd_state=0):
    random.seed(rnd_state)
    group_keys = list(fracs.keys())
    intended, total, remainders = {}, 0, []

    for g in group_keys:
        cnt = len(groups_to_indices.get(g, []))
        raw = cnt * fracs[g]
        flo = math.floor(raw)
        intended[g] = int(flo)
        total += flo
        remainders.append((raw - flo, g, cnt))

    remaining = target_n - total
    remainders.sort(reverse=True)
    for frac, g, cnt in remainders:
        if remaining <= 0:
            break
        if intended[g] < cnt:
            intended[g] += 1
            remaining -= 1

    if remaining > 0:
        for _, g, cnt in remainders:
            while remaining > 0 and intended[g] < cnt:
                intended[g] += 1
                remaining -= 1

    sampled = []
    for g, take in intended.items():
        idxs = groups_to_indices.get(g, [])
        if take > 0 and idxs:
            sampled.extend(random.sample(idxs, min(take, len(idxs))))
    return sampled


def subset_match_via_lp(pre_pool, wl_df, index_column, cat_cols, num_cols,
                        logger: PipelineLogger, min_frac_of_wl=LP_MIN_FRAC_OF_WL):
    """LP-based subset selection (Option 2 final stage)."""
    logger.step_start("Subset_Match_Via_LP")

    groups_df, groups_to_indices = _build_group_aggregates(pre_pool, cat_cols, num_cols)
    logger.info(f"Groups formed: {len(groups_df)}")

    fracs, target_n = _solve_lp(
        groups_df, groups_to_indices, wl_df,
        cat_cols, num_cols, min_frac_of_wl,
    )

    sampled_indices = _sample_from_groups(fracs, groups_to_indices, target_n)
    selected = pre_pool.reset_index().loc[sampled_indices][index_column]

    logger.info(f"LP selected {len(selected)} rows (target: {target_n})")
    logger.step_end("Subset_Match_Via_LP")
    return selected