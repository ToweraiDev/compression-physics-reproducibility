# scripts/gec_results_bar.py
import matplotlib.pyplot as plt

domains = ["Comms", "Thermo", "ML", "Finance", "Governance"]
gec0 = [0.87, 0.81, 0.95, 0.44, 0.88]

plt.figure(figsize=(9, 5))
bars = plt.bar(domains, gec0, color='#4477AA', edgecolor='black')
plt.axhline(1.0, color='red', linestyle='--', linewidth=1.5, label='Frontier')
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{height:.2f}', ha='center', va='bottom', fontsize=11)
plt.ylim(0, 1.05)
plt.ylabel('GEC₀')
plt.title('GEC₀ Across Domains (Real 2024 Data)')
plt.legend()
plt.tight_layout()
plt.savefig("../figures/gec_results_real.png", dpi=300, bbox_inches='tight')
plt.close()