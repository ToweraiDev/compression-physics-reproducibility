#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate Table VI (Median |t* - phi| by domain and estimator).
Writes a LaTeX tabular snippet to 'tab_robust_grid.tex'.

Model:
  t = k + 1/t + epsilon,   epsilon ~ N(0, sigma_domain)

For each domain:
  - Repeat B bootstrap replicates; each replicate uses n draws of epsilon.
  - For each replicate, aggregate the t-samples with a chosen estimator
    (geom mean, mean, median, 10% trimmed mean, 5% winsorized mean),
    then record |t_hat - phi|.
  - Report the median across replicates (per estimator).
"""

import math
from pathlib import Path

import numpy as np

# --- Fixed-point + golden ratio ---
phi = (1 + 5**0.5) / 2
k = 1.0  # symmetric binary-merge case

def t_from_eps(eps, k=1.0):
    """Closed-form positive root of t^2 - (k+eps) t - 1 = 0."""
    a = k + eps
    return 0.5 * (a + np.sqrt(a * a + 4.0))

# --- Robust aggregators ---
def gmean(x):
    x = np.asarray(x, dtype=float)
    return float(np.exp(np.mean(np.log(x))))

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
    "Geom":   gmean,
    "Mean":   lambda x: float(np.mean(x)),
    "Median": lambda x: float(np.median(x)),
    "Trim":   lambda x: trimmed_mean(x, 0.10),
    "Winsor": lambda x: winsorized_mean(x, 0.05),
}

# --- Domains + noise scales (tunable, but fixed for reproducibility) ---
DOMAINS = {
    "Comms":   0.02,  # lower noise
    "Thermo":  0.05,
    "ML":      0.015,
    "Finance": 0.06,  # higher noise
    "Govern.": 0.04,
}

# --- Bootstrap config ---
B = 600        # number of bootstrap replicates
n = 80         # draws per replicate
seed = 42
rng = np.random.default_rng(seed)

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def evaluate_domain(sigma):
    """Return dict of median |t_hat - phi| per estimator."""
    dist = {name: [] for name in ESTIMATORS}
    for _ in range(B):
        eps = rng.normal(0.0, sigma, size=n)
        t   = t_from_eps(eps, k=k)
        for name, est in ESTIMATORS.items():
            t_hat = est(t)
            dist[name].append(abs(t_hat - phi))
    return {name: float(np.median(vals)) for name, vals in dist.items()}

def main():
    # Compute medians
    table = {dom: evaluate_domain(sig) for dom, sig in DOMAINS.items()}

    # Format as LaTeX tabular (matches your manuscript’s columns)
    header = (
        "\\begin{table}[!t]\n"
        "\\centering\n"
        "\\caption{Median $|t^* - \\varphi|$ by domain and estimator (lower is better).}\n"
        "\\label{tab:robust_grid}\n"
        "\\small\n"
        "\\begin{tabular}{@{}lccccc@{}}\n"
        "\\toprule\n"
        "Domain & Geom & Mean & Median & Trim & Winsor \\\\\n"
        "\\midrule\n"
    )

    def fmt(x):  # 4 decimal places, leading zero
        return f"{x:.4f}"

    rows = []
    for dom in ["Comms", "Thermo", "ML", "Finance", "Govern."]:
        vals = table[dom]
        row = (
            f"{dom} & {fmt(vals['Geom'])} & {fmt(vals['Mean'])} & "
            f"{fmt(vals['Median'])} & {fmt(vals['Trim'])} & {fmt(vals['Winsor'])} \\\\"
        )
        rows.append(row)

    footer = (
        "\n\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}\n"
    )

    tex = header + "\n".join(rows) + footer
    (FIGURES_DIR / "tab_robust_grid.tex").write_text(tex, encoding="utf-8")

    # Also print a compact version to the console
    print(tex)

if __name__ == "__main__":
    main()
