# scripts/convergence_rate.py
import numpy as np
import matplotlib.pyplot as plt

phi = (1 + np.sqrt(5)) / 2
t = np.array([1.0])
errors = []
for i in range(20):
    t_next = 1 + 1/t[-1]
    t = np.append(t, t_next)
    errors.append(abs(t[-1] - phi))

plt.figure(figsize=(7, 4))
plt.semilogy(errors, 'o-', color='purple')
plt.xlabel("Iteration")
plt.ylabel("Error |t_n - φ|")
plt.title("Convergence Rate to φ (k=1)")
plt.grid(True, which="both", ls=":", alpha=0.6)
plt.tight_layout()
plt.savefig("../figures/convergence_rate.png", dpi=300, bbox_inches='tight')
plt.close()