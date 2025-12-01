#!/usr/bin/env python3
# scripts/fig1_aggregator_means_ci.py
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

aggregators = ["Multiplicative", "Fibonacci-like", "Cobb–Douglas", "LSE"]
medians = [1.6180341, 1.6180347, 1.6180342, 1.6180340]
errors = [0.000012, 0.000009, 0.000014, 0.000011]

x = np.arange(len(aggregators))
phi = (1 + np.sqrt(5)) / 2

fig, ax = plt.subplots(figsize=(8.5, 4.8))
ax.errorbar(x, medians, yerr=errors, fmt="o", capsize=7, capthick=2,
            markersize=10, color="#1f77b4", elinewidth=2)
ax.axhline(phi, color="red", linestyle="--", linewidth=2,
           label=r"$\varphi = 1.618033988749895$")
ax.set_xticks(x)
ax.set_xticklabels(["Multiplicative", "Fibonacci-\nlike", "Cobb–\nDouglas", "LSE"], fontsize=11)
ax.set_ylim(1.618020, 1.618050)
ax.set_ylabel("Estimated Fixed Point", fontsize=12)
ax.set_title("Fixed-Point Estimates Across Aggregators\n(Median ± 95% Bootstrap CI)", fontsize=13)

# CRITICAL FIX: Disable offset notation
ax.ticklabel_format(style='plain', axis='y', useOffset=False)

ax.grid(True, axis='y', linestyle=':', alpha=0.6)
ax.legend(fontsize=11)
plt.tight_layout(pad=2.0)
plt.subplots_adjust(bottom=0.20)
plt.savefig(FIGURES_DIR / "fig1_aggregator_means_ci.png", dpi=500, bbox_inches='tight')
plt.savefig(FIGURES_DIR / "fig1_aggregator_means_ci.pdf", bbox_inches='tight')
plt.close()
print("✓ Fixed-point estimates figure saved (offset disabled)")