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

## Final result (held-out numbers only)

| Claim | Evidence |
| --- | --- |
| Learning from actual hours makes estimates more accurate | SiP 2011–2014, 2,248 unseen tasks: MAE −10.4%, SA 48.6 → 54.0%, Wilcoxon p = 3.2×10⁻⁶, P10–P90 coverage 82.0%. Production replay (1,391 tasks): SA 56.3 → 61.1%, p = 0.006, coverage 85.0% |
| The shipped reader notices what the client has not committed to | Rounds 1, 2, 4, 5 and 6: **23/24** tentative clauses caught vs **8/24** with rules alone, **0** false alarms |
| The shipped reader finds the main kind of work | Rounds 1, 2, 4, 5 and 6: **95/112** vs 90/112 with rules alone |
| Jev spots work that will take longer than it looks | Partly. SiP 2011–2014: high-risk group overran 1.47× as much as low-risk (Spearman 0.20, AUC 0.62). Other organisations (Itemlet, all 2,032 issues): same direction, weak (AUC 0.535). No MAE gain anywhere, so it is a review flag, not extra hours |
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
| 2 | 2026-10-17 00:37 | `round2` | `55dfa88a19` | jev-1.13.0 | rules: kind 23/30, tentative 1/5, false 0<br>jev: kind 19/30, tentative 4/5, false 0<br>shipped: kind 24/30, tentative 5/5, false 0 | Round 2 VN set (held-out), Jev jev-1.13.0 via JevStation, rules before any round-2 change |
| 3 | 2026-10-17 00:40 | `round3_rules_before` | `55dfa88a19` | — | rules: kind 17/25, tentative 3/4, false 0 | Round 3 held-out, rules BEFORE round-2 fixes (summary only, details not inspected) |
| 4 | 2026-10-17 00:41 | `round1_dev_after_fixes` | `7ffca8bc41` | jev-1.13.0 | rules: kind 29/31, tentative 6/6, false 0<br>jev: kind 23/31, tentative 6/6, false 0<br>shipped: kind 29/31, tentative 6/6, false 0 | Round 1 after round-2 rule fixes (this set was used to derive them: dev, not held-out) |
| 5 | 2026-10-17 00:41 | `round2_dev_after_fixes` | `7ffca8bc41` | jev-1.13.0 | rules: kind 28/30, tentative 5/5, false 0<br>jev: kind 19/30, tentative 4/5, false 0<br>shipped: kind 29/30, tentative 5/5, false 0 | Round 2 after round-2 rule fixes (this set was used to derive them: dev, not held-out) |
| 6 | 2026-10-17 00:44 | `round3_rules_after` | `7ffca8bc41` | — | rules: kind 23/25, tentative 4/4, false 0 | Round 3 held-out, rules AFTER round-2 fixes: generalisation check |
| 7 | 2026-10-17 00:45 | `promise_rules_first` | `7ffca8bc41` | — | retention 69.7%, false tentative 4/969 | First PROMISE_exp run, rules as of round-2 fixes |
| 8 | 2026-10-17 00:46 | `promise_split_before` | `7ffca8bc41` | — | odd projects: retention 72.7%, performance recall 3.2%, security recall 54.7%, false tentative 0/392 | PROMISE split by project parity, rules BEFORE English fixes |
| 9 | 2026-10-17 00:47 | `promise_split_after` | `3e1ee5ba9d` | — | odd projects: retention 100.0%, performance recall 51.6%, security recall 77.4%, false tentative 0/392 | PROMISE split by project parity, AFTER English rule fixes derived from even projects only |
| 10 | 2026-10-17 00:47 | `round3_rules_after_english` | `3e1ee5ba9d` | — | rules: kind 23/25, tentative 4/4, false 0 | Round 3 held-out after English (PROMISE) fixes: regression check |
| 11 | 2026-10-17 00:56 | `sip_holdout` | `2860f74a76` | — | MAE 10.34 → 9.26 h (-10.4%), P10–P90 coverage 82.03% | Calibration benchmark on real SiP tasks: fit before 2011, test 2011-2014 |
| 12 | 2026-10-17 02:02 | `round4_heldout` | `2860f74a76` | jev-1.13.0 | rules: kind 13/14, tentative 2/4, false 0<br>jev: kind 11/14, tentative 4/4, false 0<br>shipped: kind 14/14, tentative 4/4, false 0 | Round 4: 16 new clauses labelled before any reader ran (commit 6169d92). Final shipped reader, spends the last credits of the main key. (scored 14/16, API calls 7, credits left 0) |
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
| 24 | 2026-10-17 02:07 | `round4_shipped_final` | `5f17422a06` | jev-1.13.0 | rules: kind 14/14, tentative 4/4, false 0<br>jev: kind 11/14, tentative 4/4, false 0<br>shipped: kind 14/14, tentative 4/4, false 0 | Final shipped reader (final rules + cached Jev readings, no API calls) on round 4; rule fixes were derived from round 4, so this is dev, not held-out. (scored 14/16, API calls 0, credits left None) |
| 25 | 2026-10-17 13:53 | `sip_jev_pilot` | `` | jev-1.13.0 | open_scope@v1: Spearman 0.106, AUC 0.631<br>new_build@v1: Spearman 0.302, AUC 0.595<br>coupling@v1: Spearman 0.19, AUC 0.598<br>overrun@v1: Spearman 0.297, AUC 0.678 | Pilot on 75 TRAINING tasks only (estimated before 2011): choose the question to scale up. Chosen: new_build@v1 |
| 26 | 2026-10-17 13:53 | `sip_jev_pilot` | `` | jev-1.13.0 | open_scope@v1: Spearman 0.106, AUC 0.631<br>new_build@v1: Spearman 0.302, AUC 0.595<br>coupling@v1: Spearman 0.19, AUC 0.598<br>overrun@v1: Spearman 0.297, AUC 0.678 | Pilot on 75 TRAINING tasks only (estimated before 2011), test tasks untouched. Chosen: overrun@v1. Reason: Tie on Spearman (new_build 0.302 vs overrun 0.297); overrun has the higher AUC for >25% overruns (0.678 vs 0.595) and transfers to greenfield briefs, where nearly every clause is new_build. Decided on training data only. |
| 27 | 2026-10-17 13:54 | `sip_jev_holdout` | `` | jev-1.13.0 | human: MAE 56.92 h, PRED(25) 23.7%, P10–P90 —<br>size-only: MAE 52.11 h, PRED(25) 16.4%, P10–P90 76.3<br>jev:overrun@v1: MAE 52.65 h, PRED(25) 19.6%, P10–P90 76.7 | Held-out test 2011-2014. Jev overrun@v1 tertile split fitted on training tasks only. MAE gain vs size-only -0.54 h (95% CI [-1.91, 0.73]); test Spearman 0.197, AUC 0.62. |
| 28 | 2026-10-17 14:01 | `round5_rules_before` | `74c1409f3b` | — | rules: kind 21/24, tentative 1/6, false 0 | Round 5: 24 new clauses (labels committed before the run). Rules as shipped incl. round-4 fixes: first held-out check of those fixes. |
| 29 | 2026-10-17 14:02 | `round5_heldout` | `74c1409f3b` | jev-1.13.0 | rules: kind 21/24, tentative 1/6, false 0<br>jev: kind 18/24, tentative 6/6, false 0<br>shipped: kind 21/24, tentative 5/6, false 0 | Round 5 held-out: 24 new clauses (VN + EN), labels committed before any reader ran. Shipped reader = rules + Jev via the 9-key pool. (scored 24/24, API calls 10, credits left 108) |
| 30 | 2026-10-17 14:03 | `round1_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 29/31, tentative 6/6, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 31 | 2026-10-17 14:03 | `round2_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 28/30, tentative 5/5, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 32 | 2026-10-17 14:03 | `round3_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 23/25, tentative 4/4, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 33 | 2026-10-17 14:03 | `round4_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 16/16, tentative 5/5, false 0 | Regression check after round-5 rule fixes (round 5 = dev, derived from it). |
| 34 | 2026-10-17 14:03 | `round5_rules_after_round5_fixes` | `dd175964ab` | — | rules: kind 24/24, tentative 6/6, false 0 | Round 5 after its own rule fixes: dev, not evidence. |
| 35 | 2026-10-17 14:03 | `promise_after_round5_fixes` | `dd175964ab` | — | odd projects: retention 100.0%, performance recall 51.6%, security recall 77.4%, false tentative 0/392 | Regression check after round-5 rule fixes. |
| 36 | 2026-10-17 14:03 | `round5_shipped_final` | `dd175964ab` | jev-1.13.0 | rules: kind 24/24, tentative 6/6, false 0<br>jev: kind 18/24, tentative 6/6, false 0<br>shipped: kind 24/24, tentative 6/6, false 0 | Final shipped reader (rules after round-5 fixes + cached Jev answers, no API calls) on round 5: dev, not held-out. (scored 24/24, API calls 0, credits left None) |
| 37 | 2026-10-17 14:51 | `itemlet_replication_interim` | `` | jev-1.13.0 | read 465/2032: high/low median ratio x1.145, Spearman 0.053, AUC 0.559<br>MAE raw 18.64 h → with SiP factors 19.86 h (gain CI [-1.81, -0.66]) | Independent replication on Itemlet (30 open-source Jira projects), SiP thresholds and factors unchanged, protocol committed before the run. Read 465/2032 (random prefix). |
| 38 | 2026-10-17 14:52 | `sip_operational_replay` | `` | jev-1.13.0 (cached) | human: MAE 4.33 h, PRED(25) 51.5%, SA 56.3%, P10–P90 —<br>frozen: MAE 3.82 h, PRED(25) 51.1%, SA 61.4%, P10–P90 85.3, Wilcoxon p 0.00208<br>online: MAE 3.85 h, PRED(25) 50.9%, SA 61.1%, P10–P90 85.0, Wilcoxon p 0.00552<br>dev>=20h human: MAE 26.89 h, PRED(25) 27.6%, SA 18.5%, P10–P90 —<br>dev>=20h online: MAE 23.81 h, PRED(25) 21.9%, SA 27.8%, P10–P90 81.0, Wilcoxon p 0.0155<br>dev>=20h online+jev: MAE 24.7 h, PRED(25) 22.9%, SA 25.1%, P10–P90 81.0, Wilcoxon p 0.0106 | Production replay: every estimate uses only work completed before its estimate date. Online = refit daily (what the app does); frozen = fitted on work completed before 2011. |
| 39 | 2026-10-17 14:56 | `round6_rules_before` | `f0608239a4` | — | rules: kind 10/13, tentative 2/3, false 0 | Round 6 (private-equity onboarding, 13 new clauses, labels committed in 60fbfe8 before the run). Rules incl. round-5 fixes: first held-out check of those fixes. |
| 40 | 2026-10-17 16:54 | `itemlet_replication_final` | `` | jev-1.13.0 | read 2032/2032: high/low median ratio x1.128, Spearman 0.054, AUC 0.535<br>MAE raw 18.35 h → with SiP factors 19.54 h (gain CI [-1.45, -0.95]) | Independent replication on Itemlet (37 open-source Jira projects), SiP thresholds and factors unchanged, protocol committed before the run. Read 2032/2032 (random prefix). |
| 41 | 2026-10-17 16:55 | `round6_heldout` | `f0608239a4` | jev-1.13.0 | rules: kind 10/13, tentative 2/3, false 0<br>jev: kind 13/13, tentative 3/3, false 0<br>shipped: kind 12/13, tentative 3/3, false 0 | Round 6 held-out: private-equity investor onboarding (challenge host's domain), 13 new clauses, labels committed in 60fbfe8 before any reader ran. Jev jev-1.13.0 via TypeSafe direct (same pinned model). (scored 13/13, API calls 2, credits left None) |
<!-- AUTO:journal:end -->
