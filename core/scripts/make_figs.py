#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate figs for the GEC paper, consistent with Table VI:
  Fig. 1: Estimated fixed points (median ± 95% bootstrap CI) across estimators
          for two models: additive-epsilon and multiplicative-epsilon.
  Fig. 2: Median MSE to phi (log scale) by estimator and model.

Outputs:
  - fig1_aggregator_means_ci.pdf
  - fig2_mse_vs_phi.pdf
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ------------------ Shared simulation config ------------------
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ Shared simulation config ------------------
phi = (1 + 5**0.5) / 2
k = 1.0  # symmetric case

# Domain noise scales (matched to make_table_vi.py magnitudes, but we just
# use one representative sigma per figure for clarity)
SIGMA = 0.03   # global noise scale used to build the figure panels

B = 600        # bootstrap replicates
n = 80         # draws per replicate
seed = 123     # figure seed (separate from table seed for independence)
rng = np.random.default_rng(seed)

# ------------------ Fixed-point models ------------------
def t_from_eps_additive(eps, k=1.0):
    """
    Additive perturbation to the metallic-mean relation:
    t = k + 1/t + eps  -> positive root of t^2 - (k+eps) t - 1 = 0
    """
    a = k + eps
    return 0.5 * (a + np.sqrt(a * a + 4.0))

def t_from_eps_multiplicative(eps, k=1.0):
    """
    Multiplicative perturbation around the symmetric map:
    t = (k + 1/t) * (1 + eps)
    Empirically solve for t by fixed-point iteration (converges quickly).
    """
    t = np.full_like(eps, phi, dtype=float)  # good initializer
    for _ in range(25):
        t = (k + 1.0 / np.clip(t, 1e-12, None)) * (1.0 + eps)
    return t

# ------------------ Robust aggregators ------------------
def gmean(x):
    x = np.asarray(x, dtype=float)
    return float(np.exp(np.mean(np.log(np.clip(x, 1e-12, None)))))

def trimmed_mean(x, proportion_to_cut=0.10):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    k = int(np.floor(proportion_to_cut * n))
    if n - 2 * k <= 0:
        return float(np.mean(x))
    return float(np.mean(x[k:n - k]))

def winsorized_mean(x, proportion=0.05):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    k = int(np.floor(proportion * n))
    lo = x[k]
    hi = x[-k - 1] if k > 0 else x[-1]
    xw = np.clip(x, lo, hi)
    return float(np.mean(xw))

ESTIMATORS = {
    "geom_mean": gmean,
    "mean":      lambda x: float(np.mean(x)),
    "median":    lambda x: float(np.median(x)),
    "trimmed":   lambda x: trimmed_mean(x, 0.10),
    "winsor":    lambda x: winsorized_mean(x, 0.05),
}

ESTIMATOR_LABELS = {
    "geom_mean": "geom_mean",
    "mean":      "mean",
    "median":    "median",
    "trimmed":   "trimmed_mean_10%",
    "winsor":    "winsorized_mean_5%",
}

# ------------------ Bootstrap helpers ------------------
def bootstrap_estimates(model_fn, sigma, B, n):
    """
    Returns:
      est_map: dict(estimator -> array[B] of bootstrap point estimates t_hat)
    """
    out = {name: [] for name in ESTIMATORS}
    for _ in range(B):
        eps = rng.normal(0.0, sigma, size=n)
        t = model_fn(eps, k=k)
        for name, est in ESTIMATORS.items():
            out[name].append(est(t))
    for name in out:
        out[name] = np.asarray(out[name], dtype=float)
    return out

def ci_low_high(arr, alpha=0.05):
    lo = np.quantile(arr, alpha/2.0)
    hi = np.quantile(arr, 1.0 - alpha/2.0)
    return lo, hi

# ------------------ Compute fig data ------------------
add_est = bootstrap_estimates(t_from_eps_additive, SIGMA, B, n)
mul_est = bootstrap_estimates(t_from_eps_multiplicative, SIGMA, B, n)

# Fig 1 data: medians and 95% CIs for each estimator, both models
fig1_estimators = ["geom_mean", "mean", "median", "trimmed", "winsor"]

add_median = [np.median(add_est[e]) for e in fig1_estimators]
add_lohi   = [ci_low_high(add_est[e]) for e in fig1_estimators]

mul_median = [np.median(mul_est[e]) for e in fig1_estimators]
mul_lohi   = [ci_low_high(mul_est[e]) for e in fig1_estimators]

# Fig 2 data: median MSE vs phi (log scale)
def mse_to_phi(samples):
    return np.median((samples - phi) ** 2)

add_mse = [mse_to_phi(add_est[e]) for e in fig1_estimators]
mul_mse = [mse_to_phi(mul_est[e]) for e in fig1_estimators]

# ------------------ Plot: Fig 1 ------------------
x = np.arange(len(fig1_estimators))

# additive
add_err_lo = [med - lo for med, (lo, hi) in zip(add_median, add_lohi)]
add_err_hi = [hi - med for med, (lo, hi) in zip(add_median, add_lohi)]

# multiplicative
mul_err_lo = [med - lo for med, (lo, hi) in zip(mul_median, mul_lohi)]
mul_err_hi = [hi - med for med, (lo, hi) in zip(mul_median, mul_lohi)]

plt.figure(figsize=(6.5, 3.6))
# We draw two errorbar series; no explicit colors/styles (per your constraints)
plt.errorbar(x - 0.08, add_median, yerr=[add_err_lo, add_err_hi],
             fmt='o', capsize=3, label="additive-ε")
plt.errorbar(x + 0.08, mul_median, yerr=[mul_err_lo, mul_err_hi],
             fmt='s', capsize=3, label="multiplicative-ε")

plt.axhline(phi, linestyle='--', linewidth=1)  # dashed φ reference
plt.xticks(x, [ESTIMATOR_LABELS[e] for e in fig1_estimators], rotation=30, ha='right')
plt.ylabel("fixed-point estimate $\\hat t$")
plt.title("Aggregator estimates: median ± 95% CI")
plt.legend()
plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig1_aggregator_means_ci.pdf")
plt.close()

# ------------------ Plot: Fig 2 ------------------
plt.figure(figsize=(6.5, 3.6))
width = 0.35
plt.bar(x - width/2, add_mse, width=width, label="additive-ε")
plt.bar(x + width/2, mul_mse, width=width, label="multiplicative-ε")
plt.yscale('log')
plt.xticks(x, [ESTIMATOR_LABELS[e] for e in fig1_estimators], rotation=30, ha='right')
plt.ylabel("Median MSE vs $\\varphi$")
plt.title("Median MSE to $\\varphi$ by estimator and model (lower is better)")
plt.legend()
plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig2_mse_vs_phi.pdf")
plt.close()

print("Wrote: fig1_aggregator_means_ci.pdf, fig2_mse_vs_phi.pdf")
