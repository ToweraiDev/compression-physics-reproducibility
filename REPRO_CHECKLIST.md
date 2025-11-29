# Reproducibility Checklist Status

## Environment blockers
- Python dependencies required by the figure/table scripts are not present, and `pip install` is blocked by the proxy (see `pip install numpy pandas matplotlib`).

## Minimal environment to add
- Python 3.10+
- Python packages (pip installable):
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `seaborn` (used in notebooks for nicer plots)
- Jupyter stack for notebooks:
  - `ipykernel`
  - `nbformat`
  - `nbclient`
- Optional but helpful system packages for reproducible figure builds:
  - `texlive-full` (only needed if regenerating LaTeX/PDF artifacts locally)
  - `ghostscript` (PDF tooling)
  - `poppler-utils` (PDF comparison utilities like `pdfinfo`, `pdftocairo`)

### Quick setup recipe (once network access is available)
1) Create/activate a venv: `python3 -m venv .venv && source .venv/bin/activate`.
2) Install Python deps: `pip install numpy pandas matplotlib seaborn ipykernel nbformat nbclient`.
3) (Optional) Install PDF helpers via system packages: `sudo apt-get install texlive-full ghostscript poppler-utils`.

## Figures — scripts, commands, and checks
- **Figure 1 — CSK Radar**
  - Script: `core/scripts/make_figs.py`.
  - Command: `python core/scripts/make_figs.py` (writes `fig1_aggregator_means_ci.pdf`).
  - Check: median/CI bands match the paper’s PDF.
  - Status: blocked until `numpy`/`matplotlib` install succeeds.
- **Figure 2 — Frontier Diagram**
  - LaTeX-only; no code rerun needed.
- **Figure 3 + 4 — Metallic Convergence + Error Decay**
  - Script: `phi demo/phi_proof_harness.py` (uses the bundled demo CSVs).
  - Command: `python "phi demo/phi_proof_harness.py"` (regenerates PDFs/PNGs).
  - Check: visually compare regenerated figures to the manuscript.
  - Status: pending because `numpy`/`pandas` are missing.
- **Figure 5 — Aggregator Fixed-Point CI**
  - Script: `phi demo/phi_aggregator_runner.py`.
  - Command: run against each demo CSV, e.g. `python "phi demo/phi_aggregator_runner.py" "phi demo/demo_symmetric.csv" 800`.
  - Check: confirm the fixed-point estimates/CI match the final PDF.
  - Status: pending dependency install.
- **Figure 6 — MSE to φ**
  - Script: `core/scripts/make_figs.py` (writes `fig2_mse_vs_phi.pdf`).
  - Command: `python core/scripts/make_figs.py`.
  - Check: bar heights/log-scale MSE values align with the paper.
  - Status: same dependency block as Figure 1.
- **Figure 7 — GEC Across Domains**
  - Notebook: `core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb`.
  - Command: execute the notebook (e.g., `jupyter nbconvert --to notebook --execute core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb --output tmp.ipynb`).
  - Check: values for Communications/Thermodynamics/ML/Finance/Governance match the PDF.
  - Status: pending Python deps.

## Tables — scripts, commands, and checks
- **Table 3 — Case Studies**
  - Notebook: `core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb`.
  - Check: notebook outputs must match the manuscript exactly.
- **Table 4 — Robustness Grid**
  - Script: `core/scripts/make_table-vi.py`.
  - Command: `python core/scripts/make_table-vi.py` (writes `tab_robust_grid.tex`).
  - Check: medians/errors match the PDF grid.
- **Table 5 — Aggregator Robustness**
  - Script: `phi demo/phi_aggregator_runner.py` against the demo CSVs.
  - Command: e.g., `python "phi demo/phi_aggregator_runner.py" "phi demo/demo_asymmetric.csv" 800`.
  - Check: ensure the printed JSON/CI matches the PDF.
- **Table 6 — DEA Sensitivity**
  - Notebook: `core/notebooks/GEC_Toolkit_Pro.ipynb` (or `GEC_Compression_Physics_Toolkit.ipynb`).
  - Command: execute the notebook and compare the derived numbers to the manuscript.
