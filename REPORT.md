# Repository Report

## Commands Executed

```
ls
ls core
ls validator
ls 'phi demo'
ls core/scripts
ls core/notebooks
```

## Repository Overview
- Root contents: `GECv2.pdf`, `core/`, `phi demo/`, and `validator/`.
- Core documentation: `core/Reproducibility.md` outlines the steps for computing the GEC index and optional composite metric.
- Notebooks: `core/notebooks` includes case studies and toolkit notebooks.
- Scripts: `core/scripts` contains figure and table generation utilities plus a `frontier_registry.json` reference.

## Key Modules and Usage
- **Reproducibility guide** (`core/Reproducibility.md`): describes computing raw efficiency (`eta = Y/T`), choosing frontier caps, deriving `GEC_0`, optional composite `GEC`, and points to the case study notebook.
- **Metallic-mean validator** (`validator/gec_metallic_validator.py`): CLI and library helper that builds odds-transformed efficiency pairs, fits metallic and null maps with bootstrapping, emits JSON/CSV diagnostics, and guards against inconsistent frontiers.
- **Phi aggregator demo** (`phi demo/README.txt` and `phi demo/phi_aggregator_runner.py`): sample CSVs plus runner that pairs rows, estimates metallic map parameters via least squares with bootstrap CIs, and reports implied fixed points.

## Data Assets
- Validator templates: `_DL___Real-Data_Validator__Template_Demo_.csv` and `gec_example_rows.csv`.
- Phi demo datasets: `demo_symmetric.csv`, `demo_asymmetric.csv`, and `demo_null.csv` illustrate different metallic behaviors.

## Notebook Pointers
- `core/notebooks/Compression_Physics_GEC_CaseStudies.ipynb`
- `core/notebooks/GEC_Compression_Physics_Toolkit.ipynb`
- `core/notebooks/GEC_Toolkit_Pro.ipynb`
