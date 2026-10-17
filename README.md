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

### Use it yourself: bring your own AI keys

The AI reader (Jev) is **required**: every clause of a new brief is read by Jev before an estimate is produced.
The sample briefs ship with cached answers, so they work without a key. For new briefs, put **your own** keys in a
git-ignored `.env` at the repo root (never commit it). The API loads it at startup; real environment variables win.

```bash
git clone https://github.com/mapleleaflatte03/the-estimator && cd the-estimator
cp .env.example .env    # JEVSTATION_API_KEY, JEVSTATION_API_KEY_2, ... (any number) or TYPESAFE_API_KEY
uvicorn parallax.main:app --app-dir apps/api --port 8000
```

Several keys form a **pool**: questions are packed 5 per call (JevStation bills 1 credit for up to 5 questions and
3 credits for 6–10), calls run in parallel, an empty key (HTTP 402, not charged) is skipped and the call retried on
the next key. If a charged call ever returns no usable answer, the reader halts instead of spending further. Each
person pays for their own usage under the provider's terms. `JEV_REQUIRED=0` turns the requirement off (tests only).

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

## AI reader (Jev): required, measured on real outcomes

Scoping a brief is a chain of small judgements a senior estimator makes per clause: *what kind of work is this?*,
*has the client committed to it?* and *will this take longer than it looks?*. All three go to
[Jev](https://docs.typesafe.ai) (TypeSafe's System One decision model: typed answers with calibrated probabilities,
no generated text). Hours, simulation and learning stay in code.

### "Will this take longer than it looks?" — validated on 798 real tasks

`scripts/sip_jev_study.py` asks Jev about the text of real SiP development tasks (estimate ≥ 20 h, where most of the
error lives) and compares with the hours actually spent. Only task ids and Jev's probabilities are stored
(`datasets/eval/sip_jev_readings.json`); the SiP text is never copied.

1. **Pilot on training years only** (75 tasks before 2011): four candidate questions. `new_build` and `overrun` tied
   on Spearman (0.302 vs 0.297); `overrun` was chosen for its higher AUC (0.678 vs 0.595) and because nearly every
   clause of a greenfield brief is "new build". Both the default pick and the override are in the journal.
2. **Thresholds from training years** (579 tasks): three groups by Jev's probability.
3. **One run on 2011–2014** (219 unseen tasks):

| Jev's reading | Training: actual / estimate (median) | Unseen years: actual / estimate (median) |
| --- | --- | --- |
| Low risk | 0.59 | 0.65 |
| Medium | 0.66 (×1.11) | 0.69 (×1.07) |
| **Takes longer than it looks** | 0.78 (**×1.32**) | 0.95 (**×1.47**) |

Spearman 0.20 and AUC 0.62 on the unseen tasks: the ordering holds. Using the groups as a point forecast did **not**
significantly change MAE (52.1 → 52.7 h; 95% CI of the gain −1.9 to +0.7 h), while PRED(25) rose 16.4% → 19.6%.
In the app, the *same question* is asked of every brief clause; clauses Jev rates medium/high get ×1.11 / ×1.32
hours (the training ratios), shown on the work list with the reason.

### Learning from your own projects

When a finished project's hours are entered per requirement (optional, in "Giờ thực tế"), each requirement is an
observation (unadjusted estimate vs actual). The risk-group factors and a factor per kind of work (reporting,
integration, …) are pulled from the SiP prior towards the workspace's own record with partial pooling (4
pseudo-observations, bounds 0.5–2.0), so a few projects nudge them and many take over. User-edited hours always win.

### Reading accuracy

- Questions are in English, clauses stay in their original language (independent tests found this keeps accuracy).
- Rules + Jev are combined conservatively: Jev's kind is used when the rules recognise nothing; when Jev sees a
  kind the rules missed, the app **asks the user** instead of silently adding hours; a clause is tentative if
  either reader says so (Jev threshold 0.7).
- Answers are cached per (question version, clause) (`datasets/jev_cache/` ships them for the sample briefs), so
  re-estimates and clarifications cost nothing and stay consistent, and a new question only costs the new question.
  If Jev cannot read every clause (no key, credits exhausted, hourly cap), the API answers 503 with the reason
  instead of a weaker estimate. JevStation is an independent reseller: brief text passes through it.

Held-out check (`datasets/eval/clause_labels_v1.json`: 31 new clauses, hand-labelled before any model ran;
results in `datasets/eval/reader_results_v1_heldout.json`, reproduce with `scripts/evaluate_readers.py`):

| Reader | Primary kind found | Tentative clauses caught | False "tentative" |
| --- | --- | --- | --- |
| Rules only | 23/31 | 2/6 | 0 |
| Jev only (jev-1.13.0) | 23/31 | 6/6 | 0 |
| **Rules + Jev, as shipped** | **24/31** (+4 offered as questions) | **6/6** | 0 |

Round 2 (30 new Vietnamese clauses, varied domains/styles, `clause_labels_v2.json`): rules 23/30 kinds and
1/5 tentative; shipped rules+Jev 24/30 (+1 via a question) and **5/5** tentative, no false alarms. Across both
rounds the rules alone caught 3/11 uncommitted requirements; with Jev **11/11**.

Round 4, the final end-to-end test (16 new clauses, labels committed in `6169d92` before the run; the last
credits covered 14 of them): rules 13/14 kinds and 2/4 tentative; **shipped 14/14 and 4/4**, no false alarms.
Over rounds 1, 2 and 4 the shipped reader caught **15/15** uncommitted requirements (rules alone 5/15).
Fixes derived from round 4 are reported as dev only.

Round 5 (24 new clauses from two new sample briefs, Vietnamese and English; labels committed in their own commit
before any reader ran): rules 21/24 kinds and **1/6** tentative; Jev alone 6/6 tentative; shipped 21/24 (+2 as
questions) and **5/6**, no false alarms. Over rounds 1, 2, 4 and 5: shipped **20/21** uncommitted requirements
caught vs **6/21** with rules alone, and 83/99 primary kinds vs 80/99. Full story, including a cache incident and its fix:
[`docs/EVALUATION_LOG.md`](docs/EVALUATION_LOG.md) (run table regenerated by `scripts/journal_report.py`).

Rule improvements are always measured on data not used to derive them:

| Check (held-out part) | Before | After |
| --- | --- | --- |
| Round 3, 25 Vietnamese clauses written before the fixes: primary kind | 17/25 | **23/25** |
| Round 3: tentative caught | 3/4 | **4/4** |
| PROMISE_exp odd-numbered projects (392 real English requirements): kept as requirements | 72.7% | **100%** |
| PROMISE_exp odd projects: performance requirements recognised | 3.2% | **51.6%** (3/361 false alarms) |
| PROMISE_exp odd projects: security requirements recognised | 54.7% | **77.4%** |

Every run is appended to `datasets/eval/journal.jsonl` (date, data, rule fingerprint, model, results, note) and
shown in the app's **Kiểm chứng** tab. In the app, answers to AI suggestions and removals of AI-added work are
recorded; a suggestion kind answered ≥ 3 times with < 30% acceptance is muted automatically.

The set exposed two rule bugs (Vietnamese "ai" = *who* read as AI; "số điện thoại" read as a mobile app),
fixed afterwards — so later runs on this set are no longer strictly held-out (`reader_results_latest.json`).
A free open model (Laya) was also tried on 12 clauses and rejected (7/12 kinds, missed both tentative clauses).

## Other features

- **Edit the work list**: change hours or names, remove or add items; edits persist across later versions
  (clarifications and re-estimates) and QA hours follow the new total.
- **Deliverables**: plain-language proposal (Markdown) at the chosen confidence, rate and team size, and an
  Excel-ready CSV of the work list (`/export/proposal.md`, `/export/wbs.csv`).
- **Timeline** respects the critical path: adding people cannot beat the longest chain of dependent work.
- **Learning per project type**: the bias multiplier is learned per type and partially pooled towards the
  workspace-wide one, so a few completed projects of one type shift that type without swinging the others.
- Brief upload from `.txt`, `.md` or `.csv`.

## Methodological limitations

1. Per-component hour templates are **engine priors (assumptions)**, not fitted to data. Per-requirement actuals now adjust them per kind of work, but only the workspace's own outcomes can validate them.
2. The overrun-risk factors come from SiP maintenance tasks; whether they transfer to greenfield brief clauses is assumed, and is what per-requirement actuals correct over time.
3. SiP is one UK company's maintenance/enhancement work (2004–2014); its error distribution may not transfer to other teams or greenfield projects.
4. Feature-level ratios have a long right tail (two packages overran 6–14×); P99 of the forecast is therefore very wide. This is shown, not hidden.
5. Clause classification (rules + Jev) can mislabel a component; every clause is still kept, so nothing is silently dropped. The labelled clause sets total 126 clauses written by the developer — small.
6. Old test runs wrote fake projects into `data/parallax_store.json`. `python scripts/clean_test_artifacts.py` lists them; `--apply` removes them with a backup.

## Next steps (priority order)

1. Add source document ingestion, request IDs and version persistence to the API.
2. Expand the hand-labeled golden brief suite with strict attribution and tests.
3. Implement a reference-class retrieval method with scoped features; keep its estimate separate until blend weight is tuned on training/validation data.
4. Expand benchmark coverage with additional datasets, provenance, license checks, unit checks and leakage-safe time splits.
5. Deploy the five-screen frontend and submit the live URL with this public GitHub repo.
