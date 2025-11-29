# scripts/metallic_convergence.py
import numpy as np
import matplotlib.pyplot as plt

def metallic_recurrence(t0, k, steps=15):
    t = [t0]
    for _ in range(steps):
        t.append(k + 1/t[-1])
    return np.array(t)

ks = [1, 2, 3, 4]
t0 = 1.0
steps = 15

plt.figure(figsize=(8, 5))
for k in ks:
    t = metallic_recurrence(t0, k, steps)
    plt.plot(range(steps+1), t, 'o-', label=f'k={k}, t*≈{ (k + np.sqrt(k**2 + 4))/2 :.3f}')
    plt.axhline((k + np.sqrt(k**2 + 4))/2, linestyle='--', alpha=0.5)
plt.xlabel("Iteration")
plt.ylabel("t_n")
plt.title("Convergence to Metallic Means")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../figures/metallic_convergence.png", dpi=300, bbox_inches='tight')
plt.close()