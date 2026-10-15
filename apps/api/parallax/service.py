"""Service orchestrator for PARALLAX.

Coordinates Project lifecycle, EstimateVersion creation, Active Clarification,
and Actuals recalibration with strict provenance and version immutability.
"""
from __future__ import annotations
import uuid
from typing import Optional

from .calibration import propose_multiplier, apply_multiplier
from .evaluation.benchmark import (
    BenchmarkMetrics,
    PredictionRecord,
    calibration_gate_decision,
    evaluate_predictions,
)
from .extractor import extract_scope_and_wbs
from .schemas import (
    ActualWork,
    EstimateVersion,
    EvaluationRun,
    Project,
)
from .storage import StorageRepository


class ParallaxService:
    def __init__(self, repository: StorageRepository):
        self.repo = repository
        self.calibration_multiplier = 1.0

    def create_project(
        self,
        title: str,
        brief_text: str,
        project_type: str = "custom_software",
        documents: Optional[dict[str, str]] = None,
    ) -> Project:
        project_id = f"PRJ-{uuid.uuid4().hex[:8].upper()}"
        docs = documents or {}
        project = Project(
            project_id=project_id,
            title=title,
            project_type=project_type,
            brief_text=brief_text,
            documents=docs,
            status="intake",
        )
        return self.repo.save_project(project)

    def estimate_project(self, project_id: str) -> EstimateVersion:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")

        # Retrieve comparable historical cases for reference-class forecasting
        historical_cases = self.repo.list_historical_cases(
            domain=project.project_type if project.project_type != "custom_software" else None
        )
        comparable_hours = [c.actual_hours for c in historical_cases] if historical_cases else None

        existing_versions = self.repo.get_versions(project_id)
        version_num = len(existing_versions) + 1
        version_id = f"v{version_num}"
        parent_id = existing_versions[-1].version_id if existing_versions else None

        version = extract_scope_and_wbs(
            project_id=project_id,
            brief_text=project.brief_text,
            source_docs=project.documents,
            clarification_answers=None,
            version_id=version_id,
            parent_version_id=parent_id,
            calibration_multiplier=self.calibration_multiplier,
            historical_cases=comparable_hours,
        )

        return self.repo.add_version(version)

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

        existing_versions = self.repo.get_versions(project_id)
        if not existing_versions:
            raise ValueError("Cannot clarify before generating initial estimate")

        parent = existing_versions[-1]
        version_num = len(existing_versions) + 1
        new_version_id = f"v{version_num}"

        # Consolidate previous answers and append new answer
        answers = {question_id: answer}

        historical_cases = self.repo.list_historical_cases(
            domain=project.project_type if project.project_type != "custom_software" else None
        )
        comparable_hours = [c.actual_hours for c in historical_cases] if historical_cases else None

        new_version = extract_scope_and_wbs(
            project_id=project_id,
            brief_text=project.brief_text,
            source_docs=project.documents,
            clarification_answers=answers,
            version_id=new_version_id,
            parent_version_id=parent.version_id,
            calibration_multiplier=self.calibration_multiplier,
            historical_cases=comparable_hours,
        )

        project.status = "clarified"
        self.repo.save_project(project)
        return self.repo.add_version(new_version)

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

        # Rule: Compare against the INITIAL baseline version (v1), not post-hoc modified
        baseline_version = versions[0]
        actual_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"

        actual = ActualWork(
            actual_id=actual_id,
            project_id=project_id,
            version_id=baseline_version.version_id,
            actual_hours=actual_hours,
            item_actuals=item_actuals or {},
            deviation_reasons=deviation_reasons or [],
        )
        self.repo.add_actual_work(actual)

        pred_p50 = baseline_version.forecast.p50_hours
        delta_hours = actual_hours - pred_p50
        pct_error = (delta_hours / actual_hours) * 100

        return {
            "actual_id": actual_id,
            "project_id": project_id,
            "baseline_version_id": baseline_version.version_id,
            "estimated_p50": pred_p50,
            "actual_hours": actual_hours,
            "delta_hours": round(delta_hours, 2),
            "percentage_error": round(pct_error, 2),
            "inside_p10_p90": baseline_version.forecast.p10_hours <= actual_hours <= baseline_version.forecast.p90_hours,
        }

    def run_benchmark_suite(self) -> BenchmarkMetrics:
        """Run benchmark metrics over all known historical cases against baseline predictions."""
        cases = self.repo.list_historical_cases()
        records = []
        for c in cases:
            # Baseline simulation: task count * average task hours
            est_p50 = c.task_count * 12.0
            records.append(
                PredictionRecord(
                    case_id=c.case_id,
                    actual_hours=c.actual_hours,
                    pred_p50=est_p50,
                    pred_low=est_p50 * 0.75,
                    pred_high=est_p50 * 1.35,
                )
            )
        metrics = evaluate_predictions("PARALLAX-Baseline-v1", records, split="validation")
        run = EvaluationRun(
            run_id=f"RUN-{uuid.uuid4().hex[:8].upper()}",
            dataset_name="PARALLAX-Curated-Historical",
            split="validation",
            model_tag="PARALLAX-Baseline-v1",
            metrics={
                "mae": metrics.mae,
                "mdape": metrics.mdape,
                "wape": metrics.wape,
                "pred_25": metrics.pred_25,
                "interval_coverage": metrics.interval_coverage,
                "mean_interval_width": metrics.mean_interval_width,
            },
        )
        self.repo.add_evaluation_run(run)
        return metrics
