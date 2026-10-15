"""FastAPI REST application for PARALLAX AI.

Exposes endpoints for project intake, evidence-backed WBS estimation,
adversarial review, what-if active clarification, and actuals calibration.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .schemas import (
    ActualWork,
    ClarificationAnswer,
    EstimateVersion,
    HistoricalCase,
    Project,
    ProjectCreate,
)
from .service import ParallaxService
from .storage import StorageRepository

# Initialize persistence and service
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
repo = StorageRepository(data_path=DATA_DIR / "parallax_store.json")
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
    return repo.list_historical_cases(domain=domain)


@app.post("/api/v1/benchmark/run", tags=["Evaluation"])
def run_benchmark():
    metrics = service.run_benchmark_suite()
    return {
        "model_name": metrics.model_name,
        "split": metrics.split,
        "n_cases": metrics.n_cases,
        "mae": round(metrics.mae, 2),
        "mdape": round(metrics.mdape, 2),
        "wape": round(metrics.wape, 2),
        "pred_25": round(metrics.pred_25, 2),
        "interval_coverage": round(metrics.interval_coverage, 2),
        "mean_interval_width": round(metrics.mean_interval_width, 2),
    }
