"""Toy candidate generation using *training* actuals only.

A candidate must still pass validation and untouched test evaluation.
"""
from statistics import median

from .evaluation.benchmark import PredictionRecord


def propose_multiplier(training_records: list[PredictionRecord], lower=0.5, upper=2.0) -> float:
    if not training_records:
        raise ValueError("At least one training record is required")
    ratios = [r.actual_hours / r.pred_p50 for r in training_records if r.pred_p50 > 0]
    if len(ratios) != len(training_records):
        raise ValueError("Training point forecasts must be positive")
    return max(lower, min(upper, median(ratios)))


def apply_multiplier(records: list[PredictionRecord], multiplier: float) -> list[PredictionRecord]:
    if multiplier <= 0:
        raise ValueError("Multiplier must be positive")
    return [
        PredictionRecord(
            case_id=r.case_id,
            actual_hours=r.actual_hours,
            pred_p50=r.pred_p50 * multiplier,
            pred_low=r.pred_low * multiplier,
            pred_high=r.pred_high * multiplier,
        )
        for r in records
    ]
