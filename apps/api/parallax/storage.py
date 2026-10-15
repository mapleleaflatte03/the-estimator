"""Thread-safe persistent storage repository for PARALLAX.

Enforces version immutability: EstimateVersions are never overwritten,
only appended as a DAG of versions with parent_version_id links.
"""
from __future__ import annotations
import json
from pathlib import Path
from threading import Lock
from typing import Optional

from .schemas import (
    ActualWork,
    EstimateVersion,
    EvaluationRun,
    HistoricalCase,
    Project,
)


class StorageRepository:
    def __init__(self, data_path: Optional[Path] = None):
        self.lock = Lock()
        self.data_path = data_path
        self.projects: dict[str, Project] = {}
        self.versions: dict[str, list[EstimateVersion]] = {}  # project_id -> list[EstimateVersion]
        self.historical_cases: dict[str, HistoricalCase] = {}
        self.actuals: dict[str, list[ActualWork]] = {}  # project_id -> list[ActualWork]
        self.evaluation_runs: list[EvaluationRun] = []
        self._load_seed_historical_cases()
        if self.data_path and self.data_path.exists():
            self._load()

    def _load_seed_historical_cases(self) -> None:
        """Seed representative historical project cases for reference-class matching."""
        seeds = [
            HistoricalCase(
                case_id="HIST-PM-01",
                title="Internal Workflow & Task Management Portal",
                domain="internal_tool",
                actual_hours=210.0,
                task_count=18,
                complexity_score=6.5,
                tags=["sso", "rbac", "reporting", "postgres"],
                notes="Completed in 2025. Standard CRUD with custom RBAC and PDF reports.",
            ),
            HistoricalCase(
                case_id="HIST-PM-02",
                title="Corporate Operations Dashboard & Approval Queue",
                domain="internal_tool",
                actual_hours=185.0,
                task_count=15,
                complexity_score=5.8,
                tags=["dashboard", "audit_log", "fastapi", "react"],
                notes="Delivered on schedule. Included Google OAuth SSO and CSV export.",
            ),
            HistoricalCase(
                case_id="HIST-PM-03",
                title="Project Management Suite with Legacy ERP Connector",
                domain="internal_tool",
                actual_hours=320.0,
                task_count=26,
                complexity_score=8.5,
                tags=["erp", "sap_integration", "batch_sync", "sso"],
                notes="Experienced scope creep on SOAP ERP interface and data reconciliation.",
            ),
            HistoricalCase(
                case_id="HIST-PM-04",
                title="Departmental Resource Scheduling Portal",
                domain="internal_tool",
                actual_hours=160.0,
                task_count=14,
                complexity_score=5.2,
                tags=["calendar", "rbac", "notifications"],
                notes="Clean requirements, no legacy integration required.",
            ),
            HistoricalCase(
                case_id="HIST-PM-05",
                title="Enterprise Vendor Management & Review Hub",
                domain="internal_tool",
                actual_hours=240.0,
                task_count=20,
                complexity_score=7.0,
                tags=["vendor", "sso", "audit_trail", "postgres"],
                notes="Required SAML2 enterprise SSO and multi-stage approval workflow.",
            ),
            HistoricalCase(
                case_id="HIST-PM-06",
                title="Internal Compliance & Asset Tracking System",
                domain="internal_tool",
                actual_hours=195.0,
                task_count=16,
                complexity_score=6.0,
                tags=["compliance", "assets", "rbac", "reporting"],
                notes="Standard enterprise internal tool.",
            ),
            # E-commerce API sync cases
            HistoricalCase(
                case_id="HIST-ECOMM-01",
                title="Multichannel Inventory & Order Webhook Hub",
                domain="api_integration",
                actual_hours=145.0,
                task_count=12,
                complexity_score=6.0,
                tags=["shopify", "amazon", "rate_limiting", "redis"],
                notes="Webhooks with retry queue and concurrency locking.",
            ),
            HistoricalCase(
                case_id="HIST-ECOMM-02",
                title="B2B Catalog & ERP Pricing Sync Service",
                domain="api_integration",
                actual_hours=230.0,
                task_count=19,
                complexity_score=7.5,
                tags=["erp", "catalog", "pricing_rules", "batch_sync"],
                notes="High data volume catalog updates with daily delta sync.",
            ),
            HistoricalCase(
                case_id="HIST-ECOMM-03",
                title="Payment Gateway & Tax Engine Integration",
                domain="api_integration",
                actual_hours=115.0,
                task_count=9,
                complexity_score=5.5,
                tags=["stripe", "avalara", "webhooks"],
                notes="Standard REST payment and tax calculation adapters.",
            ),
            HistoricalCase(
                case_id="HIST-ECOMM-04",
                title="Omnichannel Marketplace Order Ingestion Engine",
                domain="api_integration",
                actual_hours=175.0,
                task_count=15,
                complexity_score=6.8,
                tags=["marketplace", "orders", "webhook", "celery"],
                notes="Handled spike traffic during flash sales.",
            ),
            HistoricalCase(
                case_id="HIST-ECOMM-05",
                title="Courier Shipping API & Label Generation Gateway",
                domain="api_integration",
                actual_hours=130.0,
                task_count=11,
                complexity_score=5.0,
                tags=["dhl", "fedex", "pdf_labels", "tracking"],
                notes="Straightforward multi-carrier integration.",
            ),
            # AI & RAG cases
            HistoricalCase(
                case_id="HIST-AI-01",
                title="Customer Support RAG Knowledge Base & Ticket Router",
                domain="ai_workflow",
                actual_hours=165.0,
                task_count=14,
                complexity_score=6.5,
                tags=["rag", "pgvector", "embeddings", "slack_bot"],
                notes="Knowledge retrieval over PDF/Notion docs with fallback to Zendesk.",
            ),
            HistoricalCase(
                case_id="HIST-AI-02",
                title="Contract Extraction & Clause Analysis Pipeline",
                domain="ai_workflow",
                actual_hours=220.0,
                task_count=18,
                complexity_score=7.8,
                tags=["pdf_ocr", "structured_extraction", "pydantic", "evals"],
                notes="Complex document layout parsing and multi-turn verification.",
            ),
            HistoricalCase(
                case_id="HIST-AI-03",
                title="Internal Employee FAQ Chatbot with Enterprise RBAC",
                domain="ai_workflow",
                actual_hours=140.0,
                task_count=11,
                complexity_score=5.8,
                tags=["rag", "teams_bot", "rbac_filtering"],
                notes="Integrated with Microsoft Teams and SharePoint.",
            ),
            HistoricalCase(
                case_id="HIST-AI-04",
                title="Sales Call Transcription & CRM Summarization Agent",
                domain="ai_workflow",
                actual_hours=155.0,
                task_count=13,
                complexity_score=6.2,
                tags=["whisper", "crm_sync", "llm_eval", "webhook"],
                notes="Automated post-call summary creation in HubSpot.",
            ),
            HistoricalCase(
                case_id="HIST-AI-05",
                title="Financial Report Data Extraction & Validation Agent",
                domain="ai_workflow",
                actual_hours=205.0,
                task_count=16,
                complexity_score=7.4,
                tags=["table_extraction", "validation_rules", "auditing"],
                notes="Requires strict schema conformity and source cell citation.",
            ),
        ]
        for c in seeds:
            self.historical_cases[c.case_id] = c

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
        with self.lock:
            if domain:
                return [c for c in self.historical_cases.values() if c.domain == domain]
            return list(self.historical_cases.values())

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
            }
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception:
            pass

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
        except Exception:
            pass
