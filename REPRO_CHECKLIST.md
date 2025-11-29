# Reproducibility Checklist Status

## Environment blockers
- Base Python scientific stack is present (scripts relying on `numpy`, `pandas`, `matplotlib` all ran locally).
- Notebook execution remains **blocked**: `jupyter-nbconvert` is missing and `pip install nbconvert` fails because the proxy
  returns `403 Forbidden`.
- PDF inspection utilities (e.g., `pdftotext`) are not installed, so visual/line-for-line comparisons to `GECv2.pdf` still
  require an external viewer.

## Minimal environment to add
- Install `nbconvert` (and friends like `nbclient`, `ipykernel`) once network access is available so the notebooks can be
  executed headlessly.
- Optional but helpful system packages for reproducible figure builds:
  - `texlive-full` (only needed if regenerating LaTeX/PDF artifacts locally)
  - `ghostscript` (PDF tooling)
  - `poppler-utils` (PDF comparison utilities like `pdfinfo`, `pdftocairo`)

### Quick setup recipe (once network access is available)
1) Create/activate a venv: `python3 -m venv .venv && source .venv/bin/activate`.
2) Install Python deps: `pip install numpy pandas matplotlib seaborn ipykernel nbformat nbclient nbconvert` (currently blocked
   by the proxy).
3) (Optional) Install PDF helpers via system packages: `sudo apt-get install texlive-full ghostscript poppler-utils`.

## Figures — scripts, commands, and checks
- **Figure 1 — CSK Radar**
  - Script: `core/scripts/make_figs.py`.
  - Command: `python core/scripts/make_figs.py` (writes `fig1_aggregator_means_ci.pdf`).
  - Check: median/CI bands match the paper’s PDF.
  - Status: ✅ script runs and emits the PDF; visual check against the paper is still manual.
- **Figure 2 — Frontier Diagram**
  - LaTeX-only; no code rerun needed.
- **Figure 3 + 4 — Metallic Convergence + Error Decay**
  - Script: `phi demo/phi_proof_harness.py` (uses the bundled demo CSVs).
  - Command: `python "phi demo/phi_proof_harness.py" "phi demo/demo_symmetric.csv"` (regenerates PDFs/PNGs; CSV required).
  - Check: visually compare regenerated figures to the manuscript.
  - Status: ✅ run completed on `demo_symmetric.csv`; visual comparison to the PDF still needed.
- **Figure 5 — Aggregator Fixed-Point CI**
  - Script: `phi demo/phi_aggregator_runner.py`.
  - Command: run against each demo CSV, e.g. `python "phi demo/phi_aggregator_runner.py" "phi demo/demo_symmetric.csv" 800`.
  - Check: confirm the fixed-point estimates/CI match the final PDF.
  - Status: ✅ runs cleanly on `demo_symmetric.csv`, `demo_asymmetric.csv`, and `demo_null.csv`; numbers need cross-check
    versus the manuscript.
- **Figure 6 — MSE to φ**
  - Script: `core/scripts/make_figs.py` (writes `fig2_mse_vs_phi.pdf`).
  - Command: `python core/scripts/make_figs.py`.
  - Check: bar heights/log-scale MSE values align with the paper.
  - Status: ✅ generated alongside Figure 1; confirm visually against the PDF.
- **Figure 7 — GEC Across Domains**
  - Notebook: `core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb`.
  - Command: execute the notebook (e.g., `jupyter nbconvert --to notebook --execute core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb --output tmp.ipynb`).
  - Check: values for Communications/Thermodynamics/ML/Finance/Governance match the PDF.
  - Status: ⚠️ blocked by missing `jupyter-nbconvert` (proxy prevents installing `nbconvert`).

## Tables — scripts, commands, and checks
- **Table 3 — Case Studies**
  - Notebook: `core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb`.
  - Check: notebook outputs must match the manuscript exactly.
  - Status: ⚠️ blocked by missing `jupyter-nbconvert` (proxy prevents installing `nbconvert`).
- **Table 4 — Robustness Grid**
  - Script: `core/scripts/make_table-vi.py`.
  - Command: `python core/scripts/make_table-vi.py` (writes `tab_robust_grid.tex`).
  - Check: medians/errors match the PDF grid.
  - Status: ✅ script executes and prints the LaTeX table; manual numeric comparison to the PDF still required.
- **Table 5 — Aggregator Robustness**
  - Script: `phi demo/phi_aggregator_runner.py` against the demo CSVs.
  - Command: e.g., `python "phi demo/phi_aggregator_runner.py" "phi demo/demo_asymmetric.csv" 800`.
  - Check: ensure the printed JSON/CI matches the PDF.
  - Status: ✅ ran on the bundled demo CSVs; compare outputs to the PDF to finish validation.
- **Table 6 — DEA Sensitivity**
  - Notebook: `core/notebooks/GEC_Toolkit_Pro.ipynb` (or `GEC_Compression_Physics_Toolkit.ipynb`).
  - Command: execute the notebook and compare the derived numbers to the manuscript.
  - Status: ⚠️ notebook execution blocked by missing `jupyter-nbconvert` (proxy prevents installing `nbconvert`).
