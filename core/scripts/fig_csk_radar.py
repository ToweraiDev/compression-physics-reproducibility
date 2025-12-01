# scripts/fig_csk_radar.py
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

factors = ['S', 'H', 'D', 'R', 'E']
ml = [0.90, 0.80, 0.95, 0.88, 0.92]      # Machine Learning (GEC₀ ≈ 0.95)
thermo = [0.75, 0.65, 0.80, 0.85, 0.70]  # Thermodynamics (GEC₀ ≈ 0.81)

angles = np.linspace(0, 2 * np.pi, len(factors), endpoint=False).tolist()
ml += ml[:1]; thermo += thermo[:1]; angles += angles[:1]

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, ml, 'o-', linewidth=2, label='ML (GEC₀=0.95)')
ax.fill(angles, ml, alpha=0.25)
ax.plot(angles, thermo, 's-', linewidth=2, label='Thermo (GEC₀=0.81)')
ax.fill(angles, thermo, alpha=0.25)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(factors)
ax.set_ylim(0, 1)
ax.set_title('CSK Diagnostics: ML vs. Thermodynamics')
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

plt.savefig(FIGURES_DIR / "fig_csk_radar.png", dpi=300, bbox_inches='tight')
plt.close()