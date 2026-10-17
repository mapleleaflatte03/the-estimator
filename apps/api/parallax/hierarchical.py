"""Hierarchical (partially pooled) correction of human estimates, learned from actual hours.

What a senior estimator knows implicitly ("this project always runs over", "this person
under-estimates small tasks", "bug fixes overrun more than enhancements") is learned here as
additive effects on log(actual / estimate), one per group of each factor, each shrunk towards 0
in proportion to how little data the group has (posterior-mean style, `n / (n + k)`). Effects
are fitted by backfitting. Forecast = estimate x exp(effects) x residual quantiles, with residual
quantiles per estimate-size bucket (errors on small and large tasks differ in spread).

The same mechanism drives the app's learning from your own actuals (per project type, per kind
of work); this module is validated on real data in scripts/sip_model_search.py.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np

Features = dict[str, str]


@dataclass
class HierarchicalRatioModel:
    factors: tuple[str, ...]
    shrinkage: float = 20.0
    iterations: int = 8
    intercept: float = 0.0
    effects: dict[str, dict[str, float]] = field(default_factory=dict)
    residuals_by_bucket: dict[str, np.ndarray] = field(default_factory=dict)
    residuals_pooled: np.ndarray = field(default_factory=lambda: np.zeros(1))
    bucket_of: Optional[Callable[[float], str]] = None

    def _effect(self, x: Features) -> float:
        return self.intercept + sum(self.effects.get(f, {}).get(x.get(f, ""), 0.0) for f in self.factors)

    def fit(self, rows: Sequence[tuple[float, float, Features]]) -> "HierarchicalRatioModel":
        """rows: (estimate_hours, actual_hours, features). Never pass evaluation data."""
        y = np.array([math.log(a / e) for e, a, _ in rows])
        xs = [x for _, _, x in rows]
        self.intercept = float(np.median(y))
        self.effects = {f: {} for f in self.factors}
        for _ in range(self.iterations):
            for f in self.factors:
                partial = y - np.array([self._effect(x) - self.effects[f].get(x.get(f, ""), 0.0) for x in xs])
                sums: dict[str, float] = defaultdict(float)
                counts: dict[str, int] = defaultdict(int)
                for x, r in zip(xs, partial):
                    g = x.get(f, "")
                    sums[g] += r
                    counts[g] += 1
                self.effects[f] = {g: sums[g] / (counts[g] + self.shrinkage) for g in sums}
        resid = y - np.array([self._effect(x) for x in xs])
        self.residuals_pooled = np.sort(resid)
        by: dict[str, list[float]] = defaultdict(list)
        if self.bucket_of:
            for (e, _, _), r in zip(rows, resid):
                by[self.bucket_of(e)].append(r)
        self.residuals_by_bucket = {b: np.sort(v) for b, v in by.items() if len(v) >= 30}
        return self

    def predict(self, estimate: float, x: Features, probs: Sequence[float] = (0.1, 0.5, 0.9)) -> list[float]:
        res = self.residuals_by_bucket.get(self.bucket_of(estimate)) if self.bucket_of else None
        res = res if res is not None else self.residuals_pooled
        q = np.quantile(res, probs)
        return [float(estimate * math.exp(self._effect(x) + r)) for r in q]
