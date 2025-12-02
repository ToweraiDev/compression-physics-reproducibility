#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, json, math, os, sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

EPS = 1e-9

def odds(x):
    x = np.clip(x, EPS, 1 - EPS)
    return x / (1 - x)

def safe_lstsq(A, b):
    coef, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
    if residuals.size > 0:
        sse = float(residuals[0])
    else:
        sse = float(np.sum((b - A @ coef) ** 2))
    return coef, sse

def aic_bic(sse, n, k):
    if n <= k or n <= 0:
        return float('nan'), float('nan')
    sigma2 = max(sse / n, 1e-16)
    aic = 2 * k + n * math.log(sigma2)
    bic = k * math.log(n) + n * math.log(sigma2)
    return aic, bic

def fixed_point(k, beta):
    disc = max(k * k + 4.0 * beta, 0.0)
    return 0.5 * (k + math.sqrt(disc))

def build_pairs(gec0, Y, X, C, order_idx):
    idx = order_idx
    pairs = [(idx[i], idx[i+1]) for i in range(0, len(idx) - 1, 2)]
    t_n = []
    t_next = []
    rows = []
    for i, j in pairs:
        tA, tB = odds(gec0[i]), odds(gec0[j])
        t_sym = 0.5 * (tA + tB)
        Ym = Y[i] + Y[j]
        Xm = X[i] + X[j]
        Cm = C[i]
        gm = np.clip((Ym / Xm) / Cm, EPS, 1 - EPS)
        tm = odds(gm)
        t_n.append(t_sym)
        t_next.append(tm)
        rows.append({"i": int(i), "j": int(j), "t_n": float(t_sym), "t_next": float(tm)})
    return np.array(t_n, float), np.array(t_next, float), rows

def fit_models(t_n, t_next):
    inv = 1.0 / np.maximum(t_n, EPS)
    A = np.column_stack([np.ones_like(inv), inv])
    coef_m, sse_m = safe_lstsq(A, t_next)
    k, beta = float(coef_m[0]), float(coef_m[1])
    aic_m, bic_m = aic_bic(sse_m, len(t_next), 2)

    A0 = np.ones((len(t_n), 1))
    coef_c, sse_c = safe_lstsq(A0, t_next)
    aic_c, bic_c = aic_bic(sse_c, len(t_next), 1)

    A1 = t_n.reshape(-1, 1)
    coef_s, sse_s = safe_lstsq(A1, t_next)
    aic_s, bic_s = aic_bic(sse_s, len(t_next), 1)

    return (k, beta, aic_m, bic_m), (float(coef_c[0]), aic_c, bic_c), (float(coef_s[0]), aic_s, bic_s)

def kfold_cv(model, t_n, t_next, K=10, seed=123):
    rng = np.random.default_rng(seed)
    n = len(t_n)
    idx = np.arange(n)
    rng.shuffle(idx)
    folds = np.array_split(idx, K)
    preds = np.zeros(n, float)
    for f in folds:
        tr = np.setdiff1d(idx, f)
        if model == "metallic":
            inv = 1.0 / np.maximum(t_n[tr], EPS)
            A = np.column_stack([np.ones_like(inv), inv])
            coef, _ = safe_lstsq(A, t_next[tr])
            inv_te = 1.0 / np.maximum(t_n[f], EPS)
            A_te = np.column_stack([np.ones_like(inv_te), inv_te])
            preds[f] = A_te @ coef
        elif model == "null_const":
            A = np.ones((len(tr), 1))
            coef, _ = safe_lstsq(A, t_next[tr])
            preds[f] = coef[0]
        else:
            A = t_n[tr].reshape(-1, 1)
            coef, _ = safe_lstsq(A, t_next[tr])
            preds[f] = t_n[f] * coef[0]
    return float(np.mean((preds - t_next) ** 2))

def bootstrap_ci(t_n, t_next, B=5000, seed=123):
    rng = np.random.default_rng(seed)
    n = len(t_n)
    inv_all = 1.0 / np.maximum(t_n, EPS)
    A_all = np.column_stack([np.ones_like(inv_all), inv_all])
    ks = np.empty(B); bs = np.empty(B); ts = np.empty(B)
    for b in range(B):
        s = rng.integers(0, n, size=n)
        A = A_all[s, :]
        y = t_next[s]
        coef, _ = safe_lstsq(A, y)
        k, beta = float(coef[0]), float(coef[1])
        ks[b] = k
        bs[b] = beta
        ts[b] = fixed_point(k, beta)
    def q(a, p): return float(np.quantile(a, p))
    ci = lambda arr: {"lo": q(arr, 0.025), "med": q(arr, 0.5), "hi": q(arr, 0.975), "mean": float(np.mean(arr))}
    return ci(ks), ci(bs), ci(ts)

def permutation_test(t_n, t_next, reps=2000, seed=123):
    rng = np.random.default_rng(seed)
    (k, beta, aic_m, bic_m), (_, aic_c, bic_c), (_, aic_s, bic_s) = fit_models(t_n, t_next)
    best_null_aic = min(aic_c, aic_s)
    delta_obs = best_null_aic - aic_m  # positive favors metallic
    count = 0
    for r in range(reps):
        perm = rng.permutation(len(t_next))
        (k2, b2, aic_m2, _), (_, aic_c2, _), (_, aic_s2, _) = fit_models(t_n, t_next[perm])
        best_null = min(aic_c2, aic_s2)
        delta = best_null - aic_m2
        if delta >= delta_obs:
            count += 1
    p = (count + 1) / (reps + 1)
    return float(delta_obs), float(p)

def audit_and_run(csv, outprefix=None, cmax_ci_pct=None, seed=123):
    df = pd.read_csv(csv)
    assert {"Y","X","Cmax"}.issubset(df.columns), "CSV must contain Y,X,Cmax"
    Y = df["Y"].astype(float).to_numpy()
    X = df["X"].astype(float).to_numpy()
    C = df["Cmax"].astype(float).to_numpy()
    # Audit: single frontier
    unique_C = np.unique(np.round(C, 9))
    single_frontier = (unique_C.size == 1)
    used_C = float(unique_C[0]) if single_frontier else float("nan")

    # Raw GEC0
    raw_gec0 = (Y / X) / C
    clamps = {
        "gt1": int(np.sum(raw_gec0 > 1.0)),
        "lt0": int(np.sum(raw_gec0 < 0.0)),
        "ge_0_99": int(np.sum(raw_gec0 >= 0.99)),
        "ge_0_95": int(np.sum(raw_gec0 >= 0.95)),
    }
    gec0 = np.clip(raw_gec0, EPS, 1 - EPS)

    # Build default consecutive pairs
    order_idx = np.arange(len(df))
    t_n, t_next, pair_rows = build_pairs(gec0, Y, X, C, order_idx)

    # Fits and CV
    (k, beta, aic_m, bic_m), (alpha0, aic_c, bic_c), (alpha1, aic_s, bic_s) = fit_models(t_n, t_next)
    mse_m = kfold_cv("metallic", t_n, t_next, K=10, seed=seed)
    mse_c = kfold_cv("null_const", t_n, t_next, K=10, seed=seed)
    mse_s = kfold_cv("null_slope", t_n, t_next, K=10, seed=seed)

    # Bootstrap CIs
    k_ci, beta_ci, tstar_ci = bootstrap_ci(t_n, t_next, B=5000, seed=seed)
    tstar = fixed_point(k, beta)

    # Permutation test
    delta_aic_obs, p_perm = permutation_test(t_n, t_next, reps=2000, seed=seed)

    # Frontier jitter within CI (if provided as ±pct)
    jitter_results = []
    if cmax_ci_pct is not None and single_frontier:
        for sign in (-1, +1):
            Cj = used_C * (1 + sign * cmax_ci_pct / 100.0)
            gec0j = np.clip((Y / X) / Cj, EPS, 1 - EPS)
            tnj, tnextj, _ = build_pairs(gec0j, Y, X, np.full_like(C, Cj), order_idx)
            (kj, bj, aic_mj, bic_mj), (_, aic_cj, bic_cj), (_, aic_sj, bic_sj) = fit_models(tnj, tnextj)
            mse_mj = kfold_cv("metallic", tnj, tnextj, K=10, seed=seed)
            jitter_results.append({
                "Cmax": float(Cj),
                "k": float(kj),
                "beta": float(bj),
                "t_star": float(fixed_point(kj, bj)),
                "aic_m": float(aic_mj),
                "bic_m": float(bic_mj),
                "mse_cv_m": float(mse_mj),
                "delta_aic_vs_best_null": float(min(aic_cj, aic_sj) - aic_mj)
            })

    # Pairing variants (random reorder → new consecutive pairs)
    pairing_variants = []
    rng = np.random.default_rng(seed)
    for r in range(5):
        perm = rng.permutation(len(df))
        tnr, tnxr, _ = build_pairs(gec0, Y, X, C, perm)
        (kr, br, aic_mr, bic_mr), (a0r, aic_cr, bic_cr), (a1r, aic_sr, bic_sr) = fit_models(tnr, tnxr)
        pairing_variants.append({
            "k": float(kr), "beta": float(br),
            "t_star": float(fixed_point(kr, br)),
            "delta_aic_vs_best_null": float(min(aic_cr, aic_sr) - aic_mr)
        })

    report = {
        "n_rows": int(len(df)),
        "n_pairs": int(len(t_n)),
        "single_frontier": bool(single_frontier),
        "used_Cmax": float(used_C) if single_frontier else None,
        "raw_gec0": {
            "min": float(raw_gec0.min()), "max": float(raw_gec0.max()),
            "mean": float(raw_gec0.mean()),
            "clamps": clamps
        },
        "fits": {
            "metallic": {"k": float(k), "beta": float(beta), "t_star": float(tstar), "aic": float(aic_m), "bic": float(bic_m), "mse_cv": float(mse_m)},
            "null_const": {"alpha": float(alpha0), "aic": float(aic_c), "bic": float(bic_c), "mse_cv": float(mse_c)},
            "null_slope": {"alpha": float(alpha1), "aic": float(aic_s), "bic": float(bic_s), "mse_cv": float(mse_s)},
            "delta_aic_obs_vs_best_null": float(min(aic_c, aic_s) - aic_m)
        },
        "bootstrap": {"k_ci": k_ci, "beta_ci": beta_ci, "t_star_ci": tstar_ci},
        "permutation_test": {"delta_aic_obs": float(delta_aic_obs), "p_value": float(p_perm)},
        "frontier_jitter": jitter_results,
        "pairing_variants": pairing_variants
    }

    if outprefix:
        os.makedirs(os.path.dirname(outprefix), exist_ok=True) if os.path.dirname(outprefix) else None
        with open(outprefix + "_proof_report.json", "w") as f:
            json.dump(report, f, indent=2)
    return report

def main():
    ap = argparse.ArgumentParser(description="Metallic-means proof harness (audit + robust tests)")
    ap.add_argument("csv", help="CSV with columns Y,X,Cmax")
    ap.add_argument("--outprefix", default=None, help="Prefix for JSON report file")
    ap.add_argument("--cmax_ci_pct", type=float, default=None, help="Frontier CI half-width as percent (e.g., 0.5 means ±0.5%)")
    args = ap.parse_args()
    rep = audit_and_run(args.csv, outprefix=args.outprefix, cmax_ci_pct=args.cmax_ci_pct)
    print(json.dumps(rep, indent=2))

if __name__ == "__main__":
    main()