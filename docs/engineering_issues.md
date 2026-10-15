# Review of pasted Day 0 proposal

Key corrections implemented:

- The pasted Python text contained concatenated imports, missing newlines and malformed arithmetic after markdown conversion.
- A Pydantic evidence list only means "a quote exists". We added explicit quote-in-source checks; semantic validity still needs review.
- The pasted log-normal comment said `median=1` but `mu=-sigma^2/2` yields **mean=1**; the code and comment now agree.
- The original forecast omitted P10 despite benchmark code expecting a prediction interval.
- Arbitrary fixed 70/30 blending of a bottom-up estimate with historical medians was removed pending evaluation.
- Shared risk CV is explicit. It is not equivalent to empirically calibrated uncertainty.
- Original calibration gate risked division by zero when baseline MAE is zero and accepted test-set tuning implicitly. The new gate restricts selection to validation only, checks paired case IDs and minimum sample size.
- Requirement-to-task references, dependency links, cycles, and quantile ordering are validated.
- The proposed 'dual-track benchmark' is valid *only* if published tabular benchmarks are not misrepresented as tests of brief reading. Golden briefs are engineering QA, not proof of numeric estimation performance.
- WAPE and MAE have identical ordering on one fixed dataset: WAPE = MAE * n / sum(actuals) * 100. Don't claim them as independent gating evidence.
