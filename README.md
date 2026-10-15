# PARALLAX AI — Day 0 Technical Foundation

Working Python foundation for the Anduin Cybernetics **The Estimator** challenge.

This is **not** a complete submission: no frontend, no PDF parsing, no LLM integration, no deployed app, and no validated external datasets are included yet. It is a tested, extensible baseline.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # CachyOS / Linux
pip install -e '.[dev]'
pytest -q
python scripts/demo_foundation.py
```

## What works

- Pydantic contracts for traceable requirements and task-level 3-point estimates
- Original-source substring checks for quoted evidence, plus DAG scope consistency checks
- Seeded beta-PERT Monte Carlo and shared lognormal systemic risk for positively correlated tasks
- P10/P50/P80/P90, a source-compatible reference-class median for cross-checking (NOT arbitrary blending)
- MAE, MdAPE, WAPE, PRED(25), interval coverage and width benchmark metrics
- Toy training-only multiplicative calibration proposal + validation-only promotion gate
- Automated unit tests and GitHub Actions configuration

## Important methodological limitations

1. P10-P90 is a *model-derived* interval, **not** an empirically calibrated 80% prediction interval until verified on new cases.
2. The shared systemic risk and three-point task distributions are assumptions and can be wrong.
3. Source text substring presence is necessary but not sufficient to prove that an interpretation is correct.
4. The caller must select genuinely comparable historical projects; mere task-hour medians can be misleading.
5. The calibration example in tests uses a toy distribution and proves the code path, not model accuracy.
6. Selecting calibration repeatedly on one validation set leaks information. Use an untouched final test split only once.
7. No claim of real-world error improvement can be made until real, suitable datasets and baselines are evaluated.
8. A single release must specify dataset version, split strategy, model configuration and random seed to be reproducible.

## Next steps (priority order)

1. Create public repo under the *authorized* `mapleleaflatte03` identity and commit this foundation.
2. Add a FastAPI app with `POST /projects/estimate`, source document ingestion, request IDs and version persistence.
3. Build a hand-labeled golden brief suite with strict attribution and tests.
4. Implement a reference-class retrieval method with scoped features; keep its estimate separate until blend weight is tuned on training/validation data.
5. Load one authentic benchmark dataset with provenance, licenses, unit checks and a leakage-safe time split when timestamps are available.
6. Connect the five-screen frontend, deploy and submit live URL + public GitHub repo.
