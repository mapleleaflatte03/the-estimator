# Prospective quote and scope pilot

This is a plan for an end-to-end comparison, **not a result**. No local dataset currently contains the original client brief, a quote recorded before delivery, and the final hours for enough independent projects. SiP and Itemlet test task-level corrections; developer-written golden briefs test scope behavior, not quote accuracy.

## Cases and freeze

Start with 3–10 completed software projects from different clients or teams as a diagnostic pilot, then collect more before making a general accuracy claim. For every case, retain the original brief as it existed at intake, the human estimate or quote with its timestamp, approved scope changes, and actual hours with a consistent time-recording definition. Remove client identifiers and secrets before using the app. Reject cases where the original estimate was reconstructed after delivery.

Record the app commit, Jev model/version, configuration, cost rate, and evaluation criteria **before** running any cases. Do not tune rules, templates, prompts, or calibration on pilot cases and then score those same cases. Keep the original and revised briefs separate. If a case contributed to development or calibration, mark it as known and exclude it from the unseen comparison.

## Three workflows on the same brief

1. **Archived human baseline:** the estimate actually recorded before work began. This is the only valid baseline for retrospective hour error. Its elapsed preparation time can be compared only if a trustworthy timestamp or work log exists.
2. **PARALLAX draft:** run the frozen app on the intake brief with no knowledge of actual hours. Save the first estimate, questions, work items, model calls, and elapsed time. An independent reviewer answers questions only from information available before delivery; save the confirmation source and time. Record both first draft and reviewed version.
3. **Manual review baseline:** for a prospective speed test, ask a delivery lead to scope the same unseen brief using the team's normal spreadsheet/Jira process. Rotate case order and reviewer where possible. Do not compare a retrospective recollection of preparation time with a timed app run.

## Score every case

| Outcome | Measurement |
| --- | --- |
| Quote accuracy | Absolute error and absolute percentage error between hours quoted before delivery and actual hours, for archived human, app first draft, and app after review. Report per case, MAE and median absolute error; treat zero actual hours separately. |
| Range quality | Whether actual hours lie inside the app's stated interval, plus interval width. A few cases cannot establish calibrated 80% coverage. |
| Scope control | A blinded delivery lead labels each original clause as committed, tentative, or excluded using only intake evidence. Count missed committed work, prematurely included tentative work, and material work items with no source. Keep approved later changes separate from original-scope errors. |
| Effort to produce | Timed minutes from receiving the brief to a reviewable draft and to an approved quote; count clarification requests and manual work-item edits. Report the person's role and prior familiarity with the project. |
| Operational fit | Export readability, missing integration/security/dependency constraints, API or Jev failure, cost per case, and whether the reviewer would sign the quote. Record failures rather than replacing cases. |

Publish the anonymized case table, exclusions, code revision, and a qualitative failure analysis. With 3–10 cases, describe the findings as exploratory; do not infer a reliable win rate or promise a prize. A larger independent sample across multiple teams is needed before claiming superiority to the normal quoting process.
