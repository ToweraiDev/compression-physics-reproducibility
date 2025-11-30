import subprocess
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPTS_DIR = os.path.join(ROOT, "core", "scripts")
PHI_DEMO_DIR = os.path.join(ROOT, "phi demo")

def run(label, cmd):
    print(f"\n===== Running: {label} =====")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ ERROR in: {label}")
        sys.exit(result.returncode)
    print(f"✅ Done: {label}")

# -------------------------------
# Run figure scripts
# -------------------------------
run("CSK Radar", f"python \"{os.path.join(SCRIPTS_DIR, 'fig_csk_radar.py')}\"")
run("GEC Results Bar", f"python \"{os.path.join(SCRIPTS_DIR, 'gec_results_bar.py')}\"")
run("Fig1 Aggregator Means CI", f"python \"{os.path.join(SCRIPTS_DIR, 'fig1_aggregator_means_ci.py')}\"")
run("Metallic Convergence", f"python \"{os.path.join(SCRIPTS_DIR, 'metallic_convergence.py')}\"")
run("Convergence Rate", f"python \"{os.path.join(SCRIPTS_DIR, 'convergence_rate.py')}\"")

# -------------------------------
# Run Table Scripts
# -------------------------------
run("Robustness Grid Table (Table VI)", f"python \"{os.path.join(SCRIPTS_DIR, 'make_table-vi.py')}\"")

# -------------------------------
# Run Phi Demo scripts
# -------------------------------
phi_runner = os.path.join(PHI_DEMO_DIR, "phi_aggregator_runner.py")
phi_harness = os.path.join(PHI_DEMO_DIR, "phi_proof_harness.py")

demo_symmetric = os.path.join(PHI_DEMO_DIR, "demo_symmetric.csv")
demo_asymmetric = os.path.join(PHI_DEMO_DIR, "demo_asymmetric.csv")
demo_null = os.path.join(PHI_DEMO_DIR, "demo_null.csv")

run("Phi Aggregator (Symmetric)", f"python \"{phi_runner}\" \"{demo_symmetric}\" 800")
run("Phi Aggregator (Asymmetric)", f"python \"{phi_runner}\" \"{demo_asymmetric}\" 800")
run("Phi Aggregator (Null)", f"python \"{phi_runner}\" \"{demo_null}\" 800")

run("Phi Proof Harness", f"python \"{phi_harness}\" \"{demo_symmetric}\"")

print("\n🎉 All scripts successfully executed!")
