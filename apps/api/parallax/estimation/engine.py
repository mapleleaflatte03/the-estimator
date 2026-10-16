"""Deterministic Monte Carlo for bottom-up estimates.

Per-item Beta-PERT spread is an engine assumption. The shared (systemic)
factor is either drawn from an empirical ratio pool (real feature-level
actual/estimate ratios, see parallax.empirical) or, when no pool is given,
from an assumed mean-one lognormal.
"""
import math
from collections.abc import Sequence

import numpy as np

from parallax.schemas import HistogramBin, ProbabilisticForecast, WorkItem

CURVE_PERCENTILES = tuple(range(5, 100, 5))


def _pert_mean(item: WorkItem) -> float:
    return (item.optimistic_hours + 4.0 * item.most_likely_hours + item.pessimistic_hours) / 6.0


def critical_path(wbs: Sequence[WorkItem]) -> tuple[float, list[str]]:
    """Longest chain of dependent work (PERT means). Adding people cannot beat it."""
    by_id = {w.item_id: w for w in wbs}
    memo: dict[str, tuple[float, list[str]]] = {}
    visiting: set[str] = set()

    def longest(item_id: str) -> tuple[float, list[str]]:
        if item_id not in memo:
            visiting.add(item_id)
            item = by_id[item_id]
            best: tuple[float, list[str]] = (0.0, [])
            for dep in item.dependencies:
                if dep in by_id and dep not in visiting:  # cycles are rejected later by the schema
                    cand = longest(dep)
                    if cand[0] > best[0]:
                        best = cand
            memo[item_id] = (best[0] + _pert_mean(item), [*best[1], item_id])
            visiting.discard(item_id)
        return memo[item_id]

    paths = [longest(w.item_id) for w in wbs]
    hours, chain = max(paths, key=lambda p: p[0]) if paths else (0.0, [])
    return round(hours, 1), chain


def simulate_totals(
    wbs: Sequence[WorkItem],
    systemic_uncertainty_cv: float = 0.15,
    calibration_multiplier: float = 1.0,
    n_simulations: int = 10_000,
    seed: int = 42,
    systemic_ratio_pool: Sequence[float] | None = None,
) -> np.ndarray:
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

    if systemic_ratio_pool is not None and len(systemic_ratio_pool) > 0:
        pool = np.asarray(systemic_ratio_pool, dtype=float)
        if not np.all(np.isfinite(pool)) or np.any(pool <= 0):
            raise ValueError("Systemic ratio pool must contain positive finite ratios")
        shock = rng.choice(pool, size=n_simulations, replace=True)
    else:
        # Mean = 1.0, not median = 1.0. Shared shock induces positive correlation.
        sigma = math.sqrt(math.log1p(systemic_uncertainty_cv**2))
        shock = rng.lognormal(mean=-0.5 * sigma**2, sigma=sigma, size=n_simulations)
    return total * shock * calibration_multiplier


def run_correlated_monte_carlo(
    wbs: Sequence[WorkItem],
    systemic_uncertainty_cv: float = 0.15,
    calibration_multiplier: float = 1.0,
    n_simulations: int = 10_000,
    seed: int = 42,
) -> dict[str, float]:
    samples = simulate_totals(
        wbs,
        systemic_uncertainty_cv=systemic_uncertainty_cv,
        calibration_multiplier=calibration_multiplier,
        n_simulations=n_simulations,
        seed=seed,
    )
    percentiles = np.percentile(samples, [10, 50, 80, 90])
    return {
        "p10": float(percentiles[0]),
        "p50": float(percentiles[1]),
        "p80": float(percentiles[2]),
        "p90": float(percentiles[3]),
        "mean": float(np.mean(samples)),
        "std": float(np.std(samples)),
    }


def _histogram(samples: np.ndarray, bins: int = 40) -> list[HistogramBin]:
    """Histogram over P0.5..P97.5; shares are of *all* samples, so the long
    right tail is reported separately (tail_*) instead of being clipped."""
    lo, hi = np.percentile(samples, [0.5, 97.5])
    counts, edges = np.histogram(samples[(samples >= lo) & (samples <= hi)], bins=bins, range=(lo, hi))
    total = len(samples) or 1
    return [
        HistogramBin(start=round(float(edges[i]), 2), end=round(float(edges[i + 1]), 2),
                     share=round(float(counts[i] / total), 5))
        for i in range(len(counts))
    ]


def synthesize_forecast(
    wbs: Sequence[WorkItem],
    comparable_actual_hours: Sequence[float] | None = None,
    calibration_multiplier: float = 1.0,
    systemic_uncertainty_cv: float = 0.15,
    seed: int = 42,
    systemic_ratio_pool: Sequence[float] | None = None,
    uncertainty_source: str | None = None,
) -> ProbabilisticForecast:
    samples = simulate_totals(
        wbs,
        systemic_uncertainty_cv=systemic_uncertainty_cv,
        calibration_multiplier=calibration_multiplier,
        seed=seed,
        systemic_ratio_pool=systemic_ratio_pool,
    )
    p10, p50, p80, p90 = (float(x) for x in np.percentile(samples, [10, 50, 80, 90]))
    curve = np.percentile(samples, CURVE_PERCENTILES)
    bu_p50 = p50
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
        n = len(comparable_actual_hours) if comparable_actual_hours else 0
        warning = (
            f"Insufficient comparable historical evidence ({n} completed project(s) of this type; "
            "need at least 5)"
        )

    if uncertainty_source is None:
        uncertainty_source = (
            f"Beta-PERT per item x empirical systemic ratio pool (n={len(systemic_ratio_pool)})"
            if systemic_ratio_pool
            else f"Beta-PERT per item x assumed lognormal shock (CV={systemic_uncertainty_cv})"
        )

    cp_hours, cp_ids = critical_path(wbs)
    # Do not silently blend separate forecasts at arbitrary 70/30 weights.
    return ProbabilisticForecast(
        p10_hours=round(p10, 2),
        p50_hours=round(p50, 2),
        p80_hours=round(p80, 2),
        p90_hours=round(p90, 2),
        mean_hours=round(float(np.mean(samples)), 2),
        std_hours=round(float(np.std(samples)), 2),
        bottom_up_p50=round(bu_p50, 2),
        reference_class_p50=round(reference, 2) if reference is not None else None,
        divergence_warning=warning,
        insufficient_historical_evidence=historical_insufficient,
        calibration_multiplier=round(calibration_multiplier, 4),
        uncalibrated_p50_hours=round(p50 / calibration_multiplier, 2),
        uncertainty_source=uncertainty_source,
        n_simulations=len(samples),
        percentile_curve=[[float(p), round(float(h), 2)] for p, h in zip(CURVE_PERCENTILES, curve)],
        histogram=_histogram(samples),
        p99_hours=round(float(np.percentile(samples, 99)), 2),
        max_hours=round(float(np.max(samples)), 2),
        tail_start_hours=round(float(np.percentile(samples, 97.5)), 2),
        critical_path_hours=cp_hours,
        critical_path_ids=cp_ids,
    )
