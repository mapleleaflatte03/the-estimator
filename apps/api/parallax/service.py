"""Service orchestrator for PARALLAX.

Coordinates Project lifecycle, EstimateVersion creation, Active Clarification,
and the actuals -> calibration feedback loop with strict provenance and
version immutability.
"""
from __future__ import annotations

import logging
import math
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from . import empirical, risk
from .conformal import AdaptiveLevel
from .evaluation.benchmark import PredictionRecord, evaluate_predictions
from .extractor import MODEL_TAG, clause_texts, extract_scope_and_wbs, proposed_kinds
from .jev import JevReader
from .locale import current_lang
from .schemas import (
    ActualWork,
    CalibrationObservation,
    CalibrationState,
    EstimateVersion,
    EvaluationRun,
    FeedbackEvent,
    Project,
    RequirementObservation,
)
from .storage import StorageRepository


class AIReaderUnavailable(RuntimeError):
    """The AI reader could not read every clause; estimates are not produced without it."""

MULTIPLIER_BOUNDS = (0.5, 2.0)
INTERVAL_GAMMA = 0.05  # chosen on SiP 2008-2010 replay, confirmed on 2011-2014 (datasets/eval/sip_conformal_*.json)
# An AI suggestion kind is muted once users answered it at least this often and rarely accept it.
SUPPRESS_MIN_ANSWERS = 3
SUPPRESS_MAX_ACCEPTANCE = 0.3
logger = logging.getLogger(__name__)


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


def hierarchical_multiplier(observations, project_type: str, prior_strength: float) -> tuple[float, int]:
    """Per-project-type bias multiplier, partially pooled towards the global one.

    With no actuals of this type it equals the global multiplier; each
    completed project of this type pulls it further towards that type's own
    record. Returns (multiplier, number of same-type observations).
    """
    global_m = shrunk_multiplier([o.log_ratio for o in observations], prior_strength)
    same = [o.log_ratio for o in observations if o.project_type == project_type]
    if not same:
        return global_m, 0
    log_m = (sum(same) + prior_strength * math.log(global_m)) / (len(same) + prior_strength)
    return min(MULTIPLIER_BOUNDS[1], max(MULTIPLIER_BOUNDS[0], math.exp(log_m))), len(same)


class ParallaxService:
    def __init__(self, repository: StorageRepository, use_empirical_data: bool = True,
                 reader: Optional[JevReader] = None):
        self.repo = repository
        self.use_empirical_data = use_empirical_data
        cache = repository.data_path.with_name("jev_cache.json") if repository.data_path else None
        self.reader = reader if reader is not None else JevReader(cache_path=cache)

    def _readings(self, project: Project, reader: Optional[JevReader] = None) -> dict:
        reader = reader or self.reader
        texts = list(dict.fromkeys(t.strip() for t in clause_texts(project.brief_text, project.documents) if t.strip()))
        try:
            readings = reader.read(texts)
        except Exception as exc:
            logger.warning("AI reader failed: %s", exc)
            readings = {}
        try:
            reader.verify(readings, {t: proposed_kinds(t) for t in readings})
        except Exception as exc:  # verification only removes rule over-matches; never block on it
            logger.warning("AI verification failed: %s", exc)
        missing = [t for t in texts if t not in readings]
        if missing and self.jev_required:
            status = reader.status()
            if current_lang() == "en":
                if not status["configured"]:
                    reason = "no Jev API key is configured (JEVSTATION_API_KEY…)"
                elif status.get("halted"):
                    reason = "the reader paused to protect credits"
                elif status["keys_usable"] == 0:
                    reason = "every Jev key is out of credit or failing"
                elif not status["available"]:
                    reason = "the hourly call limit has been reached"
                else:
                    reason = status.get("last_error") or "Jev did not answer"
                raise AIReaderUnavailable(
                    f"Jev could not read {len(missing)}/{len(texts)} clauses of the brief ({reason}). "
                    "An estimate needs every clause read; try again in a few minutes."
                )
            if not status["configured"]:
                reason = "chưa cấu hình khóa API Jev (JEVSTATION_API_KEY…)"
            elif status.get("halted"):
                reason = "bộ đọc đã tạm dừng để bảo vệ credit"
            elif status["keys_usable"] == 0:
                reason = "tất cả khóa Jev đã hết credit hoặc đang lỗi"
            elif not status["available"]:
                reason = "đã chạm giới hạn số lần gọi mỗi giờ"
            else:
                reason = status.get("last_error") or "Jev không trả lời"
            raise AIReaderUnavailable(
                f"AI Jev chưa đọc được {len(missing)}/{len(texts)} câu của mô tả ({reason}). "
                "Dự toán cần AI đọc đủ mọi câu; hãy thử lại sau ít phút."
            )
        return readings

    @property
    def jev_required(self) -> bool:
        return os.environ.get("JEV_REQUIRED", "1") != "0"

    def adjustments(self) -> risk.Adjustments:
        return risk.learn(self.repo.list_requirement_observations())

    @property
    def calibration_multiplier(self) -> float:
        return self.repo.get_calibration().multiplier

    def multiplier_for(self, project_type: str) -> float:
        state = self.repo.get_calibration()
        return hierarchical_multiplier(state.observations, project_type, state.prior_strength)[0]

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

    def _build_version(self, project: Project, answers: dict[str, bool],
                       manual_edits: Optional[dict] = None, reader: Optional[JevReader] = None) -> EstimateVersion:
        existing = self.repo.get_versions(project.project_id)
        if manual_edits is None:
            manual_edits = dict(existing[-1].manual_edits) if existing else {}
        version = extract_scope_and_wbs(
            project_id=project.project_id,
            brief_text=project.brief_text,
            source_docs=project.documents,
            clarification_answers=answers,
            version_id=f"v{len(existing) + 1}",
            parent_version_id=existing[-1].version_id if existing else None,
            calibration_multiplier=self.multiplier_for(project.project_type),
            historical_cases=self._comparable_hours(project),
            systemic_ratio_pool=self._systemic_pool(),
            readings=self._readings(project, reader),
            manual_edits=manual_edits,
            ai_suppressed=self.suppressed_ai_kinds(),
            adjustments=self.adjustments(),
            interval_alpha=self.repo.get_calibration().interval_alpha,
        )
        version.clarification_notes = dict(existing[-1].clarification_notes) if existing else {}
        return version

    def feedback_summary(self) -> dict:
        by_comp: dict[str, dict] = {}
        for e in self.repo.list_feedback():
            row = by_comp.setdefault(e.component, {"component": e.component, "answered": 0, "accepted": 0})
            row["answered"] += 1
            row["accepted"] += int(e.accepted)
        for row in by_comp.values():
            # Laplace-smoothed acceptance so one answer cannot mute a kind.
            row["acceptance"] = round((row["accepted"] + 1) / (row["answered"] + 2), 3)
            row["muted"] = row["answered"] >= SUPPRESS_MIN_ANSWERS and row["acceptance"] < SUPPRESS_MAX_ACCEPTANCE
        rows = sorted(by_comp.values(), key=lambda r: -r["answered"])
        return {
            "answered": sum(r["answered"] for r in rows),
            "accepted": sum(r["accepted"] for r in rows),
            "by_component": rows,
        }

    def suppressed_ai_kinds(self) -> set[str]:
        return {r["component"] for r in self.feedback_summary()["by_component"] if r["muted"]}

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

    def estimate_project(self, project_id: str, reader: Optional[JevReader] = None) -> EstimateVersion:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        if self.repo.get_actuals(project_id):
            raise ValueError("This project has actual hours and its estimate is frozen. Create a new project to measure what the system learned.")
        existing = self.repo.get_versions(project_id)
        answers = dict(existing[-1].clarification_answers) if existing else {}
        return self.repo.add_version(self._build_version(project, answers, reader=reader))

    def answer_clarification(
        self,
        project_id: str,
        question_id: str,
        answer: bool,
        notes: Optional[str] = None,
        reader: Optional[JevReader] = None,
    ) -> EstimateVersion:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        if self.repo.get_actuals(project_id):
            raise ValueError("This project has actual hours and its estimate is frozen. Create a new project to measure what the system learned.")
        existing = self.repo.get_versions(project_id)
        if not existing:
            raise ValueError("Cannot clarify before generating initial estimate")
        parent = existing[-1]
        if question_id not in {q.question_id for q in parent.clarifications}:
            raise ValueError(f"Unknown clarification question {question_id}")
        # Answers accumulate across versions; a later answer overrides an earlier one.
        answers = {**parent.clarification_answers, question_id: answer}
        events = []
        if question_id.endswith("-AI"):
            req_id = question_id[len("CLAR-"):-len("-AI")]
            req = next((r for r in parent.requirements if r.req_id == req_id), None)
            comp = (req.ai_reading or {}).get("suggested_component") if req else None
            if comp:
                events.append(FeedbackEvent(event="ai_suggestion", component=comp, accepted=answer,
                                            project_id=project_id, version_id=parent.version_id))
        version = self._build_version(project, answers, reader=reader)
        if notes is not None:
            cleaned = notes.strip()
            if cleaned:
                version.clarification_notes[question_id] = cleaned
            else:
                version.clarification_notes.pop(question_id, None)
        return self.repo.add_version(version, status="clarified", feedback_events=events)

    def update_wbs(self, project_id: str, edits: dict, reader: Optional[JevReader] = None) -> EstimateVersion:
        """New immutable version with the user's WBS edits; edits persist across later versions."""
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        if self.repo.get_actuals(project_id):
            raise ValueError("This project has actual hours and its estimate is frozen. Create a new project to measure what the system learned.")
        existing = self.repo.get_versions(project_id)
        if not existing:
            raise ValueError("Cannot edit the WBS before generating an estimate")
        parent = existing[-1]
        known = {w.item_id for w in parent.wbs} | {
            i for i in (parent.manual_edits.get("overrides") or {})
        }
        for i, add in enumerate(edits.get("added") or [], start=1):
            add["item_id"] = f"USER-{i:02d}"
        unknown = [i for i in (edits.get("overrides") or {}) if i not in known and not i.startswith("USER-")]
        if unknown:
            raise ValueError(f"Unknown work items: {', '.join(unknown[:5])}")
        removed = set(edits.get("removed") or []) - set(parent.manual_edits.get("removed") or [])
        events = []
        for req in parent.requirements:
            comp = (req.ai_reading or {}).get("added_component")
            if comp and any(i.startswith(f"{req.req_id}-{comp.upper()}-") for i in removed):
                events.append(FeedbackEvent(event="ai_item_removed", component=comp, accepted=False,
                                            project_id=project_id, version_id=parent.version_id))
        version = self._build_version(project, dict(parent.clarification_answers), edits, reader)
        return self.repo.add_version(version, feedback_events=events)

    def record_actuals(
        self,
        project_id: str,
        actual_hours: float,
        item_actuals: Optional[dict[str, float]] = None,
        deviation_reasons: Optional[list[str]] = None,
        requirement_actuals: Optional[dict[str, float]] = None,
    ) -> dict:
        project = self.repo.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        versions = self.repo.get_versions(project_id)
        if not versions:
            raise ValueError("No estimate version found to compare against actuals")

        if not math.isfinite(actual_hours) or actual_hours <= 0:
            raise ValueError("Actual hours must be a positive finite number")
        supplied = requirement_actuals or {}
        if any(not math.isfinite(float(v)) or float(v) <= 0 for v in supplied.values()):
            raise ValueError("Each requirement's actual hours must be a positive finite number")
        if sum(float(v) for v in supplied.values()) > actual_hours + 0.1:
            raise ValueError("Requirement hours cannot add up to more than the project's total actual hours")

        # A correction to recorded actuals must still be compared with the
        # original committed estimate, not a newer or retrospectively fitted one.
        previous = self.repo.get_actuals(project_id)
        baseline = self.repo.get_version(project_id, previous[-1].version_id) if previous else versions[-1]
        supplied_items = item_actuals or {}
        unknown_items = set(supplied_items) - {w.item_id for w in baseline.wbs}
        if unknown_items:
            raise ValueError(f"Unknown work items: {', '.join(sorted(unknown_items)[:5])}")
        if any(not math.isfinite(float(v)) or float(v) <= 0 for v in supplied_items.values()):
            raise ValueError("Each work item's actual hours must be a positive finite number")
        if sum(float(v) for v in supplied_items.values()) > actual_hours + 0.1:
            raise ValueError("Work-item hours cannot add up to more than the project's total actual hours")
        requirement_actuals = {k: float(v) for k, v in (requirement_actuals or {}).items() if v and float(v) > 0}
        unknown = set(requirement_actuals) - {r.req_id for r in baseline.requirements}
        if unknown:
            raise ValueError(f"Unknown requirements: {', '.join(sorted(unknown)[:5])}")
        req_obs = [
            RequirementObservation(
                project_id=project_id, version_id=baseline.version_id, req_id=req.req_id,
                components=list(req.components), risk_group=req.risk_group,
                overrun_probability=(req.ai_reading or {}).get("overrun"),
                estimated_hours=req.estimated_hours_raw, actual_hours=requirement_actuals[req.req_id],
            )
            for req in baseline.requirements
            if req.req_id in requirement_actuals and req.in_scope and req.estimated_hours_raw
        ]
        old_req_obs = self.repo.list_requirement_observations()
        learning_before = risk.learn(old_req_obs)
        learning_after = risk.learn([o for o in old_req_obs if o.project_id != project_id] + req_obs)
        actual = ActualWork(
            actual_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
            project_id=project_id,
            version_id=baseline.version_id,
            actual_hours=actual_hours,
            item_actuals={k: float(v) for k, v in supplied_items.items()},
            deviation_reasons=deviation_reasons or [],
        )

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
        type_before = hierarchical_multiplier(state.observations, project.project_type, state.prior_strength)[0]
        type_after, type_n = hierarchical_multiplier(observations, project.project_type, state.prior_strength)
        # Adaptive conformal update of the "80% range" (gamma fixed on SiP 2008-2010, scripts/sip_conformal_replay.py).
        hit = fc.p10_hours <= actual_hours <= fc.p90_hours
        if previous:
            old_hit = fc.p10_hours <= previous[-1].actual_hours <= fc.p90_hours
            # Replace this project's one contribution; do not count a correction
            # as another finished project.
            new_alpha = state.interval_alpha + INTERVAL_GAMMA * (int(hit) - int(old_hit))
            range_checks = state.interval_updates
            range_hits = state.interval_hits + int(hit) - int(old_hit)
        else:
            level = AdaptiveLevel(gamma=INTERVAL_GAMMA, alpha={"all": state.interval_alpha})
            level.update("all", fc.p10_hours, fc.p90_hours, actual_hours)
            new_alpha = level.level("all")
            range_checks = state.interval_updates + 1
            range_hits = state.interval_hits + int(hit)
        self.repo.commit_actuals(
            actual, req_obs,
            CalibrationState(
                multiplier=after,
                prior_strength=state.prior_strength,
                observations=observations,
                updated_at=datetime.now(timezone.utc),
                interval_alpha=round(min(0.95, max(0.0, new_alpha)), 4),
                interval_updates=range_checks,
                interval_hits=range_hits,
            ),
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
                "project_type": project.project_type,
                "type_multiplier_before": round(type_before, 4),
                "type_multiplier_after": round(type_after, 4),
                "type_observations": type_n,
                "n_observations": len(observations),
                "prior_strength": state.prior_strength,
                "applies_to": "future projects; completed project estimates stay frozen",
                "range_level_before": round(1 - state.interval_alpha, 4),
                "range_level_after": round(1 - min(0.95, max(0.0, new_alpha)), 4),
                "range_hits": range_hits,
                "range_checks": range_checks,
            },
            "learning": {
                "requirements_recorded": len(req_obs),
                "before": learning_before.as_dict(),
                "after": learning_after.as_dict(),
            },
        }

    def calibration_status(self) -> dict:
        state = self.repo.get_calibration()
        types = sorted({o.project_type for o in state.observations})
        by_type = []
        for t in types:
            m, n = hierarchical_multiplier(state.observations, t, state.prior_strength)
            by_type.append({"project_type": t, "multiplier": round(m, 4), "n_observations": n})
        return {
            "multiplier": round(state.multiplier, 4),
            "range_level": round(1 - state.interval_alpha, 4),
            "range_hits": state.interval_hits,
            "range_checks": state.interval_updates,
            "by_type": by_type,
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
            others = [x for j, x in enumerate(obs) if j != i]
            m = hierarchical_multiplier(others, o.project_type, state.prior_strength)[0]
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
            "ai_reader": {**self.reader.status(), "required": self.jev_required},
            "ai_feedback": self.feedback_summary(),
            "learning": {**self.adjustments().as_dict(),
                         "requirement_observations": len(self.repo.list_requirement_observations())},
            "last_benchmark": (
                {"run_id": last.run_id, "created_at": last.created_at, "metrics": last.metrics}
                if last
                else None
            ),
        }
