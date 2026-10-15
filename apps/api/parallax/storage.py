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
    EvaluationRun,
    HistoricalCase,
    Project,
)

logger = logging.getLogger(__name__)


class StorageRepository:
    def __init__(self, data_path: Optional[Path] = None):
        self.lock = Lock()
        self.data_path = data_path
        self.projects: dict[str, Project] = {}
        self.versions: dict[str, list[EstimateVersion]] = {}  # project_id -> list[EstimateVersion]
        self.actuals: dict[str, list[ActualWork]] = {}  # project_id -> list[ActualWork]
        self.evaluation_runs: list[EvaluationRun] = []
        self.calibration = CalibrationState()
        if self.data_path and self.data_path.exists():
            self._load()

    def save_project(self, project: Project) -> Project:
        with self.lock:
            self.projects[project.project_id] = project
            if project.project_id not in self.versions:
                self.versions[project.project_id] = []
            if project.project_id not in self.actuals:
                self.actuals[project.project_id] = []
            self._save()
            return project

    def get_project(self, project_id: str) -> Optional[Project]:
        with self.lock:
            return self.projects.get(project_id)

    def list_projects(self) -> list[Project]:
        with self.lock:
            return sorted(self.projects.values(), key=lambda p: p.created_at, reverse=True)

    def add_version(self, version: EstimateVersion) -> EstimateVersion:
        with self.lock:
            p_id = version.project_id
            if p_id not in self.projects:
                raise KeyError(f"Project {p_id} not found")
            existing = self.versions.get(p_id, [])
            # Enforce immutable version IDs
            if any(v.version_id == version.version_id for v in existing):
                raise ValueError(f"Version {version.version_id} already exists for project {p_id}")
            existing.append(version)
            self.versions[p_id] = existing
            # Update project pointer
            project = self.projects[p_id]
            project.current_version_id = version.version_id
            project.status = "estimated"
            self._save()
            return version

    def get_versions(self, project_id: str) -> list[EstimateVersion]:
        with self.lock:
            return list(self.versions.get(project_id, []))

    def get_version(self, project_id: str, version_id: str) -> Optional[EstimateVersion]:
        with self.lock:
            for v in self.versions.get(project_id, []):
                if v.version_id == version_id:
                    return v
            return None

    def add_actual_work(self, actual: ActualWork) -> ActualWork:
        with self.lock:
            p_id = actual.project_id
            if p_id not in self.projects:
                raise KeyError(f"Project {p_id} not found")
            if p_id not in self.actuals:
                self.actuals[p_id] = []
            self.actuals[p_id].append(actual)
            self.projects[p_id].status = "actuals_recorded"
            self._save()
            return actual

    def get_actuals(self, project_id: str) -> list[ActualWork]:
        with self.lock:
            return list(self.actuals.get(project_id, []))

    def get_all_actuals(self) -> list[ActualWork]:
        with self.lock:
            res = []
            for act_list in self.actuals.values():
                res.extend(act_list)
            return res

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

    def get_calibration(self) -> CalibrationState:
        with self.lock:
            return self.calibration.model_copy(deep=True)

    def save_calibration(self, state: CalibrationState) -> CalibrationState:
        with self.lock:
            self.calibration = state
            self._save()
            return state

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
            }
            tmp = self.data_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            tmp.replace(self.data_path)
        except Exception as exc:
            logger.error("Could not persist store %s: %s", self.data_path, exc)

    def _load(self) -> None:
        if not self.data_path or not self.data_path.exists():
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            for p_dict in payload.get("projects", []):
                p = Project.model_validate(p_dict)
                self.projects[p.project_id] = p
            for pid, v_list in payload.get("versions", {}).items():
                self.versions[pid] = [EstimateVersion.model_validate(v) for v in v_list]
            for pid, a_list in payload.get("actuals", {}).items():
                self.actuals[pid] = [ActualWork.model_validate(a) for a in a_list]
            for r_dict in payload.get("evaluation_runs", []):
                self.evaluation_runs.append(EvaluationRun.model_validate(r_dict))
            if payload.get("calibration"):
                self.calibration = CalibrationState.model_validate(payload["calibration"])
        except Exception as exc:  # keep the API up, but never fail silently
            logger.error("Could not load store %s: %s", self.data_path, exc)
