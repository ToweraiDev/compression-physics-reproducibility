
# Reproducibility

1) Compute raw efficiency: `eta = Y/T`.
2) Choose `C_max` per domain (theory/physical/empirical).
3) Primary index: `GEC_0 = eta / C_max` with 95% CIs if available.
4) Optional composite: `GEC = GEC_0 * lambda_geom(S,H,D,R,E)`.
5) See `artifacts/Compression_Physics_GEC_CaseStudies.ipynb` for examples.
Right now that Reproducibility.md is basically a v1 stub pointing at an old `artifacts/…` path. 

You’re fine to keep the “spirit” of it, but for v2 you really want something that:

* Matches the **current repo layout** (`core/`, `phi_demo/`, `validator/`).
* Spells out **environment + commands** for each figure/table.
* Makes it clear what is **required** vs **optional**.

Here’s a drop-in replacement you can paste over `core/Reproducibility.md` and tweak if you like.

---

````markdown
# Reproducibility Guide — Compression Physics / GEC v2.0

This repository accompanies the paper:

> **Compression Physics: A Domain-Normalized Efficiency Index (Generalized Efficiency Coefficient)** (v2.0)

It contains the code, data, and notebooks required to recompute the main
numbers, figures, and tables in the manuscript.

---

## 1. Repository layout

- `GECv2.pdf`  
  Final paper (v2.0) that this repo reproduces.

- `core/`
  - `Reproducibility.md` (this file)
  - `scripts/` – small, single-purpose scripts for figures/tables:
    - `fig_csk_radar.py` – CSK radar plot (ML vs Thermodynamics).
    - `gec_results_bar.py` – GEC₀ across domains (supports Table 3 / Fig “GEC across domains”).
    - `fig1_aggregator_means_ci.py` – metallic fixed-point CI plot (Fig. 1).
    - `metallic_convergence.py` – convergence to metallic means (Fig. 2 in v2).
    - `convergence_rate.py` – convergence error vs φ (supporting metallic section).
    - `make_table-vi.py` – robustness grid LaTeX table (Table 4 in v2).
  - `notebooks/`
    - `Compression_Physics_GEC_CaseStudies.ipynb` – reproduces the cross-domain case study numbers and main GEC₀ table.
    - `GEC_Toolkit_Pro.ipynb` – DEA / finance sensitivity, toolkit-style examples.
    - `GEC_Compression_Physics_Toolkit.ipynb` – core GEC/CSK API usage and simple demos.
  - `figures/` – output directory; scripts write here (`*.png` / `*.pdf`).

- `phi_demo/`
  - `phi_aggregator_runner.py` – “metallic map” aggregator runner (Table 5 / Fig 5).
  - `phi_proof_harness.py` – harness for the metallic vs null maps (Fig 3 + Fig 4 style outputs).
  - `demo_symmetric.csv` – synthetic “φ-like” data.
  - `demo_asymmetric.csv` – asymmetric metallic data.
  - `demo_null.csv` – null/non-metallic data.
  - `README.txt` – short description of the harness and CSVs.

- `validator/`
  - `gec_metallic_validator.py` – CLI + library helper for validating metallic-mean patterns on arbitrary real datasets.
  - `_DL___Real-Data_Validator__Template_Demo_.csv` – template for plugging in your own efficiency ratios.
  - `_DL___Model_Comparison_Summary.csv` – example output summary for the ΦDL / validator.
  - `gec_example_rows.csv` – minimal example rows for the validator.

---

## 2. Environment

A minimal environment that reproduces all *scripts* (and notebooks, once Jupyter is installed):

```text
Python 3.10+
numpy
pandas
matplotlib
seaborn          # used in notebooks only
ipykernel
nbformat
nbclient
nbconvert         # for headless notebook runs
````

Suggested `requirements.txt`:

```text
numpy>=1.26
pandas>=2.0
matplotlib>=3.8
seaborn>=0.13
ipykernel>=6.0
nbformat>=5.9
nbclient>=0.9
nbconvert>=7.0
```

Optional but useful for LaTeX/PDF workflows (not required just to recompute numbers):

* `texlive-full` (or equivalent TeX distribution)
* `ghostscript`
* `poppler-utils` (e.g., `pdftotext`, `pdftocairo`)

### Quick setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

All commands below assume you are in the repo root and the virtualenv is active.

---

## 3. Core efficiency index (GEC₀) & CSK

The basic calculation, shared across all examples:

1. **Raw efficiency**:
   [
   \eta = \frac{Y}{X}
   ]
   where `Y` = validated yield, `X` = input.

2. **Frontier choice**: choose a `C_max` per domain:

   * Theoretical (e.g., Shannon, Carnot),
   * Physical (exergy / measurement-constrained),
   * Empirical (DEA/Pareto frontier).

3. **Primary index** (reported in tables/figures):
   [
   \text{GEC}*0 = \eta / C*{\max}
   ]
   with 95% CIs when available.

4. **Diagnostic CSK vector**:
   [
   \vec{\kappa} = (S,H,D,R,E)\in[0,1]^5
   ]
   reported or used qualitatively as structural/noise/scale/resource/conversion diagnostics.

5. **Composite index** (optional, not used for cross-domain ranking):
   [
   \text{GEC} = \text{GEC}*0 \cdot \lambda*{\text{geom}}(\vec{\kappa})
   ]
   where (\lambda_{\text{geom}}) is the weighted geometric mean of CSK factors.

---

## 4. How to reproduce figures (v2.0)

All figure scripts write into `core/figures/`. Ensure that directory exists:

```bash
mkdir -p core/figures
```

Then:

### 4.1 CSK radar (ML vs Thermodynamics) — supports CSK section

```bash
python core/scripts/fig_csk_radar.py
```

Outputs:

* `core/figures/fig_csk_radar.png`

Check: the ML and Thermodynamics spokes match Figure “CSK Diagnostics: ML vs Thermodynamics” in the paper.

---

### 4.2 GEC₀ across domains (communications, thermo, ML, finance, governance) — Table 3 / bar plot

```bash
python core/scripts/gec_results_bar.py
```

Outputs:

* `core/figures/gec_results_real.png`

Check: bar heights `0.87, 0.81, 0.95, 0.44, 0.88` match the manuscript’s GEC₀ values.

---

### 4.3 Metallic convergence curves — “Convergence to metallic means”

```bash
python core/scripts/metallic_convergence.py
```

Outputs:

* `core/figures/metallic_convergence.png`

Check: the curves for k = 1,2,3,4 converge to the correct metallic means with matching legend values.

---

### 4.4 Convergence rate to φ — error decay plot

```bash
python core/scripts/convergence_rate.py
```

Outputs:

* `core/figures/convergence_rate.png`

Check: the semilog error curve decays quickly and hits < 1e-15 within ≤ 15 steps, as described in the metallic section.

---

### 4.5 Aggregator fixed-point CIs — Fig. 1 (metallic means)

```bash
python core/scripts/fig1_aggregator_means_ci.py
```

Outputs:

* `core/figures/fig1_aggregator_means_ci.png`
* `core/figures/fig1_aggregator_means_ci.pdf`

Check: points and error bars for `Multiplicative`, `Fibonacci-like`, `Cobb–Douglas`, `LSE` sit tightly around φ with the same CI widths as in the paper, and the φ reference line matches 1.6180339887…

---

## 5. Metallic map demos (φ-DL / Table 5 style)

These use the synthetic CSVs in `phi_demo/`.

### 5.1 Proof harness (metallic vs null maps)

```bash
python phi_demo/phi_proof_harness.py phi_demo/demo_symmetric.csv
```

Outputs:

* JSON report to stdout with:

  * `raw_gec0` summary,
  * metallic and null model fits (`k`, `beta`, `t_star`, AIC, BIC, CV-MSE),
  * bootstrap CIs on `k`, `beta`, `t_star`,
  * permutation test results,
  * pairing variants.

Repeat with:

```bash
python phi_demo/phi_proof_harness.py phi_demo/demo_asymmetric.csv
python phi_demo/phi_proof_harness.py phi_demo/demo_null.csv
```

Use these to qualitatively reproduce the “metallic vs non-metallic” behavior discussed in the text.

---

### 5.2 Aggregator runner (Table 5 / metallic fixed-point CIs)

```bash
python phi_demo/phi_aggregator_runner.py phi_demo/demo_symmetric.csv 800
python phi_demo/phi_aggregator_runner.py phi_demo/demo_asymmetric.csv 800
python phi_demo/phi_aggregator_runner.py phi_demo/demo_null.csv 800
```

Each call prints JSON with:

* `k`, `beta`, `fixed_point`
* bootstrap CIs for all three

These values feed into the robustness/aggregator table in the manuscript.

---

## 6. Notebooks (case studies and DEA)

### 6.1 Case studies — Table 3 numbers

Notebook:

* `core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb`

Run interactively in Jupyter:

```bash
jupyter notebook core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb
```

Or headless:

```bash
jupyter nbconvert --to notebook --execute \
  core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb \
  --output Compression_Physics_GEC_CaseStudies_executed.ipynb
```

Check:

* The resulting GEC₀ values for Communications, Thermodynamics, ML, Finance, Governance match Table 3 and the bar plot.

---

### 6.2 DEA / finance sensitivity — Table 6

Notebook:

* `core/notebooks/GEC_Toolkit_Pro.ipynb`
  (or `GEC_Compression_Physics_Toolkit.ipynb`, depending on final organization)

Run as above, then verify:

* The DEA-based C_max and GEC₀ values match the “DEA sensitivity” table in the Appendix.

---

## 7. Metallic validator (real data)

`validator/gec_metallic_validator.py` provides a higher-level CLI for applying the metallic-mean tests to your own datasets.

Basic usage:

```bash
python validator/gec_metallic_validator.py \
  --input validator/_DL___Real-Data_Validator__Template_Demo_.csv \
  --output validator/real_data_validator_output.json
```

Outputs a JSON summary including:

* metallic vs null model fits,
* bootstrap CIs,
* ΦDL-style classification (nearest metallic mean).

This validator is not required to reproduce the specific numbers in the paper,
but it shows how the ΦDL layer can be applied to arbitrary real datasets.

---

## 8. Notes

* **Primary index**: When in doubt, compare systems using GEC₀ only.
  The composite GEC (GEC₀ × λ_geom) is for diagnostics or ablation studies, not for cross-domain ranking.

* **Frontier updates**: If a better C_max is discovered later, use the frontier audit / renormalization procedure described in the paper; the scripts are written to make that step explicit rather than hidden.

* **Versioning**:
  This repo is the reproducibility companion for **v2.0**.
  If you also include the v1 PDF, you may add a short note here describing which scripts/notebooks correspond to v1 vs v2.

```

---

If you drop that into `core/Reproducibility.md` and add the `requirements.txt` next to it, you’re basically “submission ready” on the reproducibility side: Zenodo + GitHub link + this doc = a very clean story.
::contentReference[oaicite:1]{index=1}
```
