# GEC φ Aggregator Demo

Files generated:
- demo_symmetric.csv
- demo_asymmetric.csv
- demo_null.csv
- phi_aggregator_runner.py

## Quick start
python phi_aggregator_runner.py demo_symmetric.csv 800
python phi_aggregator_runner.py demo_asymmetric.csv 800
python phi_aggregator_runner.py demo_null.csv 800

Each prints JSON with k, beta, and implied fixed point.

Interpretation:
- k≈1 & beta≈1 ⇒ symmetric metallic map (fixed point near φ=1.618)
- beta≈1 but k>1 ⇒ asymmetric metallic mean
- poor fit / wide CIs ⇒ likely no metallic map (compare nulls)
