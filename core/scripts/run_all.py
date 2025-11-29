import subprocess
import sys
import os

# Change into scripts directory
BASE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(BASE, "..", "figures")
os.makedirs(FIGDIR, exist_ok=True)

print("\n=== Running All Reproducibility Scripts ===\n")

def run(cmd):
    print(f"\n--- Running: {cmd} ---\n")
    subprocess.run(cmd, shell=True, check=True)

# Figure scripts
run("python scripts/fig_csk_radar.py")
run("python scripts/gec_results_bar.py")
run("python scripts/fig1_aggregator_means_ci.py")
run("python scripts/metallic_convergence.py")
run("python scripts/convergence_rate.py")

# Metallic harness (v1-style)
run('python "phi demo/phi_proof_harness.py" "phi demo/demo_symmetric.csv"')

# Aggregator runner for demo CSVs
run('python "phi demo/phi_aggregator_runner.py" "phi demo/demo_symmetric.csv" 800')
run('python "phi demo/phi_aggregator_runner.py" "phi demo/demo_asymmetric.csv" 800')
run('python "phi demo/phi_aggregator_runner.py" "phi demo/demo_null.csv" 800')

print("\n=== ALL DONE — Figures & Outputs Generated ===\n")
