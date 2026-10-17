"""Adaptive conformal intervals (Gibbs & Candes 2021, "Adaptive Conformal Inference Under Distribution Shift").

An interval at nominal level 1 - alpha is drawn from the empirical ratio distribution, but the
level actually used, alpha_t, is adjusted every time an outcome becomes known:

    alpha_{t+1} = alpha_t + gamma * (alpha - miss_t)

If too many actuals fall outside, alpha_t shrinks and intervals widen; if too few, they narrow.
Long-run miss rate converges to alpha regardless of drift. One state per group (e.g. size bucket),
so large tasks get their own correction.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AdaptiveLevel:
    target_miss: float = 0.2  # P10-P90 interval
    gamma: float = 0.01
    alpha: dict[str, float] = field(default_factory=dict)
    updates: dict[str, int] = field(default_factory=dict)

    def level(self, group: str) -> float:
        return self.alpha.get(group, self.target_miss)

    def probs(self, group: str) -> tuple[float, float, float]:
        a = min(0.95, max(0.0, self.level(group)))
        return (a / 2, 0.5, 1 - a / 2)

    def update(self, group: str, low: float, high: float, actual: float) -> None:
        miss = 0.0 if low <= actual <= high else 1.0
        self.alpha[group] = self.level(group) + self.gamma * (self.target_miss - miss)
        self.updates[group] = self.updates.get(group, 0) + 1
