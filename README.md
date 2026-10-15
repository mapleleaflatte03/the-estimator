# PARALLAX AI — The Estimator

Working Python foundation for the Anduin Cybernetics **The Estimator** challenge.

Evidence-backed scope extraction, Monte Carlo estimation, and a calibration loop grounded in a **real, public effort dataset** (no seeded or invented historical projects).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest -q                                   # tests use an isolated temp store
uvicorn parallax.main:app --port 8000       # API (store: data/parallax_store.json or $PARALLAX_DATA_PATH)
cd apps/web && npm install && npm run dev   # UI on :3000 (proxy target: $PARALLAX_API_URL, default :8000)
```

## Deploy (single service)

`Dockerfile` builds the web UI and serves it from the FastAPI app (same origin, no proxy needed).
On Render: **New → Blueprint →** select this repo (uses `render.yaml`), or open
`https://render.com/deploy?repo=https://github.com/mapleleaflatte03/the-estimator`.
The free plan has no persistent disk: projects entered on the live site reset when the service restarts.

## Real data: SiP effort estimation dataset

`datasets/sip/` contains the unmodified files of the [SiP dataset](https://github.com/Derek-Jones/SiP_dataset)
(Software in Partnership Ltd, 2004–2014, commit `fed32c6`; Jones & Cullum, [arXiv:1901.01621](https://arxiv.org/abs/1901.01621)).
License: **CC BY-NC-ND 4.0** (non-commercial; redistributed unmodified; all derived statistics are computed at runtime).
`python scripts/fetch_datasets.py --verify-only` checks the SHA-256 of the files.

After de-duplication and joining estimate dates: **10,022 completed tasks** with the hours estimated before work and the hours actually spent.

How it is used (`apps/api/parallax/empirical.py`):

| Use | Method |
| --- | --- |
| Benchmark | Temporal holdout: fit on tasks estimated before 2011-01-01 (7,774), test on 2011–2014 (2,248). Forecast = estimate × quantiles of historical actual/estimate ratios in the same size bucket. Baseline = the human estimate as-is. |
| "More accurate over time" | Rolling origin per year: a model frozen after 2005 vs. a model refitted on all prior history. |
| Uncertainty in the app | Feature-level actual/estimate ratios of 56 Development work packages (≥ 40h, ≥ 5 tasks), centered on median 1.0, bootstrapped as the shared shock in the Monte Carlo (replaces the assumed lognormal CV). |

Measured results (reproducible via `POST /api/v1/benchmark/run`):

| Holdout 2011–2014 (n = 2,248) | Human estimate | Calibrated |
| --- | --- | --- |
| MAE | 10.34 h | **9.26 h** (−10.4%) |
| MdAPE | 33.3% | 33.3% |
| PRED(25) | 44.9% | 45.4% |
| P10–P90 coverage | n/a | **82.0%** (target 80%) |

- The gain is concentrated in large estimates (≥ 50h: MAE 90.6 → 73.3 h); small tasks are unchanged.
- The rolling model has lower MAE than the frozen one in 8/9 test years (2006–2014).
- At the feature/work-package level the holdout has only 7 cases and results are **mixed** (MAE worse, MdAPE/PRED(25) better, coverage 29%). No claim is made at that level.

## Learning from your own actuals

`POST /projects/{id}/actuals` compares against the current committed version (and reports v1 too), then updates the
workspace bias multiplier: `exp(Σ log(actual / uncalibrated P50) / (n + 3))`, bounded to [0.5, 2.0]. It is persisted,
applied to new estimates/re-estimates (old versions stay immutable), and checked with leave-one-out in the benchmark.
The reference class (`/historical-cases`) contains only projects in this workspace with recorded actuals; ≥ 5 of the
same type are required before a reference-class P50 is shown.

## Scope extraction

The extractor segments any brief (Vietnamese or English, with or without diacritics) into numbered items/sentences;
each becomes a requirement whose evidence is the exact clause (verified against the source). Clauses are classified
against a component taxonomy (auth, scheduling, offline, notifications, import, integrations per named system, AI/RAG,
…); unrecognised requirements are kept with a generic, wide template and flagged for review. Tentative wording
("có thể cần", "cần xem xét", "TBD", …) produces scope questions; missing platform/data-quality/API-docs information
produces add-on questions. Answers accumulate across versions.

## Methodological limitations

1. Per-component hour templates are **engine priors (assumptions)**, not fitted to data. Only the workspace's own actuals can validate them.
2. SiP is one UK company's maintenance/enhancement work (2004–2014); its error distribution may not transfer to other teams or greenfield projects.
3. Feature-level ratios have a long right tail (two packages overran 6–14×); P99 of the forecast is therefore very wide. This is shown, not hidden.
4. Clause classification is rule-based; it catches omissions structurally (every clause is kept) but can mislabel a component.
5. Old test runs wrote fake projects into `data/parallax_store.json`. `python scripts/clean_test_artifacts.py` lists them; `--apply` removes them with a backup.

## Next steps (priority order)

1. Add source document ingestion, request IDs and version persistence to the API.
2. Expand the hand-labeled golden brief suite with strict attribution and tests.
3. Implement a reference-class retrieval method with scoped features; keep its estimate separate until blend weight is tuned on training/validation data.
4. Expand benchmark coverage with additional datasets, provenance, license checks, unit checks and leakage-safe time splits.
5. Deploy the five-screen frontend and submit the live URL with this public GitHub repo.
