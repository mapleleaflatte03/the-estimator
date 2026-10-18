# Product and prize-readiness review — 18 October 2026

## Verdict

PARALLAX is a working **draft scoping assistant for software and AI automation delivery**. It is not yet a validated autonomous quoting system. It reads a brief, traces each proposed work item to the client's words, exposes uncommitted scope, asks consequential questions, and records outcomes. A delivery lead can use it to prepare and review an estimate; the time saved has not been measured against a human workflow. A team should not commit its price or deadline from this output without checking the work breakdown and its own historical hours.

The [challenge](https://cybernetics.anduin.tech/agent-in-the-shell) asks for faster, more consistent scoping and improvement against actual work. The prototype implements that loop. Its strongest proof is of **reading and correcting existing estimates**, not of the final quote on unseen client projects. That distinction matters for both real adoption and the judging rubric (depth 30%, architecture 20%, product quality 20%, complexity 15%, AI use 15%).

## Evidence and limits

| Question | Evidence now | What remains unproven |
| --- | --- | --- |
| Does it catch uncommitted work? | 30/31 tentative clauses caught across developer-written held-out sets; rules alone caught 14/31. Exact source quotes and answer-driven versions work in the app. | The clauses were written and labelled by the builder. Accuracy on real client emails, PDFs and mixed documents is unknown. One missed clause can still cause a bad quote. |
| Are the hours right? | Templates are explicit, editable, and simulated. SiP calibration reduced error from 10.34 to 9.26 hours on 2,248 later tasks **given an existing human estimate**. | No complete historical brief-to-actual test of the generated WBS or its hour templates. The quoted 80% range is a model interval, not measured coverage for new client projects. |
| Does it get better over time? | Finished projects change future project-type and work-kind factors. Versions and original estimates are preserved. SiP's operational replay beats human estimates (SA 56.3% to 61.1%). | In that same replay, updating online had MAE 3.85 hours versus 3.82 for a frozen calibrated model. No pilot has shown better *end-to-end* quotes after several team projects. |
| Can a real team use it? | A browser can complete brief → questions with source notes → draft estimate → work edits → actuals. CSV and Markdown export work. Browser copies allow multiple visited projects to be re-read after a restart. | Free Render storage disappears on restart; recovery re-estimates and can differ from the original version. Browser storage is not a durable archive. There are no accounts, shared team review, durable history, timesheet import, or PDF/DOCX intake. This is a demo, not a production system for confidential client work. |

## Audit of the data already in this folder

| Local source | What it can test | Missing for a complete quote test |
| --- | --- | --- |
| `datasets/sip/` | Real task summaries, pre-work hour estimates, actual hours and dates; 12,299 raw task rows, 10,022 used after filtering. | These are individual task titles, not the original client brief for a whole delivery. |
| `datasets/external/itemlet/` | Jira issue titles, logged hours and an original estimate derivable from `workratio`; independent check of task-level risk. | No issue descriptions or full client briefs. |
| `datasets/external/deepse/` | Issue title/description and story points; text-to-story-point comparison. | No actual hours in its CSVs. |
| `datasets/external/PROMISE_exp.csv` | 969 real requirements for retention/classification checks. | No original quote and actual hours. |
| `datasets/golden_briefs/` | Nine end-to-end example inputs and expected scope properties. | Builder-written examples; no delivered-project actuals. |
| Local-only, Git-ignored `data/parallax_store.backup-20261016-010941.json` | Four saved actuals records for exercising the learning UI. | All four are duplicate “Corporate Project Management Portal” demo entries at exactly 175 hours with identical notes, not four independent real outcomes. This file is not part of the public repo or its reproducible evaluation. |

None of these sources contains a complete real client brief plus a quote made before delivery plus the final total. We should not turn task-level accuracy or synthetic examples into an end-to-end accuracy claim.

## Is Jev the right AI?

[TypeSafe describes Jev](https://docs.typesafe.ai/introduction) as a general model for fast, typed decisions, with `Choice`, `Score` and `Noul` answers. It was **not designed specifically for effort estimation** and the challenge does not require it. It fits narrow judgments here: classify a clause, assess whether the client has committed, and check if keyword rules overmatched. It does not invent the detailed work breakdown or the missing-information questions; those come from templates in `extractor.py`. The application should keep arithmetic, pricing and versioning in ordinary code. Typed output guarantees a valid answer shape; it does not guarantee a correct business interpretation. [TypeSafe itself recommends](https://docs.typesafe.ai/introduction) decomposing complex reasoning into small questions. The measured Jev overrun signal did **not** improve hour MAE, so it is only a review flag.

There is a product tradeoff: requiring Jev on every new clause prevents silent degradation, but provider failure, exhausted credits or rate limits can stop the main flow. Cached samples still work. The live key pool must remain funded through judging. For real confidential briefs, the team's data-processing agreement and provider path need review; the demo's reseller path is not enough.

I reran the stored-data checks on this revision without paid model calls: `python scripts/sip_operational_replay.py --no-journal` gave 1,391 time-ordered tasks with MAE 4.33 hours for human estimates, 3.82 for a frozen calibrated model, and 3.85 for online updates. After installing the optional `.[eval]` dependencies, `python scripts/itemlet_jev_replication.py report --no-journal` gave 2,032 issues from 37 projects: Jev's overrun signal had AUC 0.535, and adding SiP-derived risk factors worsened MAE from 18.35 to 19.54 hours. That is why the production estimate uses Jev's risk result only as a review flag.

## Other risks that affect judging

1. **Domain fit.** The official prompt says “incoming work”; PARALLAX's templates, roles and prior data are for software delivery. It should be presented as a deliberate software-delivery slice of that problem, not as a universal estimator for legal, operations or fund-administration tasks.
2. **Evidence can be overstated.** SiP covers corrections to someone else's estimate at task level. A reader could mistake those numbers for proof that the app's client quotes are accurate. The app and export now call them drafts and distinguish modelled intervals from measured coverage.
3. **Feedback quality.** One mistaken or duplicated actual entry can bias later quotes. Completed estimates are now frozen; corrections replace a project's calibration contribution and per-requirement breakdown. Actual breakdowns cannot exceed the project total. Outcome and calibration are committed in one storage write; failed writes return an error and roll back memory.
4. **Demo reliability.** Cold starts, ephemeral data and a required external AI service create more failure points than the code test suite captures. A real new brief and exported proposal should be checked after every deploy.
5. **Winning cannot be promised.** Engineering and AI evidence are strong relative to a simple prompt wrapper. Product quality and depth are limited until we show unseen complete client projects, a credible baseline and a dependable live workflow. Competitor quality and judges' priorities are unknown.

## Highest-value next proof

Obtain 3–10 **completed software projects** with the original intake brief, the estimate recorded *before* delivery and actual hours. Remove names and secrets. Freeze the current code; run the briefs without editing the rules or templates, record omitted/misclassified scope, WBS edit time, MAE and interval coverage, and compare with the original human estimate. Report every case, including failures. This would test the exact business loop the challenge asks for. If those records are unavailable, demonstrate the workflow honestly and avoid claiming end-to-end accuracy or a proven win.

## Final release checks

- Local: 104 backend tests pass; frontend lint and production build pass. CI runs both backend tests and frontend lint/build on every push.
- Live release `readiness-review-2026-10-18-r4`: restored an investor-portal sample after an ephemeral-store reset, saved a clarification with a source note, reloaded and confirmed both persisted. A second independent sample produced a draft estimate; its Markdown proposal downloaded. The browser reported no console errors during this check.
- Storage failure tests cover an initial failed write, a failed update, a corrupt file and an interrupted actuals/calibration commit. These are simulated failures; the free host still needs a durable database for production use.
