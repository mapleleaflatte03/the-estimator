"""Deterministic Monte Carlo for bottom-up estimates.

Risk distributions are explicit assumptions, not empirically calibrated
probabilities until their parameters have been validated against actuals.
"""
import math
from collections.abc import Sequence

import numpy as np

from parallax.schemas import ProbabilisticForecast, WorkItem


def run_correlated_monte_carlo(
    wbs: Sequence[WorkItem],
    systemic_uncertainty_cv: float = 0.15,
    calibration_multiplier: float = 1.0,
    n_simulations: int = 10_000,
    seed: int = 42,
) -> dict[str, float]:
    if not wbs:
        raise ValueError("At least one work item is needed")
    if n_simulations < 1_000:
        raise ValueError("Use >= 1,000 simulations for stable illustrative percentiles")
    if not math.isfinite(systemic_uncertainty_cv) or systemic_uncertainty_cv < 0:
        raise ValueError("Systemic uncertainty CV must be nonnegative and finite")
    if not math.isfinite(calibration_multiplier) or calibration_multiplier <= 0:
        raise ValueError("Calibration multiplier must be positive and finite")

    rng = np.random.default_rng(seed)
    total = np.zeros(n_simulations)
    for item in wbs:
        o, m, p = item.optimistic_hours, item.most_likely_hours, item.pessimistic_hours
        if p == o:
            task = np.full(n_simulations, m)
        else:
            alpha = 1.0 + 4.0 * (m - o) / (p - o)
            beta = 1.0 + 4.0 * (p - m) / (p - o)
            task = o + rng.beta(alpha, beta, size=n_simulations) * (p - o)
        total += task

    # Mean = 1.0, not median = 1.0. Shared shock induces positive correlation.
    sigma = math.sqrt(math.log1p(systemic_uncertainty_cv**2))
    shock = rng.lognormal(mean=-0.5 * sigma**2, sigma=sigma, size=n_simulations)
    samples = total * shock * calibration_multiplier
    percentiles = np.percentile(samples, [10, 50, 80, 90])
    return {
        "p10": float(percentiles[0]),
        "p50": float(percentiles[1]),
        "p80": float(percentiles[2]),
        "p90": float(percentiles[3]),
        "mean": float(np.mean(samples)),
        "std": float(np.std(samples)),
    }


def synthesize_forecast(
    wbs: Sequence[WorkItem],
    comparable_actual_hours: Sequence[float] | None = None,
    calibration_multiplier: float = 1.0,
    systemic_uncertainty_cv: float = 0.15,
    seed: int = 42,
) -> ProbabilisticForecast:
    mc = run_correlated_monte_carlo(
        wbs,
        systemic_uncertainty_cv=systemic_uncertainty_cv,
        calibration_multiplier=calibration_multiplier,
        seed=seed,
    )
    bu_p50 = mc["p50"]
    reference = None
    warning = None
    historical_insufficient = True
    if comparable_actual_hours:
        cases = np.asarray(comparable_actual_hours, dtype=float)
        if not np.all(np.isfinite(cases)) or np.any(cases <= 0):
            raise ValueError("Historical actual hours must be positive and finite")
        # A set of cases must be filtered for comparability *before* this function.
        if len(cases) >= 5:
            historical_insufficient = False
            reference = float(np.median(cases))
            gap = abs(bu_p50 - reference) / reference
            if gap > 0.30:
                warning = (
                    f"Bottom-up/reference-class P50 disagree by {gap:.0%}; "
                    "check scope and historical comparability"
                )
    if historical_insufficient:
        warning = "Insufficient comparable historical evidence (need at least 5 cases)"

    # Do not silently blend separate forecasts at arbitrary 70/30 weights.
    return ProbabilisticForecast(
        p10_hours=round(mc["p10"], 2),
        p50_hours=round(mc["p50"], 2),
        p80_hours=round(mc["p80"], 2),
        p90_hours=round(mc["p90"], 2),
        mean_hours=round(mc["mean"], 2),
        std_hours=round(mc["std"], 2),
        bottom_up_p50=round(bu_p50, 2),
        reference_class_p50=round(reference, 2) if reference is not None else None,
        divergence_warning=warning,
        insufficient_historical_evidence=historical_insufficient,
    )
