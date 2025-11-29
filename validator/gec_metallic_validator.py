
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GEC Metallic-Mean Validator
---------------------------
Implements the "Core mini-protocol" for testing metallic-mean structure in
distance-to-frontier efficiency data. Designed to drop into any notebook or
run as a standalone CLI on CSV files.



Protocol (condensed, implemented below):
    1) Define efficiency triplet: (Y, X, Cmax). One frontier per slice!
    2) Compute: eta = Y/X; GEC0 = eta / Cmax; clamp only to avoid 0/1 blowups
       and log all clamped rows.
    3) Build disjoint merges: pair non-overlapping blocks (i, j) -> merged (i∪j)
       where Y and X SUM; keep the same Cmax.
    4) Odds transform: t = GEC0 / (1 - GEC0) (positive, scale-free).
    5) Fit and falsify:
        - Metallic map: t_{n+1} = k + β / t_n
        - Nulls:        t_{n+1} = α t_n   and   t_{n+1} = α
        - Bootstrap (k, β), fixed point (k + sqrt(k^2 + 4β)) / 2
    6) Interpret:
        - k≈1, β≈1 => symmetric (golden φ fixed point)
        - k>1, β≈1 => asymmetric metallic mean
        - Wide CIs / nulls win => no metallic structure for that slice

Target sample size: ≥ 30 merges (60 rows) for believable CIs; 50–100 is great.

Data expectations
-----------------
Input CSV should contain at least the columns:
    Y, X, Cmax
Optional columns:
    block_id : to help enforce disjointness (no overlapping tokens/windows).
    well, start, end : to enable extra overlap checks (e.g., for E. coli growth).
    meta columns are preserved in outputs.

Usage (CLI)
-----------
python gec_metallic_validator.py --csv your_rows.csv --ycol Y --xcol X --cmaxcol Cmax \
    --idcol block_id --pairing consecutive --bootstrap 5000 --alpha 0.05 \
    --outprefix results/gec_run

Or, with a constant frontier for the slice:
python gec_metallic_validator.py --csv your_rows.csv --ycol Y --xcol X --cmax 0.93

The script emits:
  - <outprefix>_summary.json       : key estimates and model comparison
  - <outprefix>_pairs.csv          : the constructed (t_n, t_{n+1}) dataset
  - <outprefix>_clamps.csv         : rows that hit numeric clamps
  - <outprefix>_diagnostics.txt    : human-readable report
  - optional: plots if --plots is passed

Library dependencies: numpy, pandas, scipy (optional for stats), matplotlib (optional for plots).

Note
----
This script is intentionally conservative about assumptions (e.g., frontier leakage,
row reuse). It will refuse to proceed if it detects per-row Cmax that varies *within*
a slice unless you supply --allow-cmax-variation (but this is discouraged).
"""

import argparse
import json
import math
import os
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd

# Delayed import for optional plotting (keeps headless runs clean)
try:
    import matplotlib.pyplot as plt
    _HAS_PLT = True
except Exception:
    _HAS_PLT = False


EPS = 1e-9  # numerical floor for clamping


# ---------------------------- Utilities ----------------------------

def odds(x: np.ndarray, eps: float = EPS) -> np.ndarray:
    """Compute odds = x / (1 - x) with safe clamping to avoid division by zero."""
    x = np.clip(x, eps, 1.0 - eps)
    return x / (1.0 - x)


def inv_odds(t: np.ndarray, eps: float = EPS) -> np.ndarray:
    """Inverse of odds: x = t / (1 + t)."""
    t = np.maximum(t, eps)
    return t / (1.0 + t)


def safe_lstsq(A: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, float]:
    """Least-squares with nan/inf checks. Returns (coef, residual_sse)."""
    coef, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
    if residuals.size > 0:
        sse = float(residuals[0])
    else:
        # When design is 'perfectly' fitted, compute SSE by hand
        sse = float(np.sum((b - A @ coef) ** 2))
    return coef, sse


def aic_bic(sse: float, n: int, k: int) -> Tuple[float, float]:
    """Compute AIC and BIC for Gaussian errors with SSE and k parameters."""
    if n <= k or n <= 0:
        return float('nan'), float('nan')
    sigma2 = sse / n
    if sigma2 <= 0:
        # Perfect fit: penalize minimally
        sigma2 = 1e-16
    aic = 2 * k + n * math.log(sigma2)
    bic = k * math.log(n) + n * math.log(sigma2)
    return aic, bic


def k_beta_fixed_point_from_fit(k: float, beta: float) -> float:
    """Compute metallic fixed point t* = (k + sqrt(k^2 + 4β)) / 2, guarding domain."""
    disc = k ** 2 + 4.0 * beta
    disc = max(disc, 0.0)
    return 0.5 * (k + math.sqrt(disc))


def nearest_metallic_label(t_star: float) -> Tuple[str, float]:
    """
    Classify fixed point against a small palette of metallic means by absolute distance.
    Returns (label, abs_distance). Palette: plastic (~1.3247), golden φ (~1.618), silver (~2.414), bronze (~3.303).
    """
    palette = {
        "plastic ≈ 1.3247": 1.3247179572447458,
        "φ (golden) ≈ 1.6180": (1.0 + math.sqrt(5.0)) / 2.0,
        "silver ≈ 2.4142": 1.0 + math.sqrt(2.0),
        "bronze ≈ 3.3027756": (3.0 + math.sqrt(13.0)) / 2.0,
    }
    dists = {name: abs(t_star - val) for name, val in palette.items()}
    label = min(dists, key=dists.get)
    return label, dists[label]


# ---------------------------- Core computation ----------------------------

@dataclass
class ClampLog:
    index: int
    raw_gec0: float
    clamped_gec0: float
    reason: str


@dataclass
class ModelFit:
    name: str
    params: Dict[str, float]
    yhat: np.ndarray
    sse: float
    aic: float
    bic: float
    k_params: int


@dataclass
class BootstrapCI:
    lower: float
    upper: float
    median: float
    mean: float


@dataclass
class MetallicResult:
    n_pairs: int
    k: float
    beta: float
    t_star: float
    k_ci: BootstrapCI
    beta_ci: BootstrapCI
    tstar_ci: BootstrapCI
    label: str
    label_distance: float
    model_comparison: Dict[str, Dict[str, float]]  # model -> {aic, bic, mse_cv}
    warnings: List[str]


def compute_gec0(df: pd.DataFrame, ycol: str, xcol: str, cmax: Optional[float], cmaxcol: Optional[str],
                 eps: float = EPS, allow_cmax_variation: bool = False) -> Tuple[np.ndarray, List[ClampLog], float]:
    """
    Compute raw efficiency η = Y/X and normalized index GEC0 = η/Cmax.
    Returns (gec0, clamp_logs, used_cmax).
    """
    if cmax is None and cmaxcol is None:
        raise ValueError("You must provide either --cmax or --cmaxcol.")
    if cmax is not None and cmaxcol is not None:
        raise ValueError("Provide only one of --cmax or --cmaxcol, not both.")

    Y = df[ycol].astype(float).to_numpy()
    X = df[xcol].astype(float).to_numpy()

    if cmax is not None:
        C = float(cmax) * np.ones_like(Y, dtype=float)
        used_cmax = float(cmax)
    else:
        C = df[cmaxcol].astype(float).to_numpy()
        unique_c = np.unique(C[~np.isnan(C)])
        if unique_c.size == 0:
            raise ValueError("Cmax column appears empty.")
        if unique_c.size > 1 and not allow_cmax_variation:
            raise ValueError(
                "Detected multiple distinct Cmax values within the slice. "
                "Per-protocol, a single frontier should be used per slice. "
                "Pass --allow-cmax-variation ONLY if you know what you're doing."
            )
        used_cmax = float(np.median(unique_c))

    eta = Y / X
    raw_gec0 = eta / C

    clamp_logs: List[ClampLog] = []
    gec0 = raw_gec0.copy()
    mask_low = raw_gec0 <= eps
    mask_high = raw_gec0 >= 1.0 - eps
    if mask_low.any():
        for idx in np.where(mask_low)[0]:
            clamp_logs.append(ClampLog(index=int(idx), raw_gec0=float(raw_gec0[idx]), clamped_gec0=float(eps),
                                       reason="low clamp"))
        gec0[mask_low] = eps
    if mask_high.any():
        for idx in np.where(mask_high)[0]:
            clamp_logs.append(ClampLog(index=int(idx), raw_gec0=float(raw_gec0[idx]), clamped_gec0=float(1.0 - eps),
                                       reason="high clamp"))
        gec0[mask_high] = 1.0 - eps

    return gec0, clamp_logs, used_cmax


def build_disjoint_pairs(df: pd.DataFrame,
                         gec0: np.ndarray,
                         strategy: str = "consecutive",
                         idcol: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Build disjoint pairs (i,j) and their merged blocks per protocol.
    Returns (t_n, t_next, pairs_df).

    t_n uses the symmetric average of odds from the two source rows.
    t_next is the odds of the merged block (sum Y, sum X, same Cmax).
    """
    if strategy not in {"consecutive", "by_id"}:
        raise ValueError("pairing strategy must be 'consecutive' or 'by_id'.")

    n = len(df)
    if strategy == "consecutive":
        pairs = [(i, i + 1) for i in range(0, n - 1, 2)]
    else:
        if idcol is None or idcol not in df.columns:
            raise ValueError("by_id pairing requires --idcol present in the dataframe.")
        # Group by id and pick one representative per id, then consecutive pair across distinct ids
        first_of_id = df.drop_duplicates(subset=[idcol]).index.to_list()
        pairs = [(first_of_id[i], first_of_id[i + 1]) for i in range(0, len(first_of_id) - 1, 2)]

    t_n_list, t_next_list = [], []
    rows = []

    for (i, j) in pairs:
        gA, gB = float(gec0[i]), float(gec0[j])
        tA, tB = odds(np.array([gA]))[0], odds(np.array([gB]))[0]
        t_sym = 0.5 * (tA + tB)

        # merged block: sum Y and X; keep Cmax (assumed constant or already validated)
        Ym = float(df.iloc[i]["_Y_"]) + float(df.iloc[j]["_Y_"])
        Xm = float(df.iloc[i]["_X_"]) + float(df.iloc[j]["_X_"])
        Cm = float(df.iloc[i]["_C_"])  # same slice frontier; protocol guards already
        gm = max(min((Ym / Xm) / Cm, 1.0 - EPS), EPS)
        tm = odds(np.array([gm]))[0]

        t_n_list.append(t_sym)
        t_next_list.append(tm)

        rows.append({
            "i": int(i), "j": int(j),
            "gec0_i": gA, "gec0_j": gB,
            "t_i": tA, "t_j": tB, "t_sym": t_sym,
            "Y_sum": Ym, "X_sum": Xm, "C": Cm,
            "gec0_merged": gm, "t_next": tm
        })

    pairs_df = pd.DataFrame(rows)
    return np.array(t_n_list, dtype=float), np.array(t_next_list, dtype=float), pairs_df


# ---------------------------- Model fitting ----------------------------

def fit_metallic(t_n: np.ndarray, t_next: np.ndarray) -> ModelFit:
    """Fit t_next = k + β / t_n via linear regression with regressors [1, 1/t_n]."""
    inv = 1.0 / np.maximum(t_n, EPS)
    A = np.column_stack([np.ones_like(inv), inv])
    coef, sse = safe_lstsq(A, t_next)
    k, beta = float(coef[0]), float(coef[1])
    yhat = A @ coef
    aic, bic = aic_bic(sse, n=len(t_next), k=2)
    return ModelFit(name="metallic", params={"k": k, "beta": beta}, yhat=yhat, sse=sse, aic=aic, bic=bic, k_params=2)


def fit_null_alpha(t_n: np.ndarray, t_next: np.ndarray) -> ModelFit:
    """Fit t_next = α (intercept-only)."""
    A = np.ones((len(t_n), 1))
    coef, sse = safe_lstsq(A, t_next)
    alpha = float(coef[0])
    yhat = A @ coef
    aic, bic = aic_bic(sse, n=len(t_next), k=1)
    return ModelFit(name="null_const", params={"alpha": alpha}, yhat=yhat, sse=sse, aic=aic, bic=bic, k_params=1)


def fit_null_alpha_t(t_n: np.ndarray, t_next: np.ndarray) -> ModelFit:
    """Fit t_next = α * t_n (no intercept)."""
    A = t_n.reshape(-1, 1)
    coef, sse = safe_lstsq(A, t_next)
    alpha = float(coef[0])
    yhat = A @ coef
    aic, bic = aic_bic(sse, n=len(t_next), k=1)
    return ModelFit(name="null_slope", params={"alpha": alpha}, yhat=yhat, sse=sse, aic=aic, bic=bic, k_params=1)


def kfold_cv_mse(model_name: str, t_n: np.ndarray, t_next: np.ndarray, K: int = 10, seed: int = 42) -> float:
    """K-fold cross-validated MSE for the three models."""
    rng = np.random.default_rng(seed)
    n = len(t_n)
    idx = np.arange(n)
    rng.shuffle(idx)
    folds = np.array_split(idx, K)

    preds = np.zeros(n, dtype=float)
    for fold in folds:
        train = np.setdiff1d(idx, fold, assume_unique=False)
        tn_tr, tn_te = t_n[train], t_n[fold]
        ty_tr = t_next[train]

        if model_name == "metallic":
            inv = 1.0 / np.maximum(tn_tr, EPS)
            A = np.column_stack([np.ones_like(inv), inv])
            coef, _ = safe_lstsq(A, ty_tr)
            inv_te = 1.0 / np.maximum(tn_te, EPS)
            A_te = np.column_stack([np.ones_like(inv_te), inv_te])
            preds[fold] = A_te @ coef
        elif model_name == "null_const":
            A = np.ones((len(tn_tr), 1))
            coef, _ = safe_lstsq(A, ty_tr)
            preds[fold] = np.ones_like(tn_te) * coef[0]
        elif model_name == "null_slope":
            A = tn_tr.reshape(-1, 1)
            coef, _ = safe_lstsq(A, ty_tr)
            preds[fold] = tn_te * coef[0]
        else:
            raise ValueError("Unknown model for CV.")

    mse = float(np.mean((preds - t_next) ** 2))
    return mse


def bootstrap_metallic(t_n: np.ndarray, t_next: np.ndarray, B: int = 2000, seed: int = 12345) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Nonparametric bootstrap for (k, β, t*)."""
    rng = np.random.default_rng(seed)
    n = len(t_n)
    ks, betas, tstars = np.empty(B, dtype=float), np.empty(B, dtype=float), np.empty(B, dtype=float)
    inv_all = 1.0 / np.maximum(t_n, EPS)
    A_all = np.column_stack([np.ones_like(inv_all), inv_all])

    for b in range(B):
        samp_idx = rng.integers(0, n, size=n)
        A = A_all[samp_idx, :]
        y = t_next[samp_idx]
        coef, _ = safe_lstsq(A, y)
        k_b, beta_b = float(coef[0]), float(coef[1])
        ks[b] = k_b
        betas[b] = beta_b
        tstars[b] = k_beta_fixed_point_from_fit(k_b, beta_b)

    return ks, betas, tstars


def ci_from_samples(samples: np.ndarray, alpha: float = 0.05) -> BootstrapCI:
    lo = float(np.quantile(samples, alpha / 2.0))
    hi = float(np.quantile(samples, 1.0 - alpha / 2.0))
    med = float(np.quantile(samples, 0.5))
    mean = float(np.mean(samples))
    return BootstrapCI(lower=lo, upper=hi, median=med, mean=mean)


# ---------------------------- End-to-end runner ----------------------------

def run_validator(df: pd.DataFrame,
                  ycol: str,
                  xcol: str,
                  cmax: Optional[float],
                  cmaxcol: Optional[str],
                  pairing: str = "consecutive",
                  idcol: Optional[str] = None,
                  allow_cmax_variation: bool = False,
                  bootstrap_iters: int = 2000,
                  alpha: float = 0.05,
                  kfolds: int = 10,
                  seed: int = 123,
                  outprefix: Optional[str] = None,
                  make_plots: bool = False) -> MetallicResult:
    """
    Executes the protocol end-to-end and writes artifacts if outprefix is given.
    """
    # Preserve original Y/X/Cmax for pair construction
    df = df.copy()
    if ycol not in df.columns or xcol not in df.columns:
        raise ValueError("Input dataframe must contain the specified --ycol and --xcol.")
    if cmaxcol is not None and cmaxcol not in df.columns:
        raise ValueError("Cmax column not found: %r" % cmaxcol)

    df["_Y_"] = df[ycol].astype(float)
    df["_X_"] = df[xcol].astype(float)
    df["_C_"] = (df[cmaxcol].astype(float) if cmaxcol is not None else float(cmax))

    # Step 1–2: Compute GEC0 (with clamping logs)
    gec0, clamp_logs, used_cmax = compute_gec0(df, ycol, xcol, cmax, cmaxcol,
                                               allow_cmax_variation=allow_cmax_variation)
    df["_gec0_"] = gec0

    # Step 3–4: Build disjoint pairs and compute odds transformed sequences
    t_n, t_next, pairs_df = build_disjoint_pairs(df, gec0, strategy=pairing, idcol=idcol)

    warnings = []
    if len(t_n) < 30:
        warnings.append(f"Too few merges (n_pairs={len(t_n)}). CIs will be unreliable; aim for ≥30 (preferably 50–100).")

    # Step 5: Fit models
    metallic = fit_metallic(t_n, t_next)
    null_const = fit_null_alpha(t_n, t_next)
    null_slope = fit_null_alpha_t(t_n, t_next)

    # Cross-validated MSEs
    mse_metallic = kfold_cv_mse("metallic", t_n, t_next, K=kfolds, seed=seed)
    mse_const = kfold_cv_mse("null_const", t_n, t_next, K=kfolds, seed=seed)
    mse_slope = kfold_cv_mse("null_slope", t_n, t_next, K=kfolds, seed=seed)

    model_cmp = {
        metallic.name: {"aic": metallic.aic, "bic": metallic.bic, "mse_cv": mse_metallic},
        null_const.name: {"aic": null_const.aic, "bic": null_const.bic, "mse_cv": mse_const},
        null_slope.name: {"aic": null_slope.aic, "bic": null_slope.bic, "mse_cv": mse_slope},
    }

    # Bootstrapping
    ks, betas, tstars = bootstrap_metallic(t_n, t_next, B=bootstrap_iters, seed=seed)
    k_ci = ci_from_samples(ks, alpha=alpha)
    beta_ci = ci_from_samples(betas, alpha=alpha)
    tstar_ci = ci_from_samples(tstars, alpha=alpha)

    k_hat = float(metallic.params["k"])
    beta_hat = float(metallic.params["beta"])
    t_star_hat = k_beta_fixed_point_from_fit(k_hat, beta_hat)
    label, label_dist = nearest_metallic_label(t_star_hat)

    # Artifacts
    if outprefix is not None:
        os.makedirs(os.path.dirname(outprefix), exist_ok=True) if os.path.dirname(outprefix) else None

        # Pairs dataset
        pairs_df_out = pairs_df.copy()
        pairs_df_out["t_n"] = t_n
        pairs_df_out["t_next_hat_metallic"] = metallic.yhat
        pairs_df_out["t_next_hat_null_const"] = null_const.yhat
        pairs_df_out["t_next_hat_null_slope"] = null_slope.yhat
        pairs_df_out.to_csv(outprefix + "_pairs.csv", index=False)

        # Clamp logs
        clamp_rows = pd.DataFrame([asdict(c) for c in clamp_logs])
        clamp_rows.to_csv(outprefix + "_clamps.csv", index=False)

        # Summary JSON
        summary = {
            "n_pairs": int(len(t_n)),
            "used_cmax": float(used_cmax),
            "metallic": {
                "k": k_hat,
                "beta": beta_hat,
                "t_star": t_star_hat,
                "k_ci": asdict(k_ci),
                "beta_ci": asdict(beta_ci),
                "tstar_ci": asdict(tstar_ci),
            },
            "model_comparison": model_cmp,
            "warnings": warnings,
            "notes": [
                "One frontier per slice strongly recommended.",
                "Avoid overlapping blocks / row reuse.",
                "Target ≥30 merges (preferably 50–100).",
            ],
        }
        with open(outprefix + "_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Human-readable diagnostics
        with open(outprefix + "_diagnostics.txt", "w", encoding="utf-8") as f:
            f.write("# GEC Metallic-Mean Validator Report\n")
            f.write(f"n_pairs: {len(t_n)}\n")
            f.write(f"used Cmax: {used_cmax}\n\n")
            f.write("== Metallic fit ==\n")
            f.write(f"k = {k_hat:.6f}  (CI {k_ci.lower:.6f}, {k_ci.upper:.6f})\n")
            f.write(f"beta = {beta_hat:.6f}  (CI {beta_ci.lower:.6f}, {beta_ci.upper:.6f})\n")
            f.write(f"t* = {t_star_hat:.6f}  (CI {tstar_ci.lower:.6f}, {tstar_ci.upper:.6f})\n")
            f.write(f"closest metallic: {label} (|Δ|={label_dist:.6g})\n\n")
            f.write("== Model comparison (smaller is better) ==\n")
            for m, s in model_cmp.items():
                f.write(f"{m:12s}  AIC={s['aic']:.3f}  BIC={s['bic']:.3f}  MSE_CV={s['mse_cv']:.6g}\n")
            if len(warnings):
                f.write("\n== Warnings ==\n")
                for w in warnings:
                    f.write(f"- {w}\n")

        # Optional plots
        if make_plots and _HAS_PLT:
            fig, ax = plt.subplots()
            inv = 1.0 / np.maximum(t_n, EPS)
            ax.scatter(inv, t_next, s=22, alpha=0.8)
            inv_line = np.linspace(inv.min(), inv.max(), 200)
            ax.plot(inv_line, k_hat + beta_hat * inv_line, lw=2)
            ax.set_xlabel("1 / t_n")
            ax.set_ylabel("t_{n+1}")
            ax.set_title("Metallic map fit: t_{n+1} = k + β / t_n")
            fig.tight_layout()
            fig.savefig(outprefix + "_fit.png", dpi=160)
            plt.close(fig)

    return MetallicResult(
        n_pairs=len(t_n),
        k=k_hat,
        beta=beta_hat,
        t_star=t_star_hat,
        k_ci=k_ci,
        beta_ci=beta_ci,
        tstar_ci=tstar_ci,
        label=label,
        label_distance=label_dist,
        model_comparison=model_cmp,
        warnings=warnings,
    )


# ---------------------------- Domain preprocessors (optional) ----------------------------

def preprocess_ecoli_od600(df: pd.DataFrame,
                           well_col: str = "well",
                           time_col: str = "time_min",
                           od_col: str = "od600",
                           window_min: float = 30.0,
                           step_min: float = 15.0,
                           od_linear_max: float = 0.6,
                           r2_min: float = 0.95) -> pd.DataFrame:
    """
    Turn OD600 time-series into efficiency rows for the E. coli recipe.
    - Y = 1/τ  (divisions per minute). τ = ln(2) / r where r is slope of ln(OD) vs time in a window.
    - X = 1 (minute)
    Returns dataframe with columns: Y, X, Cmax (to be filled by user), block_id, well, start, end.

    Notes:
    * Reject windows touching saturation (OD >= od_linear_max) and low-quality fits (R^2 < r2_min).
    * Choose Cmax as best 1/τ in your run (or literature bound); set a constant column afterward.
    """
    if any(c not in df.columns for c in [well_col, time_col, od_col]):
        raise ValueError("Input dataframe must contain well_col, time_col, od_col.")

    # Ensure sorted by time per well
    df2 = df[[well_col, time_col, od_col]].dropna().copy()
    df2 = df2.sort_values([well_col, time_col])

    rows = []
    ln2 = math.log(2.0)

    for well, sub in df2.groupby(well_col):
        t = sub[time_col].to_numpy(dtype=float)
        od = sub[od_col].to_numpy(dtype=float)

        # Only keep linear range
        mask = od < od_linear_max
        t, od = t[mask], od[mask]
        if t.size < 3:
            continue

        # Sliding windows
        w = window_min
        s = step_min
        t_min, t_max = float(t.min()), float(t.max())
        if t_max - t_min < w:
            continue

        start = t_min
        block_idx = 0
        while start + w <= t_max + 1e-9:
            end = start + w
            m = (t >= start) & (t <= end)
            if np.sum(m) >= 3:
                tt = t[m]
                yy = np.log(np.maximum(od[m], 1e-6))

                # Fit line ln(OD) ~ a + r * t
                A = np.column_stack([np.ones_like(tt), tt])
                coef, sse = safe_lstsq(A, yy)
                yhat = A @ coef
                # R^2
                sst = float(np.sum((yy - np.mean(yy)) ** 2))
                r2 = 1.0 - (float(np.sum((yy - yhat) ** 2)) / sst if sst > 0 else 0.0)
                r = float(coef[1])  # per minute

                if r > 0 and r2 >= r2_min:
                    tau = ln2 / r
                    Y = 1.0 / tau
                    X = 1.0  # minute
                    rows.append({
                        "Y": Y, "X": X,
                        "block_id": f"{well}_{block_idx}",
                        "well": well,
                        "start": start,
                        "end": end,
                    })
                    block_idx += 1

            start += s

    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError("No valid growth windows found. Check OD range, window size, and r2_min.")
    return out


def preprocess_neuron_morphology(df: pd.DataFrame,
                                 cell_col: str = "cell_id",
                                 level_col: str = "level",
                                 count_col: str = "branches",
                                 option: str = "branch_counts") -> pd.DataFrame:
    """
    Turn neurite morphology tabulation into efficiency rows.
    Option A (branch counts): Y = r_ell = (#branches_{ell+1}) / (#branches_{ell}), X = 1.
    Option B (Rall-style): Y = (d1^p + d2^p) / d_parent^p with user-provided p (fit p upstream).
    Returns dataframe with Y, X, block_id (pairs across cells recommended). Leave Cmax empty for now.
    """
    if option not in {"branch_counts"}:
        raise NotImplementedError("Only option='branch_counts' is implemented in this script.")

    if any(c not in df.columns for c in [cell_col, level_col, count_col]):
        raise ValueError("Missing required columns for neuron morphology.")

    rows = []
    for cell, sub in df.groupby(cell_col):
        sub = sub.sort_values(level_col)
        levels = sub[level_col].to_numpy()
        counts = sub[count_col].astype(float).to_numpy()
        for i in range(len(levels) - 1):
            a, b = counts[i], counts[i + 1]
            if a > 0:
                r = b / a
                rows.append({
                    "Y": r, "X": 1.0,
                    "block_id": f"{cell}_L{levels[i]}"
                })

    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError("No valid neuron morphology ratios found.")
    return out


# ---------------------------- CLI ----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GEC Metallic-Mean Validator (implements the user's mini-protocol).")
    p.add_argument("--csv", required=True, help="Input CSV path containing rows (Y, X, Cmax, optional block_id).")
    p.add_argument("--ycol", default="Y", help="Column name for Y (default: Y).")
    p.add_argument("--xcol", default="X", help="Column name for X (default: X).")
    p.add_argument("--cmax", type=float, default=None, help="Constant Cmax for the slice (float).")
    p.add_argument("--cmaxcol", default=None, help="Column name for per-row Cmax (discouraged; see protocol).")
    p.add_argument("--idcol", default=None, help="Column to help enforce disjointness (e.g., block_id).")
    p.add_argument("--pairing", choices=["consecutive", "by_id"], default="consecutive",
                   help="How to pair rows into disjoint merges (default: consecutive).")
    p.add_argument("--allow-cmax-variation", action="store_true",
                   help="Allow per-row Cmax variation (NOT recommended).")
    p.add_argument("--bootstrap", type=int, default=2000, help="Bootstrap iterations for CIs (default: 2000).")
    p.add_argument("--alpha", type=float, default=0.05, help="CI alpha level (default: 0.05).")
    p.add_argument("--kfolds", type=int, default=10, help="K-folds for CV (default: 10).")
    p.add_argument("--seed", type=int, default=123, help="Random seed for CV/bootstrapping (default: 123).")
    p.add_argument("--outprefix", default=None, help="Prefix for outputs (JSON, CSV, report, plots).")
    p.add_argument("--plots", action="store_true", help="If set, save a diagnostic plot (requires matplotlib).")
    return p.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.csv)
    result = run_validator(
        df=df,
        ycol=args.ycol,
        xcol=args.xcol,
        cmax=args.cmax,
        cmaxcol=args.cmaxcol,
        pairing=args.pairing,
        idcol=args.idcol,
        allow_cmax_variation=args.allow_cmax_variation,
        bootstrap_iters=args.bootstrap,
        alpha=args.alpha,
        kfolds=args.kfolds,
        seed=args.seed,
        outprefix=args.outprefix,
        make_plots=args.plots,
    )

    # Print a short console summary
    print(json.dumps({
        "n_pairs": result.n_pairs,
        "k": result.k,
        "beta": result.beta,
        "t_star": result.t_star,
        "k_ci": asdict(result.k_ci),
        "beta_ci": asdict(result.beta_ci),
        "tstar_ci": asdict(result.tstar_ci),
        "closest_metallic": result.label,
        "closest_distance": result.label_distance,
        "model_comparison": result.model_comparison,
        "warnings": result.warnings,
    }, indent=2))


if __name__ == "__main__":
    main()
