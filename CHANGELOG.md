# Changelog
All notable changes to this project will be documented in this file.

The format follows [Semantic Versioning](https://semver.org/) and academic reproducibility best practices.

---

## [2.0.0] – 2025-12-01
### Added
- Full reproducibility scripts for *Compression Physics v2*.
- Complete **phi_demo/** suite:
  - `phi_proof_harness.py`
  - `phi_aggregator_runner.py`
  - Symmetric, asymmetric, and null demo datasets.
- Real-data validator templates:
  - `gec_metallic_validator.py`
  - `real_data_template.csv`
- Jupyter notebooks:
  - `Compression_Physics_v2.ipynb`
  - Updated `GEC_Primer.ipynb`
- Full figure-regeneration pipeline under `core/plotting`.
- Bootstrap, metallic model, and null model estimators for GEC.
- Reorganized repository structure for clarity and reproducibility.
- New README with installation, structure, and reproducibility guidelines.
- `CITATION.cff` added for GitHub-native citation support.

### Changed
- Updated efficiency models and fixed-point estimators.
- Improved frontier normalization and pairing variants.
- Cleaner paths for all figure outputs (now in `figures/`).
- Improved bootstrap confidence interval computation.
- Updated fitting logic for metallic-mean models.
- Consistent naming conventions across scripts.

### Removed
- Deprecated scripts from v1 that are now replaced by version 2 pipelines.
- Old Plotly-based figures (all replaced with Matplotlib for reproducibility).
- Legacy directory scaffolding.

---

## [1.0.0] – 2025-10-27
### Added
- Initial definition of the **Generalized Efficiency Coefficient (GEC)**.
- Baseline fixed-point estimator and frontier normalization logic.
- First reproducibility pipeline and supporting datasets.
- Published as Zenodo v1  
  DOI: **10.5281/zenodo.17457378**
