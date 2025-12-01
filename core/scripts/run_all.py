import sys
import subprocess

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "core" / "scripts"
PHI_DEMO_DIR = ROOT / "phi demo"
FIGURES_DIR = ROOT / "core" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

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
python = sys.executable

run("CSK Radar", f"\"{python}\" \"{SCRIPTS_DIR / 'fig_csk_radar.py'}\"")
run("GEC Results Bar", f"\"{python}\" \"{SCRIPTS_DIR / 'gec_results_bar.py'}\"")
run("Fig1 Aggregator Means CI", f"\"{python}\" \"{SCRIPTS_DIR / 'fig1_aggregator_means_ci.py'}\"")
run("Metallic Convergence", f"\"{python}\" \"{SCRIPTS_DIR / 'metallic_convergence.py'}\"")
run("Convergence Rate", f"\"{python}\" \"{SCRIPTS_DIR / 'convergence_rate.py'}\"")

# -------------------------------
# Run Table Scripts
# -------------------------------
run("Robustness Grid Table (Table VI)", f"\"{python}\" \"{SCRIPTS_DIR / 'make_table-vi.py'}\"")

# -------------------------------
# Run Phi Demo scripts
# -------------------------------
phi_runner = PHI_DEMO_DIR / "phi_aggregator_runner.py"
phi_harness = PHI_DEMO_DIR / "phi_proof_harness.py"

demo_symmetric = PHI_DEMO_DIR / "demo_symmetric.csv"
demo_asymmetric = PHI_DEMO_DIR / "demo_asymmetric.csv"
demo_null = PHI_DEMO_DIR / "demo_null.csv"

run("Phi Aggregator (Symmetric)", f"\"{python}\" \"{phi_runner}\" \"{demo_symmetric}\" 800")
run("Phi Aggregator (Asymmetric)", f"\"{python}\" \"{phi_runner}\" \"{demo_asymmetric}\" 800")
run("Phi Aggregator (Null)", f"\"{python}\" \"{phi_runner}\" \"{demo_null}\" 800")

run("Phi Proof Harness", f"\"{python}\" \"{phi_harness}\" \"{demo_symmetric}\"")

print("\n🎉 All scripts successfully executed!")
