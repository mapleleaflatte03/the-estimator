# Evaluation log: from first estimate to final result

This is the full record of how PARALLAX was tested and improved: every run, what changed after it, and what was
learned. The table at the end is generated from `datasets/eval/journal.jsonl` by `scripts/journal_report.py`, so
its numbers are exactly what the evaluation scripts recorded.

## Ground rules (kept for every round)

1. **Labels before runs.** Each clause set was written and hand-labelled before any reader ran on it. Round 4's labels
   were committed (`6169d92`, 2026-10-17 02:02 +07) before the run, so the order can be checked in git.
2. **Held-out vs dev.** A rule fix is only *evidence* when measured on data that was not used to derive it. Results on
   the data a fix came from are labelled **dev** and never quoted as accuracy.
3. **Append-only journal.** Every run, including disappointing ones, is appended to `datasets/eval/journal.jsonl`
   with the rules fingerprint and model version.
4. **Thresholds fixed in advance.** Jev kind confidence ≥ 0.6 and tentative probability ≥ 0.7 were set before the
   first held-out run and never tuned.

## What is measured

| Question | Data | Metric |
| --- | --- | --- |
| Does learning from actual hours make estimates more accurate over time? | SiP: 10,022 real tasks, 2004–2014 (CC BY-NC-ND 4.0) | MAE vs. the human estimate on a later period never seen in fitting |
| Does the reader find the kind of work in each clause? | Hand-labelled clause sets, rounds 1–4 | Primary kind found |
| Does it notice what the client has **not** committed to? | Same sets | Tentative clauses caught, false alarms |
| Does it keep every requirement in real English specs? | PROMISE_exp: 969 requirements from 47 projects (Lima et al., 2019) | Retention, NFR recall, false alarms |
| Can a zero-shot size reading predict story points as well as a model trained for that? | Choetkiertikul et al. 2019: 23,313 issues, 16 projects, authors' test split (doi:10.1109/TSE.2018.2792473) | MAE vs Deep-SE and vs a median baseline. One project-level MAE is not a paired test |
| Does a pre-registered correction beat the shipped size-only hour model? | SiP tasks estimated in 2010 (557), models fit on 2004–2009 | MAE vs size-only, P10–P90 coverage, paired bootstrap CI. 2011–2014 is scored only if the 2010 rule promotes a candidate |

## Timeline

### 1. Calibration on real effort data (SiP)

Fit on tasks estimated before 2011, test on 2,248 tasks from 2011–2014:

- MAE: **10.34 h** with the human estimate as-is → **9.26 h** calibrated (**−10.4%**).
- P10–P90 interval: 82.0% coverage (target 80%).
- Rolling refit beats a model frozen after 2005 in 8 of 9 test years.
- At work-package level the holdout has only 7 cases and the results are mixed, so no claim is made there.

### 2. Round 1: first AI reader test (31 clauses)

Provider search came first:
- jevai.org returned HTTP 502.
- Vercel's free AI Gateway tier does not serve Jev.
- An alternative model ("Laya") found 7/12 kinds on a smoke test and was rejected.

Jev `jev-1.13.0` was then reached through JevStation.

| Reader | Primary kind | Tentative caught | False alarms |
| --- | --- | --- | --- |
| Rules | 23/31 | 2/6 | 0 |
| Jev alone | 23/31 | 6/6 | 0 |
| **Shipped** (rules first, Jev fills gaps, extra Jev kinds become questions) | **24/31** (+4 offered as questions) | **6/6** | 0 |

**Learned:**
- The AI's main value is noticing uncommitted wording, not classifying.
- Using Jev's kind silently when the rules already found something would add unverified hours, so it is asked as a question instead.

### 3. Round 2: new clauses (30)

| Reader | Primary kind | Tentative caught | False alarms |
| --- | --- | --- | --- |
| Rules | 23/30 | 1/5 | 0 |
| Jev alone | 19/30 | 4/5 | 0 |
| **Shipped** | **24/30** | **5/5** | 0 |

### 4. Rule fixes from rounds 1–2, checked on round 3 (25 new clauses)

The errors from rounds 1–2 led to new taxonomy patterns and hedges. Round 3 was written after that analysis but
before the fixes were coded, and was never used to tune them.

| Rules on round 3 (held-out) | Primary kind | Tentative caught |
| --- | --- | --- |
| Before fixes | 17/25 | 3/4 |
| After fixes | **23/25** | **4/4** |

On rounds 1–2 themselves the fixed rules reach 29/31 and 28/30 primary kind. Those sets were used to derive the
fixes (dev), so this is not evidence.

### 5. Real English requirements (PROMISE_exp)

The 969 requirements were split by project parity:
- Fixes were derived from even-numbered projects only.
- Odd-numbered projects (392 requirements) were held out for scoring.

| Odd projects (held-out) | Before | After |
| --- | --- | --- |
| Requirements kept | 72.7% | **100%** |
| Performance requirements recognised | 3.2% | **51.6%** |
| Security requirements recognised | 54.7% | **77.4%** |
| Performance false alarms | 0/361 | 3/361 |
| Security false alarms | 15/339 | 17/339 |
| False "tentative" | 0/392 | 0/392 |

The recall gain costs a few extra false alarms. That trade-off is recorded, not hidden.

### 6. Round 4: final end-to-end test of the shipped reader (16 new clauses)

Round 4 had 16 clauses:
- Vietnamese with and without diacritics, plus English.
- Clinic, logistics, school, HR, retail and finance briefs.
- 5 tentative clauses, and one trap where "có thể" means *is able to*, not *maybe*.

The run spent the last credits of the main account. They covered 7 calls, i.e. 14 of the 16 clauses; the balance
afterwards was 0.

| Reader (14 clauses read by Jev) | Primary kind | Tentative caught | False alarms |
| --- | --- | --- | --- |
| Rules | 13/14 | 2/4 | 0 |
| Jev alone | 11/14 | 4/4 | 0 |
| **Shipped** | **14/14** | **4/4** | 0 |

On all 16 clauses the rules found 14/16 primary kinds and caught 3/5 tentative clauses.

**Learned:** on brand-new wording the rules alone still miss hedges. Earlier rounds had suggested the rules were
already sufficient; round 4 shows the AI reader is still needed.

### 7. Fixes from round 4 (dev) and regression checks

Round 4 errors led to four narrow patterns:

| Pattern | Catches | Guard |
| --- | --- | --- |
| "đang / còn / sẽ cân nhắc", "cân nhắc có / xem / việc" | Tentative | Without diacritics "cân nhắc" folds to the same text as "cần nhắc" (remind). Bare "can nhac" is avoided so that "Hệ thống cần nhắc lịch hẹn" stays firm. |
| "if budget / time allows / permits", "budget / time permitting" | Tentative | — |
| "sang hệ thống mới", "từ file / hệ thống / phần mềm … cũ" | Data migration | — |
| "tìm … theo …" (within 40 characters) | Search | — |

Results:
- Round 4 after the fixes: 16/16 primary kind, 5/5 tentative. This is **dev**: the fixes came from round 4, so it is
  not evidence of generalisation.
- **Regression checks:** rounds 1, 2 and 3 and the PROMISE odd projects are unchanged, number for number. Tests pin
  the new patterns and their traps.

### 8. Incident: cached AI readings overwritten

**What happened:** a rules-only run with the AI disabled started with an empty cache and, at the end of `read()`,
wrote that empty cache over `datasets/jev_cache/clauses_v1.json`. The file had 95 readings, 14 of them paid for in
round 4.

**Recovery:**
- The 81 committed readings were restored from git.
- The 14 round-4 readings were rebuilt from `reader_results_round4_heldout.json`: kind, confidence, tentative
  probability and model.
- Only the runner-up kind probabilities of those 14 were lost; nothing in the app uses them.

**Fix:** the reader now writes the cache only after a fresh reading was added. A test asserts that a disabled reader
leaves the file byte-for-byte unchanged.

### 9. Product QA: layout under real numbers

An automated check rendered all six screens at 7 widths (320–1440 px) in light and dark mode, with large values
(1,500,000 VND/h, 1,234.5 actual hours).

- It found 27 distinct overflow problems; all were fixed and the re-run reports **0**.
- Screenshots at 320, 375 and 1280 px found 4 more issues the detector could not see, also fixed:
  - Header overlap.
  - An unreadable chart label.
  - Steps hidden off-screen.
  - A squeezed actuals table.

### 10. Jev becomes required; a pool of keys

The AI reader is now mandatory: an estimate is only produced once Jev has read every clause (otherwise the API
answers 503 with the reason). Nine JevStation keys were provided; a probe found key 1 empty and keys 2–9 at 49
credits each. A probe of the pricing found **1 credit for 1–5 questions and 3 credits for 6–10**, so the client now
packs exactly 5 questions per call across clauses, runs calls in parallel and moves to the next key on HTTP 402.

### 11. Incident: 60 credits spent on unreadable answers

The first pilot run named questions `c0__open_scope` (double underscore). The API normalises answer keys to
`c0_open_scope`, so 60 paid calls returned answers the client could not match, and nothing was cached.

**Fix:**
- Single underscores, plus loose key matching.
- A circuit breaker: if a charged call yields no usable answer, the reader halts all further spending until a
  human looks.
- Both are covered by tests.

The pilot was then re-run: 59 credits.

### 12. Can Jev tell which estimates will overrun? (SiP, real outcomes)

The question asked was whether Jev, reading only a task's one-line text, can tell which human estimates will run
over. Population: SiP Development tasks estimated at ≥ 20 h: 579 before 2011, 219 from 2011.

| Pilot, 75 training tasks | Spearman with log(actual/estimate) | AUC (overrun > 25%) |
| --- | --- | --- |
| open-ended / loosely defined | 0.106 | 0.631 |
| builds something new | **0.302** | 0.595 |
| depends on data moves / other parties | 0.190 | 0.598 |
| **"would an experienced developer expect it to take longer than it looks?"** | 0.297 | **0.678** |

The pre-written rule (highest Spearman) picked `new_build`; it was overridden for `overrun`, with the reason
recorded before any test data was touched:
- The Spearman values were a tie.
- `overrun` had the higher AUC.
- Nearly every clause of a greenfield brief is "new build".

The journal keeps both entries.

`overrun` was then asked of every remaining training task and all test tasks (141 credits). Thresholds came from
training data (tertiles at p = 0.66 and 0.71). The test set was scored once:

| Group | Training median actual/estimate | 2011–2014 median actual/estimate |
| --- | --- | --- |
| low | 0.590 (n=222) | 0.647 (n=110) |
| medium | 0.655 (n=174) | 0.692 (n=50) |
| high | 0.779 (n=183) | 0.952 (n=59) |

| Metric on 219 unseen tasks | Human estimate | Ratio model, size only | Ratio model + Jev group |
| --- | --- | --- | --- |
| MAE | 56.9 h | 52.1 h | 52.7 h |
| PRED(25) | 23.7% | 16.4% | 19.6% |
| P10–P90 coverage | — | 76.3% | 76.7% |

On unseen tasks the ranking holds (Spearman 0.197, AUC 0.62). High-risk work overran 1.47× as much as low-risk
work, against 1.32× in training.

As a point forecast, the change in MAE is not significant: the paired-bootstrap 95% CI of the gain is
−1.9 to +0.7 h.

**Used in the app:** the identical question is asked of every brief clause. Medium and high groups get the
*training* ratios (×1.11, ×1.32 relative to low), and low-risk clauses keep their hours.

### 13. Round 5: two new briefs, 24 new clauses

The labels were committed on their own commit (`Round 5 held-out labels…`) before any reader ran.

| Reader | Primary kind | Tentative caught | False alarms |
| --- | --- | --- | --- |
| Rules (incl. round-4 fixes, first held-out check) | 21/24 | 1/6 | 0 |
| Jev alone | 18/24 | 6/6 | 0 |
| **Shipped** | **21/24** (+2 as questions) | **5/6** | 0 |

The shipped reader missed one tentative clause, "…thì để xem ngân sách đã". Jev gave it 0.53, below the 0.7
threshold that was fixed in advance; the threshold was not changed.

The round-4 fixes did not generalise to new hedges: the rules caught only 1/6. That confirms the AI reader is the
part that catches uncommitted scope.

Fixes from round 5 (dev):
- Hedges: "để xem ngân sách", "đang tính có nên", "if there's time", "down the line", "not sure whether", "we may
  want".
- Branch-only visibility counts as permissions.
- "Customers get an email" counts as a notification.
- "entering their …" counts as a form.

Rounds 1–4 and PROMISE odd projects are unchanged, number for number. Round 5 after its own fixes scores 24/24 and
6/6, which is dev, not evidence.

### 14. Standard statistics on the SiP holdout

The holdout result is now also reported with the statistics reviewers expect. The baseline is the developers' own
estimate, i.e. what the company actually used.

- **SA** (accuracy relative to random guessing; Shepperd & MacDonell): 48.6% → 54.0%.
- **MdAE:** 1.0 h → 1.0 h. Most tasks are small and exact.
- **Wilcoxon signed-rank on per-task absolute errors:** p = 3.2×10⁻⁶, effect size 0.21. The model is closer on 16.3%
  of tasks and the human on 12.3%; the rest tie.

### 15. Production replay (completion-date aware)

The temporal split above had a small gap: a task estimated before 2011 but finished later still counted as training
data. `scripts/sip_operational_replay.py` closes it. Every 2011–2014 estimate is made on its estimate date, using
only tasks *completed* before that date, and the model is refitted daily. That is what the app does in production.

Result on the 1,391 tasks with a completion date:

| | Human | Frozen at 2011 | Online (app) |
| --- | --- | --- | --- |
| MAE | 4.33 h | 3.82 h | 3.85 h |
| SA | 56.3% | 61.4% | 61.1% |
| P10–P90 coverage | — | 85.3% | 85.0% |
| Wilcoxon vs human | — | p = 0.002 | p = 0.006 |

- The calibrated forecast beats the developers' estimates in production conditions.
- Refitting daily did not beat a model frozen at 2011 in this period. The process was stable, so learning
  mainly guards against drift.
- On the 105 large development tasks Jev had read, Jev's overrun groups did not reduce MAE (23.8 h without, 24.7 h
  with).

### 16. Independent replication on other organisations (Itemlet, interim)

`scripts/itemlet_jev_replication.py` tests whether the SiP finding carries over to other organisations.

- **Data:** Itemlet (CC BY 4.0), 2,032 issues of ≥ 20 h from open-source Jira projects. The original estimate is
  recovered from Jira's `workratio`.
- **Pre-registered** in `d9e5a7f` before any call: SiP thresholds and factors applied unchanged, and issues read in a
  fixed random order.
- **Interim:** the credits ran out after 465 issues (30 projects), which is still a random sample. We committed to
  reading the full population regardless of this result.

| Jev overrun group | n | Median actual/estimate | Share overrunning > 25% |
| --- | --- | --- | --- |
| low | 289 | 0.76 | 18.0% |
| medium | 88 | 0.86 | 20.5% |
| high | 88 | 0.87 | 30.7% |

- **Direction replicates:** high-risk work overran more often.
- **The signal is much weaker:** Spearman 0.05, AUC 0.56.
- **The SiP factors hurt:** multiplying estimates by them made MAE worse (18.6 → 19.9 h, gain CI −1.8..−0.7 h).

### 17. Decision: the overrun reading is a flag, not hours

Three tests agree:
- SiP holdout: no MAE gain.
- Production replay: no MAE gain.
- Itemlet: MAE significantly worse with the SiP factors.

The app therefore no longer multiplies hours by the SiP factors. Requirements Jev rates high-risk are flagged for
senior review. Their group factor starts at 1.0 and moves only with the team's own per-requirement actuals (partial
pooling).

This decision was made on replication data, so it is reported as such. The SiP factors stay visible as evidence.

### 18. Round 6: the challenge host's domain

GOLDEN-07 is an investor onboarding portal for a private equity fund: 13 clauses, 3 tentative. Its labels were
committed in `60fbfe8` before any run. Jev was reached through TypeSafe directly, with the same pinned model
`jev-1.13.0`.

| Reader | Primary kind | Tentative caught | False alarms |
| --- | --- | --- | --- |
| Rules (incl. round-5 fixes, first held-out check) | 10/13 | 2/3 | 0 |
| Jev alone | **13/13** | **3/3** | 0 |
| **Shipped** | 12/13 (+1 as a question) | **3/3** | 0 |

Kind precision of the rules was 50%: they add kinds the clause does not ask for. That is the next thing to fix.

### 19. Itemlet replication, final (all 2,032 issues)

After the top-up, the reader continued in the pre-registered order to the full population (37 projects). This was
done through TypeSafe directly, at a few cents in total.

| Jev overrun group | n | Median actual/estimate | Share overrunning > 25% |
| --- | --- | --- | --- |
| low | 1,279 | 0.82 | 19.9% |
| medium | 407 | 0.85 | 21.1% |
| high | 346 | 0.925 | 28.6% |

- **Direction confirmed:** high-risk work overran more often, 28.6% vs 19.9%, two-proportion z ≈ 3.5.
- **Weak as a predictor:** Spearman 0.054, AUC 0.535.
- **SiP factors hurt:** multiplying estimates by them increased MAE, 18.35 → 19.54 h (gain CI −1.45..−0.95 h).

The interim result (section 16) and this final one agree, and the decision in section 17 stands.

### 20. Jev verifies the kinds the rules propose (dev on rounds 1–6)

Round 6 showed that the keyword rules add kinds a clause does not ask for: kind precision was 50%. Each extra kind
adds hours.

The fix: for every rule-proposed kind other than Jev's own, Jev now answers a yes/no question, "does the requirement
itself ask for <kind>?". Kinds below a threshold are dropped from the estimate and offered back as a client question,
so nothing disappears silently.

On rounds 1–6 (139 clauses, already used, so this is **dev**; `scripts/verify_kinds_dev.py`, cost $0.0014):

| Setting | Kind precision | Kind recall | Primary kind |
| --- | --- | --- | --- |
| no verification | 81.0% | 89.5% | 134/139 |
| verify ≥ 0.4 | 88.0% | 90.1% | 135/139 |
| verify ≥ 0.6 | 92.6% | 87.7% | 135/139 |

0.4 was fixed (`VERIFY_MIN`) because precision improves without losing recall. It was committed together with the
round-7 labels (`9779516`) before round 7 ran.

### 21. Round 7: verification on new clauses (held-out)

24 new clauses from two new sample briefs: an English-language centre written in Vietnamese, including one clause
without diacritics, and a construction site-inspection app in English. Labels were committed in `9779516` before any
run.

| Reader | Primary kind | Kind precision | Kind recall | Tentative caught | False alarms |
| --- | --- | --- | --- | --- | --- |
| Rules (incl. round-5 fixes) | 15/24 | 72.0% | 56.2% | 4/4 | 0 |
| Jev alone | 19/24 | 100% | 71.9% | 4/4 | 0 |
| Shipped before (rules + Jev) | 16/24 (+3 as questions) | 73.1% | 59.4% | 4/4 | 0 |
| **Shipped now (+ verification)** | **17/24** (+2 as questions) | **83.3%** | **62.5%** | **4/4** | 0 |

- **Verification holds on held-out data:** kind precision rose by 10 points and nothing was lost.
- **The round-5 hedge fixes generalised this time:** the rules caught 4/4 tentative clauses.
- **Jev alone found more primary kinds than the shipped reader** in rounds 6 and 7, which are English-heavy. Across
  all rounds the shipped reader is still ahead (rounds 1–2 favour rules). A language-aware policy is a candidate for
  a future pre-registered round.

### 22. A live test on the deployed site, and round 8

A brand-new brief was entered on the live site: a car-wash booking platform with 7 clauses. Jev read it through
TypeSafe in 1.5 s, for $0.00022.

The test exposed a pattern:
- "pay by card… refunds" was read by the rules as *scheduling*, from the word "booking".
- Jev read it as *payments* with high confidence, but the app only offered that as a question.

On rounds 1–7 (dev, `scripts/confident_kind_dev.py`), adding Jev's kind directly at confidence ≥ 0.95 raised primary
kind from 152/163 to 155/163, with precision −0.6 points. `AI_ADD_MIN = 0.95` was committed with the round-8 labels
(`d194f64`) before round 8 ran.

Round 8 had 24 new clauses: restaurant, payroll and delivery in Vietnamese (one clause without diacritics); clinic and
real estate in English.

| Reader | Primary kind | Kind precision | Kind recall | Tentative caught | False alarms |
| --- | --- | --- | --- | --- | --- |
| Rules | 16/24 | 81.0% | 60.7% | 2/3 | 0 |
| Jev alone | 22/24 | 100% | 85.7% | 3/3 | 0 |
| Shipped before (rules + Jev) | 20/24 | 84.6% | 78.6% | 3/3 | 0 |
| + verification (section 20) | 21/24 | **95.8%** | 82.1% | 3/3 | 0 |
| **+ add near-certain Jev kinds (shipped now)** | **21/24** | **95.8%** | 82.1% | **3/3** | 0 |

- **Verification is confirmed a second time on held-out data:** precision rose by 11 points.
- **Adding near-certain kinds was neutral on this round.** It is kept, because it helped on dev and did no harm here.

### 23. Honest ranges for every size of work (adaptive conformal)

**Problem.** In the SiP holdout, the "80%" range held 82% of actuals overall, but only 66% for tasks of 50 h or more
and 85–90% for small ones. That is overconfident where it matters most and too cautious elsewhere.

**Method.** Adaptive Conformal Inference (Gibbs & Candès 2021), one level per size bucket (`parallax/conformal.py`).
When a task completes, the level moves by γ·(target miss − miss), so the long-run hit rate converges to 80% even
under drift.

**Choosing γ.** It was chosen on a production replay of the training period, 2008–2010
(`scripts/sip_conformal_replay.py select`). The rule was the smallest worst-bucket gap to 80%: γ = 0.05.

**Held-out test.** One production replay of 2011–2014 (1,391 tasks with completion dates); each outcome updates the
level on its completion day.

| Size | n | Fixed ranges | Adaptive ranges | Mean width |
| --- | --- | --- | --- | --- |
| 0–4 h | 905 | 84.3% | **80.0%** | 2.6 → 2.5 h |
| 4–8 h | 214 | 89.7% | **81.3%** | 10.1 → 7.3 h |
| 8–20 h | 101 | 89.1% | **82.2%** | 28.8 → 23.3 h |
| 20–50 h | 144 | 78.5% | **79.9%** | 52.9 → 108.7 h |
| ≥ 50 h | 27 | 88.9% | 85.2% | 183.6 → 163.7 h |
| **all** | 1,391 | 85.0% | **80.4%** | 14.4 → 18.9 h |

- Every bucket with enough data lands within 2.2 points of 80%.
- The trade-off: ranges for 20–50 h work almost doubled, while small work got narrower ranges.
- The ≥ 50 h bucket is too small (27 tasks) to conclude anything.

**In the app.** Each recorded project updates the level with the same γ, and the next estimates use the adapted
percentiles (`range_percentiles`). The UI tells the user whether the last range was hit and how the next ones change.

### 24. Person and project effects (negative result, not shipped)

**Idea.** Would a senior estimator's tacit knowledge, such as "this project runs over" or "this person under-estimates",
help? We tested it as partially pooled effects on log(actual/estimate) (`parallax/hierarchical.py`).

**Choosing the model.** Inside the training period: fit 2004–2009, validate on 2010 (557 tasks), 27 candidates. The
rule was the lowest validation MAE with coverage ≥ 75%. It picked size + assignee, k = 5: validation MAE 7.995 vs
8.189 for size only.

**Held-out test (2011–2014, once).**

| | Human | Size only (shipped) | Size + assignee |
| --- | --- | --- | --- |
| MAE | 10.34 h | **9.26 h** | 9.34 h |
| SA | 48.6% | **54.0%** | 53.6% |
| PRED(25) | 44.9% | **45.4%** | 42.6% |
| P10–P90 coverage | — | 82.0% | 78.1% |

The person effects did not carry over to later years; staff and habits change. The gain CI against size only is −0.34
to +0.19 h, so it is not shipped. The app's per-project-type and per-kind learning use the same pooling but start
from no effect and only move with the team's own data.

### 25. Story points from text (negative result, not shipped)

**Question.** Can the same reader, with no training on story points, size an issue as well as Deep-SE, a model
trained for that task?

**Data.** M. Choetkiertikul, H. K. Dam, T. Tran, T. Pham, A. Ghose and T. Menzies, "A Deep Learning Model for
Estimating Story Points", IEEE TSE 45(7):637–656, 2019, doi:10.1109/TSE.2018.2792473. 23,313 issues from 16
open-source projects. Files and the authors' 60/20/20 chronological split are from
https://github.com/morakotch/datasets at `133a5f5` (`scripts/fetch_storypoints.py`). Published Deep-SE, mean and
median MAE are Table 3 of the preprint in that repository. GPT2SP is not compared: Tawosi, Moussa and Sarro
(IEEE TSE 2023, arXiv:2201.05401) reported an evaluation bug in those figures.

**Method.** Jev answered a 5-level size question that never mentions story points (`SIZE_Q` in `parallax/jev.py`).
Per project, that score was mapped to points with a monotone step function. Four mappings were fit on the
training split and compared on the validation split. `bins10` had the lowest mean validation MAE (2.63).
The single test refit that chosen mapping on train+validation, then scored the test split once
(`scripts/storypoint_benchmark.py`). All 23,313 issues were read. Re-running `test --no-journal` from the
saved scores reproduces `datasets/eval/storypoint_result.json`.

**Test result.** Unweighted mean of the 16 project MAEs. 4,692 test issues. Deep-SE, Mean and Median below
are Table 3 of the preprint, checked against `datasets/external/deepse/preprint.pdf` (the accepted manuscript
carrying doi:10.1109/TSE.2018.2792473). "Our median" is the median of story points in that project's
train+validation rows, scored on the test rows. It is not Table 3's Median column: the two averages are
2.56 and 2.77. The paper's own baseline code was not re-run.

| | Jev | Deep-SE (Table 3) | Table 3 median | Our median |
| --- | --- | --- | --- | --- |
| Mean MAE | 2.54 | **2.09** | 2.77 | 2.56 |
| Projects where this column has a higher MAE than Jev | — | 4/16 | 11/16 | 10/16 |

The 4/16 and 11/16 counts compare one published MAE with one MAE of ours. They are not a paired test.
Wilcoxon is only against our recomputed median, issue by issue. It is significant (p < 0.05) and in Jev's
favour on 6 projects: Mesos, Titanium, DuraCloud, Data Management, Mule, Talend ESB. It is significant and
against Jev on 2: Moodle (p = 5.4×10⁻⁶) and Talend Data Quality (p = 2.4×10⁻⁴). Median Spearman of the raw
score against story points was 0.49.

| Project | n | Jev | Our median | Table 3 median | Deep-SE |
| --- | --- | --- | --- | --- | --- |
| Mesos | 337 | 0.90 | 1.22 | 1.73 | 1.02 |
| Usergrid | 98 | 1.15 | 1.15 | 1.60 | 1.03 |
| Appcelerator Studio | 586 | 1.40 | 1.30 | 1.84 | 1.36 |
| Aptana Studio | 168 | 3.14 | 3.61 | 3.71 | 2.71 |
| Titanium | 452 | 1.71 | 2.04 | 2.47 | 1.97 |
| DuraCloud | 135 | 0.64 | 0.82 | 0.73 | 0.68 |
| Bamboo | 106 | 0.84 | 0.75 | 1.32 | 0.74 |
| Clover | 79 | 3.15 | 3.57 | 2.84 | 2.11 |
| Jira | 72 | 1.79 | 1.58 | 2.93 | 1.38 |
| Moodle | 235 | 9.11 | 6.59 | 7.18 | 5.97 |
| Data Management | 935 | 5.08 | 6.19 | 4.82 | 3.77 |
| Mule | 180 | 2.07 | 2.47 | 2.69 | 2.18 |
| Mule Studio | 148 | 3.45 | 3.66 | 3.30 | 3.23 |
| Spring XD | 707 | 1.67 | 1.71 | 2.07 | 1.63 |
| Talend Data Quality | 278 | 3.91 | 3.31 | 3.87 | 2.97 |
| Talend ESB | 176 | 0.66 | 0.92 | 1.16 | 0.64 |

Data Management is the case that shows why the two medians must not be mixed: Jev MAE 5.08 beats our median
6.19 and loses to Table 3's median 4.82, and loses to Deep-SE 3.77. Moodle dominates the average
(9.11 vs Deep-SE 5.97).

**Decision.** Not shipped. On this benchmark a zero-shot reading is in the neighbourhood of a per-project
median and behind Deep-SE. The product still estimates hours from a brief plus the team's own actuals. This
run does not show that a size score read from text should be added to that hour model.

### 26. Other hour corrections (negative result, not shipped)

**Question.** On tasks estimated in 2010, does any correction listed in advance have a lower MAE than the shipped
size-only model?

**What this run does not repeat.** The hierarchical factor grid (section 24), turning an overrun reading into extra
hours, the conformal step, and the story-point reader. No Jev calls.

**Protocol.** `datasets/eval/sip_correction_protocol_v1.json`, committed in `4668353` before the score. Eight
candidates: trailing windows that ignore ratios from before 2006, 2007, or 2008; shrinking each size-bucket ratio
toward the pooled ratio (k = 30 and k = 100); a round-versus-odd split inside the shipped size buckets; and two
other bucket edges (powers of two, and 8 h / 40 h). Fit on tasks estimated before 2010. Score 2010 only (557 tasks).
A candidate is promoted only when its P10–P90 coverage is at least 75%, its MAE is strictly below size-only, and
the paired bootstrap 95% CI of the MAE gain is entirely above 0 (5,000 resamples, seed 20261017). Otherwise
2011–2014 stays closed.

**2010 result.** Size-only MAE 8.189 h, coverage 82.76%. Human MAE 8.738 h. Every gain CI includes 0, so nobody
was promoted. `datasets/eval/sip_correction_choice.json` records `holdout_scored: false`. Tasks estimated in
2011–2014 were not scored.

| Candidate | MAE (h) | P10–P90 | MAE gain vs size-only, 95% CI |
| --- | --- | --- | --- |
| size-only (shipped) | **8.189** | 82.76% | — |
| recent-2006 | 8.204 | 80.61% | [−0.043, 0.012] |
| recent-2007 | 8.174 | 79.35% | [−0.025, 0.058] |
| recent-2008 | 8.185 | 79.53% | [−0.046, 0.050] |
| shrink-k30 | 8.225 | 82.23% | [−0.189, 0.105] |
| shrink-k100 | 8.276 | 81.51% | [−0.453, 0.246] |
| round-by-bucket | 7.955 | 82.59% | [−0.202, 0.739] |
| edges-pow2 | 8.262 | 80.79% | [−0.166, 0.016] |
| edges-coarse | 8.149 | 80.61% | [−0.106, 0.184] |

A positive gain is a lower MAE than size-only. The lowest point estimate is round-by-bucket, 7.955 h against
8.189 h. Its interval runs from a loss of 0.202 h to a gain of 0.739 h. Wilcoxon against size-only is p = 0.24,
and against the human estimate p = 0.568 (the p in journal row 48). No candidate has p < 0.05 against
size-only. The smallest of those p-values is 0.157, for edges-pow2, and that MAE is higher than size-only.
Eight candidates shared this screen. A single CI lying entirely above 0 would still not have been a
family-wise 95% claim. No lower bound was above 0.

**Decision.** Not shipped. The screen does not replace the size-only model. These rows already contain a human
estimate, so the result does not speak to a brief that has no estimate and no actual hours.

## Final result (held-out numbers only)

| Claim | Evidence |
| --- | --- |
| Learning from actual hours makes estimates more accurate | SiP 2011–2014, 2,248 unseen tasks: MAE −10.4%, SA 48.6 → 54.0%, Wilcoxon p = 3.2×10⁻⁶, P10–P90 coverage 82.0%. Production replay (1,391 tasks): SA 56.3 → 61.1%, p = 0.006, coverage 85.0% |
| The shipped reader notices what the client has not committed to | Rounds 1, 2, 4–8: **30/31** tentative clauses caught vs **14/31** with rules alone, **0** false alarms |
| The shipped reader finds the main kind of work | Rounds 1, 2, 4–8: **133/160** vs 121/160 with rules alone |
| The 80% range is honest for every size of work | Production replay 2011–2014 with adaptive conformal ranges: 85.0% → **80.4%** overall; every bucket with n ≥ 100 within 2.2 points of 80% (was up to 9.7 off) |
| AI verification removes kinds the client did not ask for | Round 7: kind precision 73.1% → **83.3%**; round 8: 84.6% → **95.8%**; recall up in both |
| Jev spots work that will take longer than it looks | Partly. SiP 2011–2014: high-risk group overran 1.47× as much as low-risk (Spearman 0.20, AUC 0.62). Other organisations (Itemlet, all 2,032 issues): same direction, weak (AUC 0.535). No MAE gain anywhere, so it is a review flag, not extra hours |
| A zero-shot size reading predicts story points | No. Choetkiertikul et al. 2019 test split, 16 projects. `bins10` chosen on validation, refit on train+validation, tested once: mean MAE 2.54 vs Table 3 Deep-SE 2.09 vs Table 3 median 2.77 vs our recomputed median 2.56. Lower MAE than Deep-SE on 4/16 projects, with no paired test. Not shipped |
| Rule fixes generalise | Round 3: 17/25 → 23/25. PROMISE odd projects: 72.7% → 100% kept, performance recall 3.2% → 51.6%. Round-4 hedge fixes did **not** generalise to round 5 (rules 1/6) |

## Limitations

- **Clause sets.** The sets were written by the developer in the style of client briefs, not taken from real client
  documents. They total 126 clauses, which is small.
- **Round-5 fixes.** They have no held-out confirmation yet; that needs a round 6.
- **Overrun transfer.** The overrun factors come from SiP maintenance tasks; per-requirement actuals in the app are
  how they get corrected for greenfield work.
- **Model version.** Jev results are for `jev-1.13.0`. Another model version needs a new run.
- **Work-package level.** SiP shows no reliable gain at that level (7 holdout cases).

## Every run

<!-- AUTO:journal:start -->
| # | Date (UTC+7) | Run | Rules | Model | Result | Note |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-10-17 00:36 | `round2_rules_first` | `55dfa88a19` | — | rules: kind 23/30, tentative 1/5, false 0 | Round 2 VN set, rules before any change |
| 2 | 2026-10-17 00:37 | `round2` | `55dfa88a19` | jev-1.13.0 | rules: kind 23/30, tentative 1/5, false 0<br>jev: kind 19/30, tentative 4/5, false 0<br>shipped: kind 24/30 (precision 84.8%), tentative 5/5, false 0 | Round 2 VN set (held-out), Jev jev-1.13.0 via JevStation, rules before any round-2 change |
| 3 | 2026-10-17 00:40 | `round3_rules_before` | `55dfa88a19` | — | rules: kind 17/25, tentative 3/4, false 0 | Round 3 held-out, rules BEFORE round-2 fixes (summary only, details not inspected) |
| 4 | 2026-10-17 00:41 | `round1_dev_after_fixes` | `7ffca8bc41` | jev-1.13.0 | rules: kind 29/31, tentative 6/6, false 0<br>jev: kind 23/31, tentative 6/6, false 0<br>shipped: kind 29/31 (precision 87.8%), tentative 6/6, false 0 | Round 1 after round-2 rule fixes (this set was used to derive them: dev, not held-out) |
| 5 | 2026-10-17 00:41 | `round2_dev_after_fixes` | `7ffca8bc41` | jev-1.13.0 | rules: kind 28/30, tentative 5/5, false 0<br>jev: kind 19/30, tentative 4/5, false 0<br>shipped: kind 29/30 (precision 89.5%), tentative 5/5, false 0 | Round 2 after round-2 rule fixes (this set was used to derive them: dev, not held-out) |
| 6 | 2026-10-17 00:44 | `round3_rules_after` | `7ffca8bc41` | — | rules: kind 23/25, tentative 4/4, false 0 | Round 3 held-out, rules AFTER round-2 fixes: generalisation check |
| 7 | 2026-10-17 00:45 | `promise_rules_first` | `7ffca8bc41` | — | retention 69.7%, false tentative 4/969 | First PROMISE_exp run, rules as of round-2 fixes |
| 8 | 2026-10-17 00:46 | `promise_split_before` | `7ffca8bc41` | — | odd projects: retention 72.7%, performance recall 3.2%, security recall 54.7%, false tentative 0/392 | PROMISE split by project parity, rules BEFORE English fixes |
| 9 | 2026-10-17 00:47 | `promise_split_after` | `3e1ee5ba9d` | — | odd projects: retention 100.0%, performance recall 51.6%, security recall 77.4%, false tentative 0/392 | PROMISE split by project parity, AFTER English rule fixes derived from even projects only |
| 10 | 2026-10-17 00:47 | `round3_rules_after_english` | `3e1ee5ba9d` | — | rules: kind 23/25, tentative 4/4, false 0 | Round 3 held-out after English (PROMISE) fixes: regression check |
| 11 | 2026-10-17 00:56 | `sip_holdout` | `2860f74a76` | — | MAE 10.34 → 9.26 h (-10.4%), P10–P90 coverage 82.03% | Calibration benchmark on real SiP tasks: fit before 2011, test 2011-2014 |
| 12 | 2026-10-17 02:02 | `round4_heldout` | `2860f74a76` | jev-1.13.0 | rules: kind 13/14, tentative 2/4, false 0<br>jev: kind 11/14, tentative 4/4, false 0<br>shipped: kind 14/14 (precision 78.9%), tentative 4/4, false 0 | Round 4: 16 new clauses labelled before any reader ran (commit 6169d92). Final shipped reader, spends the last credits of the main key. (scored 14/16, API calls 7, credits left 0) |
| 13 | 2026-10-17 02:03 | `round4_rules_before` | `2860f74a76` | — | rules: kind 14/16, tentative 3/5, false 0 | Round 4, all 16 clauses, rules as shipped before the round-4 fixes (held-out for rules). |
| 14 | 2026-10-17 02:03 | `round1_rules_after_round4_fixes` | `d59755ab5f` | — | rules: kind 29/31, tentative 6/6, false 0 | Regression check after round-4 rule fixes (round 4 = dev, derived from it). |
| 15 | 2026-10-17 02:03 | `round2_rules_after_round4_fixes` | `d59755ab5f` | — | rules: kind 28/30, tentative 5/5, false 0 | Regression check after round-4 rule fixes (round 4 = dev, derived from it). |
| 16 | 2026-10-17 02:03 | `round3_rules_after_round4_fixes` | `d59755ab5f` | — | rules: kind 23/25, tentative 4/4, false 0 | Regression check after round-4 rule fixes (round 4 = dev, derived from it). |
| 17 | 2026-10-17 02:03 | `round4_rules_after_round4_fixes` | `d59755ab5f` | — | rules: kind 15/16, tentative 5/5, false 0 | Regression check after round-4 rule fixes (round 4 = dev, derived from it). |
| 18 | 2026-10-17 02:04 | `promise_after_round4_fixes` | `d59755ab5f` | — | odd projects: retention 100.0%, performance recall 51.6%, security recall 77.4%, false tentative 0/392 | Regression check after round-4 rule fixes. |
| 19 | 2026-10-17 02:04 | `round1_rules_final` | `5f17422a06` | — | rules: kind 29/31, tentative 6/6, false 0 | Final rules: round-4 fixes + 'tìm … theo' search pattern (round 4 = dev). |
| 20 | 2026-10-17 02:04 | `round2_rules_final` | `5f17422a06` | — | rules: kind 28/30, tentative 5/5, false 0 | Final rules: round-4 fixes + 'tìm … theo' search pattern (round 4 = dev). |
| 21 | 2026-10-17 02:04 | `round3_rules_final` | `5f17422a06` | — | rules: kind 23/25, tentative 4/4, false 0 | Final rules: round-4 fixes + 'tìm … theo' search pattern (round 4 = dev). |
| 22 | 2026-10-17 02:04 | `round4_rules_final` | `5f17422a06` | — | rules: kind 16/16, tentative 5/5, false 0 | Final rules: round-4 fixes + 'tìm … theo' search pattern (round 4 = dev). |
| 23 | 2026-10-17 02:04 | `promise_final` | `5f17422a06` | — | odd projects: retention 100.0%, performance recall 51.6%, security recall 77.4%, false tentative 0/392 | Final rules regression check. |
| 24 | 2026-10-17 02:07 | `round4_shipped_final` | `5f17422a06` | jev-1.13.0 | rules: kind 14/14, tentative 4/4, false 0<br>jev: kind 11/14, tentative 4/4, false 0<br>shipped: kind 14/14 (precision 78.9%), tentative 4/4, false 0 | Final shipped reader (final rules + cached Jev readings, no API calls) on round 4; rule fixes were derived from round 4, so this is dev, not held-out. (scored 14/16, API calls 0, credits left None) |
| 25 | 2026-10-17 13:53 | `sip_jev_pilot` | `` | jev-1.13.0 | open_scope@v1: Spearman 0.106, AUC 0.631<br>new_build@v1: Spearman 0.302, AUC 0.595<br>coupling@v1: Spearman 0.19, AUC 0.598<br>overrun@v1: Spearman 0.297, AUC 0.678 | Pilot on 75 TRAINING tasks only (estimated before 2011): choose the question to scale up. Chosen: new_build@v1 |
| 26 | 2026-10-17 13:53 | `sip_jev_pilot` | `` | jev-1.13.0 | open_scope@v1: Spearman 0.106, AUC 0.631<br>new_build@v1: Spearman 0.302, AUC 0.595<br>coupling@v1: Spearman 0.19, AUC 0.598<br>overrun@v1: Spearman 0.297, AUC 0.678 | Pilot on 75 TRAINING tasks only (estimated before 2011), test tasks untouched. Chosen: overrun@v1. Reason: Tie on Spearman (new_build 0.302 vs overrun 0.297); overrun has the higher AUC for >25% overruns (0.678 vs 0.595) and transfers to greenfield briefs, where nearly every clause is new_build. Decided on training data only. |
| 27 | 2026-10-17 13:54 | `sip_jev_holdout` | `` | jev-1.13.0 | human: MAE 56.92 h, PRED(25) 23.7%, P10–P90 —<br>size-only: MAE 52.11 h, PRED(25) 16.4%, P10–P90 76.3<br>jev:overrun@v1: MAE 52.65 h, PRED(25) 19.6%, P10–P90 76.7 | Held-out test 2011-2014. Jev overrun@v1 tertile split fitted on training tasks only. MAE gain vs size-only -0.54 h (95% CI [-1.91, 0.73]); test Spearman 0.197, AUC 0.62. |
| 28 | 2026-10-17 14:01 | `round5_rules_before` | `74c1409f3b` | — | rules: kind 21/24, tentative 1/6, false 0 | Round 5: 24 new clauses (labels committed before the run). Rules as shipped incl. round-4 fixes: first held-out check of those fixes. |
| 29 | 2026-10-17 14:02 | `round5_heldout` | `74c1409f3b` | jev-1.13.0 | rules: kind 21/24, tentative 1/6, false 0<br>jev: kind 18/24, tentative 6/6, false 0<br>shipped: kind 21/24 (precision 75.9%), tentative 5/6, false 0 | Round 5 held-out: 24 new clauses (VN + EN), labels committed before any reader ran. Shipped reader = rules + Jev via the 9-key pool. (scored 24/24, API calls 10, credits left 108) |
| 30 | 2026-10-17 14:03 | `round1_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 29/31, tentative 6/6, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 31 | 2026-10-17 14:03 | `round2_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 28/30, tentative 5/5, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 32 | 2026-10-17 14:03 | `round3_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 23/25, tentative 4/4, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 33 | 2026-10-17 14:03 | `round4_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 16/16, tentative 5/5, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 34 | 2026-10-17 14:03 | `round5_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 24/24, tentative 6/6, false 0 | Round 5 after its own rule fixes: dev, not evidence. |
| 35 | 2026-10-17 14:03 | `promise_after_round5_fixes` | `dd175964ab` | — | odd projects: retention 100.0%, performance recall 51.6%, security recall 77.4%, false tentative 0/392 | Regression check after round-5 rule fixes. |
| 36 | 2026-10-17 14:03 | `round5_shipped_final` | `dd175964ab` | jev-1.13.0 | rules: kind 24/24, tentative 6/6, false 0<br>jev: kind 18/24, tentative 6/6, false 0<br>shipped: kind 24/24 (precision 80.6%), tentative 6/6, false 0 | Final shipped reader (rules after round-5 fixes + cached Jev answers, no API calls) on round 5: dev, not held-out. (scored 24/24, API calls 0, credits left None) |
| 37 | 2026-10-17 14:51 | `itemlet_replication_interim` | `` | jev-1.13.0 | read 465/2032: high/low median ratio x1.145, Spearman 0.053, AUC 0.559<br>MAE raw 18.64 h → with SiP factors 19.86 h (gain CI [-1.81, -0.66]) | Independent replication on Itemlet (30 open-source Jira projects), SiP thresholds and factors unchanged, protocol committed before the run. Read 465/2032 (random prefix). |
| 38 | 2026-10-17 14:52 | `sip_operational_replay` | `` | jev-1.13.0 (cached) | human: MAE 4.33 h, PRED(25) 51.5%, SA 56.3%, P10–P90 —<br>frozen: MAE 3.82 h, PRED(25) 51.1%, SA 61.4%, P10–P90 85.3, Wilcoxon p 0.00208<br>online: MAE 3.85 h, PRED(25) 50.9%, SA 61.1%, P10–P90 85.0, Wilcoxon p 0.00552<br>dev>=20h human: MAE 26.89 h, PRED(25) 27.6%, SA 18.5%, P10–P90 —<br>dev>=20h online: MAE 23.81 h, PRED(25) 21.9%, SA 27.8%, P10–P90 81.0, Wilcoxon p 0.0155<br>dev>=20h online+jev: MAE 24.7 h, PRED(25) 22.9%, SA 25.1%, P10–P90 81.0, Wilcoxon p 0.0106 | Production replay: every estimate uses only work completed before its estimate date. Online = refit daily (what the app does); frozen = fitted on work completed before 2011. |
| 39 | 2026-10-17 14:56 | `round6_rules_before` | `f0608239a4` | — | rules: kind 10/13, tentative 2/3, false 0 | Round 6 (private-equity onboarding, 13 new clauses, labels committed in 60fbfe8 before the run). Rules incl. round-5 fixes: first held-out check of those fixes. |
| 40 | 2026-10-17 16:54 | `itemlet_replication_final` | `` | jev-1.13.0 | read 2032/2032: high/low median ratio x1.128, Spearman 0.054, AUC 0.535<br>MAE raw 18.35 h → with SiP factors 19.54 h (gain CI [-1.45, -0.95]) | Independent replication on Itemlet (37 open-source Jira projects), SiP thresholds and factors unchanged, protocol committed before the run. Read 2032/2032 (random prefix). |
| 41 | 2026-10-17 16:55 | `round6_heldout` | `f0608239a4` | jev-1.13.0 | rules: kind 10/13, tentative 2/3, false 0<br>jev: kind 13/13, tentative 3/3, false 0<br>shipped: kind 12/13 (precision 54.5%), tentative 3/3, false 0 | Round 6 held-out: private-equity investor onboarding (challenge host's domain), 13 new clauses, labels committed in 60fbfe8 before any reader ran. Jev jev-1.13.0 via TypeSafe direct (same pinned model). (scored 13/13, API calls 2, credits left None) |
| 42 | 2026-10-17 17:01 | `round7_heldout` | `b226aede6c` | jev-1.13.0 | rules: kind 15/24, tentative 4/4, false 0<br>jev: kind 19/24, tentative 4/4, false 0<br>shipped: kind 16/24 (precision 73.1%), tentative 4/4, false 0<br>shipped+verify: kind 17/24 (precision 83.3%), tentative 4/4, false 0 | Round 7 held-out: 24 new clauses (VI + EN), labels committed in 9779516 before any reader ran. First held-out test of AI verification of rule kinds (VERIFY_MIN 0.4 fixed on rounds 1-6). Jev jev-1.13.0 via TypeSafe. (scored 24/24, API calls 4, credits left None) |
| 43 | 2026-10-17 17:11 | `round8_heldout` | `0d839b7e12` | jev-1.13.0 | rules: kind 16/24, tentative 2/3, false 0<br>jev: kind 22/24, tentative 3/3, false 0<br>shipped: kind 20/24 (precision 84.6%), tentative 3/3, false 0<br>shipped+verify: kind 21/24 (precision 95.8%), tentative 3/3, false 0<br>shipped+verify+add: kind 21/24 (precision 95.8%), tentative 3/3, false 0 | Round 8 held-out: 24 new clauses (VI + EN), labels committed before any reader ran. Tests adding Jev's kind directly at confidence >= 0.95 (fixed on rounds 1-7) on top of verification. Jev jev-1.13.0 via TypeSafe. (scored 24/24, API calls 4, credits left None) |
| 44 | 2026-10-17 18:48 | `sip_conformal_select` | `` | — | gamma 0.0: 80% range holds 85.5%, worst size bucket off by 7.3 pts, mean width 14.3 h<br>gamma 0.002: 80% range holds 81.7%, worst size bucket off by 3.4 pts, mean width 14.0 h<br>gamma 0.005: 80% range holds 81.0%, worst size bucket off by 3.4 pts, mean width 13.8 h<br>gamma 0.01: 80% range holds 80.5%, worst size bucket off by 2.5 pts, mean width 13.8 h<br>gamma 0.02: 80% range holds 80.4%, worst size bucket off by 1.9 pts, mean width 13.7 h<br>gamma 0.05: 80% range holds 80.0%, worst size bucket off by 1.1 pts, mean width 14.1 h | Choosing the adaptive-conformal step on the training period only (replay 2008-2010). Chosen gamma 0.05. |
| 45 | 2026-10-17 18:49 | `sip_conformal_holdout` | `` | — | fixed ranges: 80% range holds 85.0%, worst size bucket off by 9.7 pts, mean width 14.4 h<br>adaptive (gamma 0.05): 80% range holds 80.4%, worst size bucket off by 5.2 pts, mean width 18.9 h | Held-out production replay 2011-2014, gamma fixed on 2008-2010. Coverage by size bucket: 0-4h: 84.3% -> 80.0%; 20-50h: 78.5% -> 79.9%; 4-8h: 89.7% -> 81.3%; 8-20h: 89.1% -> 82.2%; >= 50h: 88.9% -> 85.2% |
| 46 | 2026-10-17 18:50 | `sip_hierarchical_holdout` | `` | — | human: MAE 10.337 h, PRED(25) 44.88%, SA 48.64%, P10–P90 —<br>size-only: MAE 9.255 h, PRED(25) 45.42%, SA 54.02%, P10–P90 82.03<br>hierarchical: MAE 9.339 h, PRED(25) 42.62%, SA 53.6%, P10–P90 78.11, Wilcoxon p 1.06e-07 | Hierarchical correction chosen on 2010 validation only (hier[bucket+assignee] k=5), fitted on pre-2011, tested once on 2011-2014. Wilcoxon vs size-only p=9.86e-18, MAE gain vs size-only CI [-0.343, 0.185] h. |
| 47 | 2026-10-17 19:17 | `storypoint_benchmark` | `` | jev-1.13.0 | MAE 2.542 vs Deep-SE 2.087 vs recomputed median 2.556; lower MAE than Deep-SE on 4/16, lower MAE than the recomputed median on 10/16 | Zero-shot Jev size score (variant bins10 chosen on validation), test split once. Deep-SE MAE from the authors' preprint Table 3 (doi:10.1109/TSE.2018.2792473). |
| 48 | 2026-10-17 21:22 | `sip_correction_validation` | `sip_correction_protocol_v1` | — | human: MAE 8.738 h, PRED(25) 51.53%, SA 53.8%, P10–P90 —<br>size-only: MAE 8.189 h, PRED(25) 52.06%, SA 56.71%, P10–P90 82.76<br>round-by-bucket: MAE 7.955 h, PRED(25) 52.24%, SA 57.94%, P10–P90 82.59, Wilcoxon p 0.568 | No correction promoted on 2010. Lowest MAE was round-by-bucket 7.955 h vs size-only 8.189 h, coverage 82.59%, MAE-gain 95% CI [-0.202, 0.739]. 2011-2014 was not scored. |
<!-- AUTO:journal:end -->
