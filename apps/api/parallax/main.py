"""FastAPI REST application for PARALLAX AI.

Exposes endpoints for project intake, evidence-backed WBS estimation,
adversarial review, what-if active clarification, and actuals calibration.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .schemas import (
    ActualWork,
    ClarificationAnswer,
    EstimateVersion,
    HistoricalCase,
    Project,
    ProjectCreate,
)
from . import empirical
from .service import ParallaxService
from .storage import StorageRepository

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
# PARALLAX_DATA_PATH lets tests and deployments use an isolated store.
DATA_PATH = Path(os.environ.get("PARALLAX_DATA_PATH", ROOT_DIR / "data" / "parallax_store.json"))
GOLDEN_DIR = ROOT_DIR / "datasets" / "golden_briefs"
WEB_DIST = Path(os.environ.get("PARALLAX_WEB_DIST", ROOT_DIR / "apps" / "web" / "dist"))
repo = StorageRepository(data_path=DATA_PATH)
service = ParallaxService(repository=repo)

app = FastAPI(
    title="PARALLAX AI — Estimation Intelligence API",
    description="Evidence-driven, self-calibrating estimation engine for software and AI automation projects.",
    version="0.1.0",
)

# Enable CORS for local Next.js / Vite web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ActualWorkCreate(BaseModel):
    actual_hours: float = Field(gt=0)
    item_actuals: Optional[dict[str, float]] = None
    deviation_reasons: Optional[list[str]] = None


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "parallax-estimator-api",
        "version": "0.1.0",
        "projects_count": len(repo.list_projects()),
        "historical_cases_count": len(repo.list_historical_cases()),
    }


@app.get("/api/v1/system/status", tags=["System"])
def system_status():
    """Live facts for the UI header: dataset, calibration state, last benchmark."""
    return service.system_status()


@app.get("/api/v1/sample-briefs", tags=["Projects"])
def sample_briefs():
    """Golden briefs stored in datasets/golden_briefs (inputs only, no labels claimed)."""
    briefs = []
    for path in sorted(GOLDEN_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        briefs.append(
            {
                "id": data.get("brief_id", path.stem),
                "title": data.get("title", path.stem),
                "project_type": data.get("project_type", "custom_software"),
                "brief_text": data["brief_text"],
            }
        )
    return briefs


@app.post("/api/v1/projects", response_model=Project, status_code=status.HTTP_201_CREATED, tags=["Projects"])
def create_project(payload: ProjectCreate):
    try:
        project = service.create_project(
            title=payload.title,
            brief_text=payload.brief_text,
            project_type=payload.project_type,
            documents=payload.documents,
        )
        return project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/projects", response_model=list[Project], tags=["Projects"])
def list_projects():
    return repo.list_projects()


@app.get("/api/v1/projects/{project_id}", response_model=Project, tags=["Projects"])
def get_project(project_id: str):
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/api/v1/projects/{project_id}/estimate", response_model=EstimateVersion, tags=["Estimation"])
def estimate_project(project_id: str):
    try:
        version = service.estimate_project(project_id)
        return version
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/projects/{project_id}/versions", response_model=list[EstimateVersion], tags=["Estimation"])
def list_versions(project_id: str):
    if not repo.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return repo.get_versions(project_id)


@app.get("/api/v1/projects/{project_id}/versions/{version_id}", response_model=EstimateVersion, tags=["Estimation"])
def get_version(project_id: str, version_id: str):
    version = repo.get_version(project_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@app.post("/api/v1/projects/{project_id}/clarify", response_model=EstimateVersion, tags=["Clarification"])
def answer_clarification(project_id: str, payload: ClarificationAnswer):
    try:
        new_version = service.answer_clarification(
            project_id=project_id,
            question_id=payload.question_id,
            answer=payload.answer,
            notes=payload.notes,
        )
        return new_version
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/projects/{project_id}/actuals", tags=["Actuals & Learning"])
def record_actuals(project_id: str, payload: ActualWorkCreate):
    try:
        result = service.record_actuals(
            project_id=project_id,
            actual_hours=payload.actual_hours,
            item_actuals=payload.item_actuals,
            deviation_reasons=payload.deviation_reasons,
        )
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/historical-cases", response_model=list[HistoricalCase], tags=["Historical Intelligence"])
def list_historical_cases(domain: Optional[str] = None):
    """Completed projects in this workspace (projects with recorded actuals)."""
    return repo.list_historical_cases(domain=domain)


@app.get("/api/v1/calibration", tags=["Actuals & Learning"])
def calibration_status():
    return service.calibration_status()


@app.get("/api/v1/datasets/sip", tags=["Historical Intelligence"])
def sip_dataset_summary():
    try:
        return empirical.dataset_summary()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/benchmark/run", tags=["Evaluation"])
def run_benchmark():
    try:
        return service.run_benchmark_suite()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


# Serve the built web UI from the same origin when it exists (production image).
# Mounted last so every API route above takes precedence.
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
