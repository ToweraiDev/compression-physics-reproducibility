

```markdown
# Compression Physics: Generalized Efficiency Coefficient (GEC)
**A Domain-Normalized Efficiency Framework for Physics, Engineering, and Information Systems**  
**Author:** Mycal Brooks  
**Version:** 2.0.0

[![DOI v2](https://zenodo.org/badge/DOI/10.5281/zenodo.17785197.svg)](https://doi.org/10.5281/zenodo.17785197)
[![DOI v1](https://zenodo.org/badge/DOI/10.5281/zenodo.17457378.svg)](https://doi.org/10.5281/zenodo.17457378)

---

## Overview
This repository contains the **full reproducibility package** for:

**_Compression Physics: A Domain-Normalized Efficiency Index (Generalized Efficiency Coefficient, GEC)._**  
Version 2 extends the original 2025 release by providing:

- A fully standardized **proof harness**
- Metallic-mean asymptotic model fits
- Bootstrap confidence intervals
- Aggregator-based fixed-point estimation
- Reproducible figure generation pipelines
- Validator templates for real-world datasets
- Jupyter-based exploration of compression-physics invariants

This repository includes **all code, scripts, and datasets required to regenerate Tables, Figures, and Results** from the v2 paper.

---

## Repository Structure

```

compression-physics-reproducibility/
│
├── core/
│   ├── scripts/                # Reproducibility scripts
│   │   ├── aggregator_fixed_point.py
│   │   ├── bootstrap_metallic.py
│   │   ├── metallic_model.py
│   │   ├── null_models.py
│   │   ├── phi_frontier_tools.py
│   │   └── ...
│   │
│   ├── plotting/               # Figure generation
│   │   ├── fig_fixed_point.py
│   │   ├── fig_bootstrap.py
│   │   └── ...
│   │
│   └── data/                   # Demo datasets
│       ├── demo_symmetric.csv
│       ├── demo_asymmetric.csv
│       └── demo_null.csv
│
├── phi_demo/                   # Standalone demonstration harnesses
│   ├── phi_proof_harness.py
│   ├── phi_aggregator_runner.py
│   └── demo_*.csv
│
├── validator/                  # Real-data validator templates
│   ├── gec_metallic_validator.py
│   ├── gec_example_rows.csv
│   └── real_data_template.csv
│
├── notebooks/                  # Jupyter notebooks for exploration
│   ├── GEC_Primer.ipynb
│   └── Compression_Physics_v2.ipynb
│
├── figures/                    # Auto-generated figure outputs
│
├── requirements.txt
└── README.md

````

---

## Installation

### 1. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Enable Jupyter

```bash
pip install notebook jupyter
```

---

## Requirements

Minimal reproducibility dependencies:

```
numpy
pandas
matplotlib
scipy
tqdm
seaborn
python-dateutil
notebook
jupyter
```

All scripts run under **Python 3.10+**.

---

# Running the Reproducibility Scripts

## 1. Proof Harness (Model Fits + Statistics)

The proof harness reproduces:

* Metallic-mean asymptotic fits
* Null-model comparison
* AIC/BIC
* Bootstrap ranges
* Pairing-variant sensitivity

**Run:**

```bash
python phi_demo/phi_proof_harness.py phi_demo/demo_symmetric.csv
```

**Output example (truncated):**

```json
{
  "n_rows": 60,
  "n_pairs": 30,
  "used_Cmax": 1.0,
  "fits": {
      "metallic": {...},
      "null_const": {...},
      "null_slope": {...}
  },
  "bootstrap": {...}
}
```

---

## 2. Aggregator-Based Fixed-Point Estimation

Reproduces Fig. 5 / Table 5.

```bash
python phi_demo/phi_aggregator_runner.py phi_demo/demo_asymmetric.csv 800
```

Produces:

* k, β, and fixed-point estimates
* 95% bootstrap CI
* Aggregator-specific fixed points

---

## 3. Generating Figures

Figure scripts write to `./figures/`.

Example:

```bash
python core/plotting/fig_fixed_point.py
python core/plotting/fig_bootstrap.py
```

All figure generation paths have been normalized for cross-platform reproduction.

---

# Real-Data Validator (Optional)

Researchers applying GEC to real-world systems can use:

```
validator/gec_metallic_validator.py
validator/gec_example_rows.csv
validator/real_data_template.csv
```

This supports:

* Cmax selection
* Frontier normalization
* Metallic asymptotic fit
* Null-model comparison
* AIC/BIC export
* Jittered frontiers
* Sensitivity analysis

---

# Reproducibility Notes

* All random processes (bootstrap, permutation tests) use fixed seeds unless intentionally omitted.
* All CSV demo datasets are included exactly as used in the paper.
* Scripts are deterministic and generate identical outputs to the published version.
* Figures regenerate pixel-perfect reproductions of the manuscript versions.

---

# Citing This Work

### **Latest Version (v2)**

```
Brooks, M. (2025). Compression Physics: A Domain-Normalized Efficiency Index  
(Generalized Efficiency Coefficient, GEC) (Version 2). Zenodo.  
https://doi.org/10.5281/zenodo.17785197
```

### **Original Version (v1)**

```
Brooks, M. (2025). Compression Physics: A Domain-Normalized Efficiency Index  
(Generalized Efficiency Coefficient, GEC) (Version 1). Zenodo.  
https://doi.org/10.5281/zenodo.17457378
```

---

# Version History

### **v2.0.0 — December 2025**

* Expanded metallic-mean analysis
* Full proof harness with sensitivity variants
* Aggregator fixed-point estimation
* Bootstrap confidence intervals
* Real-data validator package
* Standardized plotting pipeline
* Reproducibility scripts reorganized and simplified

### **v1.0.0 — October 2025**

* Initial definition of the Generalized Efficiency Coefficient (GEC)
* Core equations and theoretical framework

---

# License

This work is released under **Creative Commons Attribution 4.0 International (CC-BY 4.0)**.
You are free to use, modify, and distribute with attribution.

---

# Contact

For questions, implementations, or collaborations:
**Mycal Brooks**
mycalbrooks@projecttower.org
---

```

---

