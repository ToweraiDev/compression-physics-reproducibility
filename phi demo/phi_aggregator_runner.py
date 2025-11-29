
import sys, json
import numpy as np
import pandas as pd
from numpy.random import default_rng

def odds(x, eps=1e-9):
    x = np.clip(x, eps, 1-eps)
    return x / (1 - x)

def run(csv_path, bootstrap=500, seed=123):
    df = pd.read_csv(csv_path)
    for col in ["Y","X","Cmax"]:
        if col not in df.columns:
            raise SystemExit(f"CSV must contain columns Y,X,Cmax (missing {col})")
    eps = 1e-9
    gec0 = (df["Y"].values / df["X"].values) / df["Cmax"].values
    gec0 = np.clip(gec0, eps, 1-eps)

    pairs = [(i, i+1) for i in range(0, len(gec0)-1, 2)]

    t_n = []
    t_next = []
    Y = df["Y"].values
    X = df["X"].values
    C = df["Cmax"].values

    for (i,j) in pairs:
        tA = odds(gec0[i])
        tB = odds(gec0[j])
        t_sym = 0.5*(tA + tB)
        Ym = Y[i] + Y[j]
        Xm = X[i] + X[j]
        Cmerge = 0.5*(C[i] + C[j])
        gm = np.clip((Ym / Xm) / Cmerge, 1e-9, 1-1e-9)
        tm = odds(gm)
        t_n.append(t_sym)
        t_next.append(tm)

    t_n = np.array(t_n)
    t_next = np.array(t_next)

    inv = 1.0 / t_n
    A = np.vstack([np.ones_like(inv), inv]).T
    k_hat, beta_hat = np.linalg.lstsq(A, t_next, rcond=None)[0]
    star = (k_hat + np.sqrt(max(k_hat**2 + 4*beta_hat, 0.0))) / 2.0

    rng = default_rng(seed)
    Ks, Betas, Stars = [], [], []
    n = len(t_n)
    for _ in range(bootstrap):
        sel = rng.integers(0, n, n)
        inv_b = inv[sel]
        y_b = t_next[sel]
        A_b = np.vstack([np.ones_like(inv_b), inv_b]).T
        kb, bb = np.linalg.lstsq(A_b, y_b, rcond=None)[0]
        Ks.append(kb); Betas.append(bb)
        Stars.append((kb + np.sqrt(max(kb**2 + 4*bb, 0.0))) / 2.0)

    def ci(arr, a=2.5, b=97.5):
        return float(np.percentile(arr, a)), float(np.percentile(arr, b))

    out = {
        "n_pairs": int(len(pairs)),
        "k": float(k_hat),
        "beta": float(beta_hat),
        "fixed_point": float(star),
        "k_CI": ci(Ks),
        "beta_CI": ci(Betas),
        "fixed_point_CI": ci(Stars),
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python phi_aggregator_runner.py <path_to_csv> [bootstrap=500]")
        sys.exit(1)
    csv_path = sys.argv[1]
    bootstrap = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    run(csv_path, bootstrap)
