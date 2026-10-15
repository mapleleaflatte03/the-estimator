"""Service orchestrator for PARALLAX.

Coordinates Project lifecycle, EstimateVersion creation, Active Clarification,
and the actuals -> calibration feedback loop with strict provenance and
version immutability.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from . import empirical
from .evaluation.benchmark import PredictionRecord, evaluate_predictions
from .extractor import MODEL_TAG, extract_scope_and_wbs
from .schemas import (
    ActualWork,
    CalibrationObservation,
    CalibrationState,
    EstimateVersion,
    EvaluationRun,
    Project,
)
from .storage import StorageRepository

MULTIPLIER_BOUNDS = (0.5, 2.0)


def shrunk_multiplier(log_ratios: list[float], prior_strength: float) -> float:
    """Posterior-mean style estimate of the bias multiplier.

    Shrinks the mean log(actual / uncalibrated P50) towards 0 (multiplier 1.0)
    with `prior_strength` pseudo-observations, so one project can move the
    multiplier but cannot swing it to an extreme.
    """
    if not log_ratios:
        return 1.0
    m = math.exp(sum(log_ratios) / (len(log_ratios) + prior_strength))
    return min(MULTIPLIER_BOUNDS[1], max(MULTIPLIER_BOUNDS[0], m))


class ParallaxService:
    def __init__(self, repository: StorageRepository, use_empirical_data: bool = True):
        self.repo = repository
        self.use_empirical_data = use_empirical_data

    @property
    def calibration_multiplier(self) -> float:
        return self.repo.get_calibration().multiplier

    def _systemic_pool(self) -> Optional[tuple[float, ...]]:
        if not self.use_empirical_data:
            return None
        try:
            return empirical.systemic_ratio_pool()
        except FileNotFoundError:
            return None

    def _comparable_hours(self, project: Project) -> Optional[list[float]]:
        cases = self.repo.list_historical_cases(domain=project.project_type)
        cases = [c for c in cases if c.case_id != project.project_id]
        return [c.actual_hours for c in cases] or None

    def _build_version(self, project: Project, answers: dict[str, bool]) -> EstimateVersion:
        existing = self.repo.get_versions(project.project_id)
        return extract_scope_and_wbs(
            project_id=project.project_id,
            brief_text=project.brief_text,
            source_docs=project.documents,
            clarification_answers=answers,
            version_id=f"v{len(existing) + 1}",
            parent_version_id=existing[-1].version_id if existing else None,
            calibration_multiplier=self.calibration_multiplier,
            historical_cases=self._comparable_hours(project),
            systemic_ratio_pool=self._systemic_pool(),
        )

    def create_project(
        self,
        title: str,
        brief_text: str,
        project_type: str = "custom_software",
        documents: Optional[dict[str, str]] = None,
    ) -> Project:
        project = Project(
            project_id=f"PRJ-{uuid.uuid4().hex[:8].upper()}",
            title=title,
            project_type=project_type,
            brief_text=brief_text,
            documents=documents or {},
            status="intake",
        )
        return self.repo.save_project(project)

    def estimate_project(self, project_id: str) -> EstimateVersion:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        existing = self.repo.get_versions(project_id)
        answers = dict(existing[-1].clarification_answers) if existing else {}
        return self.repo.add_version(self._build_version(project, answers))

    def answer_clarification(
        self,
        project_id: str,
        question_id: str,
        answer: bool,
        notes: Optional[str] = None,
    ) -> EstimateVersion:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        existing = self.repo.get_versions(project_id)
        if not existing:
            raise ValueError("Cannot clarify before generating initial estimate")
        parent = existing[-1]
        if question_id not in {q.question_id for q in parent.clarifications}:
            raise ValueError(f"Unknown clarification question {question_id}")
        # Answers accumulate across versions; a later answer overrides an earlier one.
        answers = {**parent.clarification_answers, question_id: answer}
        version = self.repo.add_version(self._build_version(project, answers))
        project.status = "clarified"
        self.repo.save_project(project)
        return version

    def record_actuals(
        self,
        project_id: str,
        actual_hours: float,
        item_actuals: Optional[dict[str, float]] = None,
        deviation_reasons: Optional[list[str]] = None,
    ) -> dict:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        versions = self.repo.get_versions(project_id)
        if not versions:
            raise ValueError("No estimate version found to compare against actuals")

        # Accuracy is judged against the estimate that was actually committed
        # (the latest version at completion time), never a post-hoc rewrite.
        baseline = versions[-1]
        actual = ActualWork(
            actual_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
            project_id=project_id,
            version_id=baseline.version_id,
            actual_hours=actual_hours,
            item_actuals=item_actuals or {},
            deviation_reasons=deviation_reasons or [],
        )
        self.repo.add_actual_work(actual)

        fc = baseline.forecast
        uncalibrated = fc.uncalibrated_p50_hours or fc.p50_hours / fc.calibration_multiplier
        state = self.repo.get_calibration()
        before = state.multiplier
        observations = [o for o in state.observations if o.project_id != project_id]
        observations.append(
            CalibrationObservation(
                project_id=project_id,
                version_id=baseline.version_id,
                project_type=project.project_type,
                uncalibrated_p50=uncalibrated,
                actual_hours=actual_hours,
            )
        )
        after = shrunk_multiplier([o.log_ratio for o in observations], state.prior_strength)
        self.repo.save_calibration(
            CalibrationState(
                multiplier=after,
                prior_strength=state.prior_strength,
                observations=observations,
                updated_at=datetime.now(timezone.utc),
            )
        )

        delta = actual_hours - fc.p50_hours
        initial = versions[0].forecast
        return {
            "actual_id": actual.actual_id,
            "project_id": project_id,
            "baseline_version_id": baseline.version_id,
            "estimated_p50": fc.p50_hours,
            "estimated_p10": fc.p10_hours,
            "estimated_p90": fc.p90_hours,
            "actual_hours": actual_hours,
            "delta_hours": round(delta, 2),
            "percentage_error": round(delta / actual_hours * 100, 2),
            "inside_p10_p90": fc.p10_hours <= actual_hours <= fc.p90_hours,
            "initial_version": {
                "version_id": versions[0].version_id,
                "estimated_p50": initial.p50_hours,
                "percentage_error": round((actual_hours - initial.p50_hours) / actual_hours * 100, 2),
                "inside_p10_p90": initial.p10_hours <= actual_hours <= initial.p90_hours,
            },
            "calibration": {
                "multiplier_before": round(before, 4),
                "multiplier_after": round(after, 4),
                "n_observations": len(observations),
                "prior_strength": state.prior_strength,
                "applies_to": "new estimates and re-estimates; existing versions stay unchanged",
            },
        }

    def calibration_status(self) -> dict:
        state = self.repo.get_calibration()
        return {
            "multiplier": round(state.multiplier, 4),
            "n_observations": len(state.observations),
            "prior_strength": state.prior_strength,
            "updated_at": state.updated_at,
            "observations": [
                {
                    "project_id": o.project_id,
                    "project_type": o.project_type,
                    "version_id": o.version_id,
                    "uncalibrated_p50": round(o.uncalibrated_p50, 2),
                    "actual_hours": o.actual_hours,
                    "ratio": round(math.exp(o.log_ratio), 3),
                    "recorded_at": o.recorded_at,
                }
                for o in state.observations
            ],
        }

    def _in_app_evaluation(self) -> dict:
        """Leave-one-out check of the learned multiplier on this workspace's actuals."""
        state = self.repo.get_calibration()
        obs = state.observations
        result: dict = {"n_observations": len(obs), "multiplier": round(state.multiplier, 4)}
        if len(obs) < 2:
            result["status"] = "insufficient_data"
            result["message"] = "Need actuals for at least 2 completed projects for a leave-one-out check."
            return result
        raw, loo = [], []
        for i, o in enumerate(obs):
            others = [x.log_ratio for j, x in enumerate(obs) if j != i]
            m = shrunk_multiplier(others, state.prior_strength)
            raw.append(PredictionRecord(o.project_id, o.actual_hours, o.uncalibrated_p50, o.uncalibrated_p50, o.uncalibrated_p50))
            p = o.uncalibrated_p50 * m
            loo.append(PredictionRecord(o.project_id, o.actual_hours, p, p, p))
        before = evaluate_predictions("uncalibrated", raw, split="validation")
        after = evaluate_predictions("loo-calibrated", loo, split="validation")
        result.update(
            status="ok",
            uncalibrated_mae=round(before.mae, 2),
            calibrated_mae=round(after.mae, 2),
            uncalibrated_mdape=round(before.mdape, 2),
            calibrated_mdape=round(after.mdape, 2),
            improved=after.mae < before.mae,
        )
        return result

    def run_benchmark_suite(self) -> dict:
        """Real-data benchmark (SiP temporal holdout) plus this workspace's own actuals."""
        sip = empirical.run_sip_benchmark()
        in_app = self._in_app_evaluation()
        cal = sip["holdout"]["calibrated"]
        run = EvaluationRun(
            run_id=f"RUN-{uuid.uuid4().hex[:8].upper()}",
            dataset_name=f"{sip['dataset']['name']} @ {sip['dataset']['source_commit'][:7]}",
            split="test",
            model_tag="SiP-ratio-quantile-v1",
            metrics={k: v for k, v in cal.items() if isinstance(v, (int, float))},
            gate_decision={"in_app": in_app},
        )
        self.repo.add_evaluation_run(run)
        return {"run_id": run.run_id, "created_at": run.created_at, "sip": sip, "in_app": in_app}

    def system_status(self) -> dict:
        try:
            summary = empirical.dataset_summary()
            dataset = {
                "available": True,
                "name": summary["name"],
                "n_tasks": summary["n_tasks"],
                "n_aggregates": summary["n_aggregates"],
                "period": summary["period"],
                "license": summary["license"],
            }
        except FileNotFoundError as exc:
            dataset = {"available": False, "error": str(exc)}
        runs = self.repo.list_evaluation_runs()
        last = next((r for r in reversed(runs) if r.model_tag == "SiP-ratio-quantile-v1"), None)
        return {
            "model_tag": MODEL_TAG,
            "n_simulations": 10_000,
            "dataset": dataset,
            "calibration": {
                "multiplier": round(self.calibration_multiplier, 4),
                "n_observations": len(self.repo.get_calibration().observations),
            },
            "reference_class_projects": len(self.repo.list_historical_cases()),
            "last_benchmark": (
                {"run_id": last.run_id, "created_at": last.created_at, "metrics": last.metrics}
                if last
                else None
            ),
        }
