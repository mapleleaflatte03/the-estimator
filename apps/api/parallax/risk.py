"""Turn Jev's "this will take longer than it looks" reading into hours, using real outcomes.

Prior: scripts/sip_jev_study.py asked Jev the same question (OVERRUN_Q) about 798
real SiP development tasks. On the training years, tasks were split into three
groups by Jev's probability; each group's median actual/estimate ratio, divided
by that of the low-risk group, is the group's factor: low-risk work keeps its
hours and flagged work gets the extra overrun measured on real tasks. The later,
unseen years confirmed the ordering (scripts/sip_jev_study.py report).

Learning: when a finished project's hours are recorded per requirement, each
requirement becomes an observation (estimated vs actual hours). Group factors and
per-component factors are then pulled from the SiP prior towards this
workspace's own record with partial pooling, so a few projects nudge the
numbers and many projects take over.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

STUDY_PATH = Path(__file__).resolve().parents[3] / "datasets" / "eval" / "sip_jev_study.json"
PRIOR_STRENGTH = 4.0  # pseudo-observations behind each prior factor
FACTOR_BOUNDS = (0.5, 2.0)
GROUP_LABELS = ("low", "medium", "high")


@dataclass(frozen=True)
class RiskPrior:
    thresholds: tuple[float, float]
    factors: tuple[float, float, float]
    n_train: tuple[int, int, int]
    question: str
    test_ratio_p50: tuple[Optional[float], ...]

    def group(self, p: float) -> int:
        return int(p > self.thresholds[0]) + int(p > self.thresholds[1])


@lru_cache(maxsize=1)
def sip_prior() -> Optional[RiskPrior]:
    try:
        report = json.loads(STUDY_PATH.read_text(encoding="utf-8"))["report"]
    except (OSError, ValueError, KeyError):
        return None
    groups = sorted(report["groups_train"], key=lambda g: g["group"])
    base = groups[0]["ratio_p50"]
    test = {g["group"]: g["test_ratio_p50"] for g in report.get("groups_test", [])}
    return RiskPrior(
        thresholds=tuple(report["thresholds_from_train"]),
        factors=tuple(round(g["ratio_p50"] / base, 4) for g in groups),
        n_train=tuple(g["n_train"] for g in groups),
        question=report["question"],
        test_ratio_p50=tuple(test.get(g) for g in range(3)),
    )


def _bounded(x: float) -> float:
    return min(FACTOR_BOUNDS[1], max(FACTOR_BOUNDS[0], x))


def pooled_factor(log_ratios: list[float], prior: float = 1.0, strength: float = PRIOR_STRENGTH) -> float:
    """Posterior-mean style: n observations against `strength` pseudo-observations at the prior."""
    if not log_ratios:
        return prior
    return _bounded(math.exp((sum(log_ratios) + strength * math.log(prior)) / (len(log_ratios) + strength)))


@dataclass
class Adjustments:
    """Everything learned that changes item hours for a new estimate."""

    group_factors: tuple[float, float, float]
    group_observations: tuple[int, int, int]
    component_factors: dict[str, float]
    component_observations: dict[str, int]
    prior: Optional[RiskPrior]

    def group_of(self, p: Optional[float]) -> Optional[int]:
        if p is None or self.prior is None:
            return None
        return self.prior.group(p)

    def as_dict(self) -> dict:
        return {
            "question": self.prior.question if self.prior else None,
            "thresholds": list(self.prior.thresholds) if self.prior else None,
            "sip_factors": list(self.prior.factors) if self.prior else None,
            "sip_train_counts": list(self.prior.n_train) if self.prior else None,
            "sip_test_ratio_p50": list(self.prior.test_ratio_p50) if self.prior else None,
            "group_factors": list(self.group_factors),
            "group_observations": list(self.group_observations),
            "component_factors": self.component_factors,
            "component_observations": self.component_observations,
        }


def learn(observations: Iterable) -> Adjustments:
    """observations: objects with .risk_group (0-2 or None), .components (list[str]), .log_ratio.

    Group factors are relative: the workspace's overall bias is already learned by the
    project-level multiplier, so each group's mean log-ratio is centred on the mean of all
    requirement observations before being pooled with the SiP prior.
    """
    obs = list(observations)
    prior = sip_prior()
    base = prior.factors if prior else (1.0, 1.0, 1.0)
    centre = sum(o.log_ratio for o in obs) / len(obs) if obs else 0.0
    groups, counts = [], []
    for g in range(3):
        rel = [o.log_ratio - centre for o in obs if o.risk_group == g]
        groups.append(round(pooled_factor(rel, base[g]), 4))
        counts.append(len(rel))
    by_comp: dict[str, list[float]] = {}
    for o in obs:
        for c in set(o.components):
            by_comp.setdefault(c, []).append(o.log_ratio - centre)
    comp_factors = {c: round(pooled_factor(v), 4) for c, v in by_comp.items()}
    return Adjustments(tuple(groups), tuple(counts), comp_factors, {c: len(v) for c, v in by_comp.items()}, prior)
