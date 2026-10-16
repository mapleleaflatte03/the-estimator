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

## Final result (held-out numbers only)

| Claim | Evidence |
| --- | --- |
| Learning from actual hours makes estimates more accurate | SiP 2011–2014, 2,248 unseen tasks: MAE −10.4%, P10–P90 coverage 82.0% |
| The shipped reader notices what the client has not committed to | Rounds 1, 2 and 4: **15/15** tentative clauses caught vs **5/15** with rules alone, **0** false alarms |
| The shipped reader finds the main kind of work | Rounds 1, 2 and 4: **62/75** vs 59/75 with rules alone |
| Rule fixes generalise | Round 3: 17/25 → 23/25. PROMISE odd projects: 72.7% → 100% kept, performance recall 3.2% → 51.6% |

## Limitations

- **Clause sets.** The sets were written by the developer in the style of client briefs, not taken from real client
  documents. They total 102 clauses, which is small.
- **Round-4 fixes.** They have no held-out confirmation yet; that needs a round 5 of fresh clauses and AI credits.
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
<!-- AUTO:journal:end -->
