"""Thread-safe persistent storage repository for PARALLAX.

Enforces version immutability: EstimateVersions are never overwritten,
only appended as a DAG of versions with parent_version_id links.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

from .schemas import (
    ActualWork,
    CalibrationState,
    EstimateVersion,
    FeedbackEvent,
    EvaluationRun,
    HistoricalCase,
    Project,
    RequirementObservation,
)

logger = logging.getLogger(__name__)


class StorageError(RuntimeError):
    """A workspace could not be read or durably saved."""


class StorageRepository:
    def __init__(self, data_path: Optional[Path] = None):
        self.lock = Lock()
        self.data_path = data_path
        self.projects: dict[str, Project] = {}
        self.versions: dict[str, list[EstimateVersion]] = {}  # project_id -> list[EstimateVersion]
        self.actuals: dict[str, list[ActualWork]] = {}  # project_id -> list[ActualWork]
        self.evaluation_runs: list[EvaluationRun] = []
        self.calibration = CalibrationState()
        self.feedback: list[FeedbackEvent] = []
        self.requirement_observations: list[RequirementObservation] = []
        if self.data_path and self.data_path.exists():
            self._load()

    def save_project(self, project: Project) -> Project:
        with self.lock:
            self.projects[project.project_id] = project.model_copy(deep=True)
            if project.project_id not in self.versions:
                self.versions[project.project_id] = []
            if project.project_id not in self.actuals:
                self.actuals[project.project_id] = []
            self._save()
            return project.model_copy(deep=True)

    def get_project(self, project_id: str) -> Optional[Project]:
        with self.lock:
            project = self.projects.get(project_id)
            return project.model_copy(deep=True) if project else None

    def list_projects(self) -> list[Project]:
        with self.lock:
            return [p.model_copy(deep=True) for p in sorted(self.projects.values(), key=lambda p: p.created_at, reverse=True)]

    def add_version(self, version: EstimateVersion, *, status: str = "estimated",
                    feedback_events: Optional[list[FeedbackEvent]] = None) -> EstimateVersion:
        with self.lock:
            p_id = version.project_id
            if p_id not in self.projects:
                raise KeyError(f"Project {p_id} not found")
            existing = self.versions.get(p_id, [])
            # Enforce immutable version IDs
            if any(v.version_id == version.version_id for v in existing):
                raise ValueError(f"Version {version.version_id} already exists for project {p_id}")
            existing.append(version.model_copy(deep=True))
            self.versions[p_id] = existing
            # Update project pointer
            project = self.projects[p_id]
            project.current_version_id = version.version_id
            project.status = status
            if feedback_events:
                self.feedback.extend(feedback_events)
            self._save()
            return version.model_copy(deep=True)

    def get_versions(self, project_id: str) -> list[EstimateVersion]:
        with self.lock:
            return [v.model_copy(deep=True) for v in self.versions.get(project_id, [])]

    def get_version(self, project_id: str, version_id: str) -> Optional[EstimateVersion]:
        with self.lock:
            for v in self.versions.get(project_id, []):
                if v.version_id == version_id:
                    return v.model_copy(deep=True)
            return None

    def commit_actuals(self, actual: ActualWork, observations: list[RequirementObservation],
                       calibration: CalibrationState) -> None:
        """Commit the outcome and both learning states in one durable write."""
        with self.lock:
            pid = actual.project_id
            if pid not in self.projects:
                raise KeyError(f"Project {pid} not found")
            self.requirement_observations = [
                o for o in self.requirement_observations if o.project_id != pid
            ] + list(observations)
            self.actuals.setdefault(pid, []).append(actual)
            self.projects[pid].status = "actuals_recorded"
            self.calibration = calibration
            self._save()

    def get_actuals(self, project_id: str) -> list[ActualWork]:
        with self.lock:
            return [a.model_copy(deep=True) for a in self.actuals.get(project_id, [])]

    def list_historical_cases(self, domain: Optional[str] = None) -> list[HistoricalCase]:
        """Completed projects in this workspace, i.e. projects with recorded actuals.

        Nothing is seeded: the reference class only contains real outcomes.
        The latest actuals record per project wins.
        """
        with self.lock:
            cases = []
            for pid, acts in self.actuals.items():
                project = self.projects.get(pid)
                if not acts or not project:
                    continue
                if domain and project.project_type != domain:
                    continue
                latest = acts[-1]
                baseline = next(
                    (v for v in self.versions.get(pid, []) if v.version_id == latest.version_id), None
                )
                cases.append(
                    HistoricalCase(
                        case_id=pid,
                        title=project.title,
                        domain=project.project_type,
                        actual_hours=latest.actual_hours,
                        task_count=len(baseline.wbs) if baseline else 1,
                        estimated_p50_hours=baseline.forecast.p50_hours if baseline else None,
                        completed_at=latest.recorded_at,
                        notes="; ".join(latest.deviation_reasons) or None,
                    )
                )
            return sorted(cases, key=lambda c: c.completed_at or datetime.min.replace(tzinfo=timezone.utc))

    def list_feedback(self) -> list[FeedbackEvent]:
        with self.lock:
            return list(self.feedback)

    def list_requirement_observations(self) -> list[RequirementObservation]:
        with self.lock:
            return list(self.requirement_observations)

    def get_calibration(self) -> CalibrationState:
        with self.lock:
            return self.calibration.model_copy(deep=True)

    def add_evaluation_run(self, run: EvaluationRun) -> EvaluationRun:
        with self.lock:
            self.evaluation_runs.append(run)
            self._save()
            return run

    def list_evaluation_runs(self) -> list[EvaluationRun]:
        with self.lock:
            return list(self.evaluation_runs)

    def _save(self) -> None:
        if not self.data_path:
            return
        tmp = self.data_path.with_suffix(".tmp")
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "projects": [p.model_dump(mode="json") for p in self.projects.values()],
                "versions": {
                    pid: [v.model_dump(mode="json") for v in v_list]
                    for pid, v_list in self.versions.items()
                },
                "actuals": {
                    pid: [a.model_dump(mode="json") for a in a_list]
                    for pid, a_list in self.actuals.items()
                },
                "evaluation_runs": [r.model_dump(mode="json") for r in self.evaluation_runs],
                "calibration": self.calibration.model_dump(mode="json"),
                "feedback": [e.model_dump(mode="json") for e in self.feedback],
                "requirement_observations": [o.model_dump(mode="json") for o in self.requirement_observations],
            }
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            tmp.replace(self.data_path)
        except Exception as exc:
            logger.exception("Could not persist store %s", self.data_path)
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            # A failed write must not leave changes visible in memory as if saved.
            if self.data_path.exists():
                self._load()
            else:
                self._reset()
            raise StorageError(f"Workspace could not be saved: {self.data_path}") from exc

    def _reset(self) -> None:
        self.projects = {}
        self.versions = {}
        self.actuals = {}
        self.evaluation_runs = []
        self.calibration = CalibrationState()
        self.feedback = []
        self.requirement_observations = []

    def _load(self) -> None:
        if not self.data_path or not self.data_path.exists():
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            projects = {}
            for p_dict in payload.get("projects", []):
                p = Project.model_validate(p_dict)
                projects[p.project_id] = p
            versions = {pid: [EstimateVersion.model_validate(v) for v in v_list]
                        for pid, v_list in payload.get("versions", {}).items()}
            actuals = {pid: [ActualWork.model_validate(a) for a in a_list]
                       for pid, a_list in payload.get("actuals", {}).items()}
            evaluation_runs = [EvaluationRun.model_validate(r) for r in payload.get("evaluation_runs", [])]
            feedback = [FeedbackEvent.model_validate(e) for e in payload.get("feedback", [])]
            requirement_observations = [
                RequirementObservation.model_validate(o) for o in payload.get("requirement_observations", [])
            ]
            calibration = CalibrationState.model_validate(payload.get("calibration") or {})
            self.projects, self.versions, self.actuals = projects, versions, actuals
            self.evaluation_runs, self.feedback = evaluation_runs, feedback
            self.requirement_observations, self.calibration = requirement_observations, calibration
        except Exception as exc:
            logger.exception("Could not load store %s", self.data_path)
            raise StorageError(f"Workspace could not be loaded: {self.data_path}") from exc
