"""FastAPI REST application for PARALLAX AI.

Exposes endpoints for project intake, evidence-backed WBS estimation,
adversarial review, what-if active clarification, and actuals calibration.
"""
from __future__ import annotations
import json
import os
import re
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .schemas import (
    ActualWork,
    ClarificationAnswer,
    EstimateVersion,
    HistoricalCase,
    ManualEdits,
    Project,
    ProjectCreate,
)
from . import empirical
from .export import proposal_markdown, wbs_csv
from .jev import load_dotenv
from .locale import ui_language
from .service import AIReaderUnavailable, ParallaxService
from .storage import StorageError, StorageRepository

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")  # API keys live in a git-ignored .env; real env vars take precedence
# PARALLAX_DATA_PATH lets tests and deployments use an isolated store.
DATA_PATH = Path(os.environ.get("PARALLAX_DATA_PATH", ROOT_DIR / "data" / "parallax_store.json"))
GOLDEN_DIR = ROOT_DIR / "datasets" / "golden_briefs"
WEB_DIST = Path(os.environ.get("PARALLAX_WEB_DIST", ROOT_DIR / "apps" / "web" / "dist"))
repo = StorageRepository(data_path=DATA_PATH)
service = ParallaxService(repository=repo)
_workspace_services: dict[str, ParallaxService] = {}
_workspace_lock = Lock()
_workspace_id_pattern = re.compile(r"[0-9a-f]{32}")
RELEASE = "scope-decisions-2026-10-18-r6"

# One shared clock of estimate attempts per visitor.
_estimate_hits: dict[str, list[float]] = {}
_estimate_lock = Lock()


def _visitor_ip(request: Request) -> str:
    # Only trust forwarding headers behind the known deployment proxy. Its
    # right-most address is the one the proxy appended; left-most is spoofable.
    forwarded = request.headers.get("x-forwarded-for", "")
    if (os.environ.get("RENDER") or os.environ.get("TRUST_PROXY_HEADERS") == "1") and forwarded.strip():
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def enforce_estimate_limit(request: Request) -> None:
    """Cap how often one visitor can ask Jev to read a brief. 0 disables the cap (tests)."""
    limit = int(os.environ.get("ESTIMATE_IP_LIMIT_PER_HOUR", "24"))
    if limit <= 0:
        return
    now = time.time()
    ip = _visitor_ip(request)
    with _estimate_lock:
        # Expire abandoned visitors so a public demo cannot grow this map forever.
        for key in list(_estimate_hits):
            recent = [t for t in _estimate_hits[key] if now - t < 3600]
            if recent:
                _estimate_hits[key] = recent
            else:
                del _estimate_hits[key]
        exceeded = len(_estimate_hits.get(ip, [])) >= limit
        if not exceeded:
            _estimate_hits.setdefault(ip, []).append(now)
    if exceeded:
        if ui_language.get() == "en":
            detail = (
                f"This address has used its {limit} brief readings for this hour. "
                "Sample briefs still open; try again later."
            )
        else:
            detail = (
                f"Đã đủ {limit} lần đọc mô tả từ địa chỉ này trong một giờ. "
                "Các mô tả mẫu vẫn mở được; hãy thử lại sau."
            )
        raise HTTPException(status_code=429, detail=detail)

app = FastAPI(
    title="PARALLAX AI — Estimation Intelligence API",
    description="Evidence-driven, self-calibrating estimation engine for software and AI automation projects.",
    version=RELEASE,
)


@app.middleware("http")
async def set_ui_language(request: Request, call_next):
    supplied = request.headers.get("x-parallax-workspace") or request.cookies.get("parallax_workspace", "")
    workspace_id = supplied if _workspace_id_pattern.fullmatch(supplied) else secrets.token_hex(16)
    request.state.workspace_id = workspace_id
    header = request.headers.get("accept-language", "")
    token = ui_language.set("en" if header.lower().startswith("en") else "vi")
    try:
        response = await call_next(request)
        if request.cookies.get("parallax_workspace") != workspace_id:
            response.set_cookie(
                "parallax_workspace", workspace_id, max_age=60 * 60 * 24 * 30,
                httponly=True, samesite="lax",
                secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
            )
        return response
    finally:
        ui_language.reset(token)


def workspace_service(request: Request) -> ParallaxService:
    """An anonymous browser keeps its own projects, actuals and learned calibration."""
    workspace_id = request.state.workspace_id
    with _workspace_lock:
        if workspace_id not in _workspace_services:
            data_path = DATA_PATH.parent / "workspaces" / f"{workspace_id}.json"
            _workspace_services[workspace_id] = ParallaxService(
                repository=StorageRepository(data_path=data_path), reader=service.reader,
            )
        return _workspace_services[workspace_id]

# Production UI is same-origin. Explicit origins support local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.environ.get(
        "PARALLAX_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ActualWorkCreate(BaseModel):
    actual_hours: float = Field(gt=0, allow_inf_nan=False)
    item_actuals: Optional[dict[str, float]] = None
    deviation_reasons: Optional[list[str]] = None
    requirement_actuals: Optional[dict[str, float]] = None


@app.exception_handler(AIReaderUnavailable)
def ai_unavailable(_request, exc: AIReaderUnavailable):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"detail": str(exc), "code": "AI_READER_UNAVAILABLE"})


@app.exception_handler(StorageError)
def storage_unavailable(_request, _exc: StorageError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"detail": "Workspace storage is unavailable. Your changes were not saved; please retry later.", "code": "STORAGE_UNAVAILABLE"})


def visitor_reader(
    x_jev_key: Optional[str] = Header(default=None, description="Your own Jev API key; used for this request only, never stored"),
    x_jev_provider: Optional[str] = Header(default=None, description="jevstation (default) or typesafe"),
):
    if x_jev_key and x_jev_key.strip():
        return service.reader.with_key(x_jev_key, (x_jev_provider or "jevstation").strip().lower())
    return None


def _report_visitor_credits(response: Response, reader) -> None:
    if reader is not None and reader.keys and reader.keys[0].credits is not None:
        response.headers["X-Jev-Credits-Remaining"] = str(reader.keys[0].credits)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "parallax-estimator-api",
        "version": RELEASE,
        "projects_count": len(repo.list_projects()),
        "historical_cases_count": len(repo.list_historical_cases()),
    }


@app.get("/api/v1/system/status", tags=["System"])
def system_status(workspace: ParallaxService = Depends(workspace_service)):
    """Live facts for the UI header: dataset, calibration state, last benchmark."""
    return workspace.system_status()


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
def create_project(payload: ProjectCreate, workspace: ParallaxService = Depends(workspace_service)):
    try:
        project = workspace.create_project(
            title=payload.title,
            brief_text=payload.brief_text,
            project_type=payload.project_type,
            documents=payload.documents,
        )
        return project
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/projects", response_model=list[Project], tags=["Projects"])
def list_projects(workspace: ParallaxService = Depends(workspace_service)):
    return workspace.repo.list_projects()


@app.get("/api/v1/projects/{project_id}", response_model=Project, tags=["Projects"])
def get_project(project_id: str, workspace: ParallaxService = Depends(workspace_service)):
    project = workspace.repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/api/v1/projects/{project_id}/estimate", response_model=EstimateVersion, tags=["Estimation"])
def estimate_project(project_id: str, request: Request, response: Response, reader=Depends(visitor_reader),
                     workspace: ParallaxService = Depends(workspace_service)):
    enforce_estimate_limit(request)
    try:
        version = workspace.estimate_project(project_id, reader=reader)
        _report_visitor_credits(response, reader)
        return version
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except AIReaderUnavailable:
        raise
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/v1/projects/{project_id}/wbs", response_model=EstimateVersion, tags=["Estimation"])
def update_wbs(project_id: str, payload: ManualEdits, request: Request, reader=Depends(visitor_reader),
               workspace: ParallaxService = Depends(workspace_service)):
    """Replace the user's WBS edits (hours, names, removed and added items) and re-estimate."""
    enforce_estimate_limit(request)
    try:
        return workspace.update_wbs(project_id, payload.model_dump(exclude_none=True), reader=reader)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _latest(project_id: str, workspace: ParallaxService) -> tuple[Project, EstimateVersion]:
    project = workspace.repo.get_project(project_id)
    versions = workspace.repo.get_versions(project_id) if project else []
    if not project or not versions:
        raise HTTPException(status_code=404, detail="Project or estimate not found")
    return project, versions[-1]


def _download_name(project: Project, ext: str, lang: str) -> str:
    stem = "estimate" if lang == "en" else "du-toan"
    return f"{stem}-{project.project_id}.{ext}"


@app.get("/api/v1/projects/{project_id}/export/proposal.md", tags=["Deliverables"])
def export_proposal(project_id: str, confidence: float = Query(80, ge=50, le=95), rate: float = Query(500_000, ge=0),
                    currency: str = Query("VND", pattern="^(VND|USD)$"), people: int = Query(3, ge=1, le=50),
                    lang: str = Query("vi", pattern="^(vi|en)$"),
                    workspace: ParallaxService = Depends(workspace_service)):
    project, version = _latest(project_id, workspace)
    body = proposal_markdown(project, version, confidence, rate, currency, people, lang)
    return Response(body, media_type="text/markdown; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{_download_name(project, "md", lang)}"'} )


@app.get("/api/v1/projects/{project_id}/export/wbs.csv", tags=["Deliverables"])
def export_wbs(project_id: str, lang: str = Query("vi", pattern="^(vi|en)$"),
               workspace: ParallaxService = Depends(workspace_service)):
    project, version = _latest(project_id, workspace)
    return Response(wbs_csv(version, lang), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{_download_name(project, "csv", lang)}"'} )


@app.get("/api/v1/reader/evaluation", tags=["Evaluation"])
def reader_evaluation(workspace: ParallaxService = Depends(workspace_service)):
    """Measured accuracy of the scope readers on the hand-labelled held-out clause set."""
    out = {}
    for key, name in (("held_out", "reader_results_v1_heldout.json"), ("latest", "reader_results_latest.json")):
        path = ROOT_DIR / "datasets" / "eval" / name
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            out[key] = {k: data.get(k) for k in ("note", "model", "thresholds", "summary")}
    out["status"] = workspace.reader.status()
    out["feedback"] = workspace.feedback_summary()
    study = ROOT_DIR / "datasets" / "eval" / "sip_jev_study.json"
    out["sip_study"] = json.loads(study.read_text(encoding="utf-8")) if study.exists() else None
    for key, name in (("itemlet_replication", "itemlet_replication.json"), ("operational_replay", "sip_operational_replay.json"),
                      ("conformal", "sip_conformal_test.json"), ("hierarchical", "sip_model_test.json")):
        path = ROOT_DIR / "datasets" / "eval" / name
        out[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    out["learning"] = workspace.adjustments().as_dict()
    journal = ROOT_DIR / "datasets" / "eval" / "journal.jsonl"
    out["journal"] = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()] \
        if journal.exists() else []
    return out


@app.get("/api/v1/projects/{project_id}/versions", response_model=list[EstimateVersion], tags=["Estimation"])
def list_versions(project_id: str, workspace: ParallaxService = Depends(workspace_service)):
    if not workspace.repo.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace.repo.get_versions(project_id)


@app.get("/api/v1/projects/{project_id}/versions/{version_id}", response_model=EstimateVersion, tags=["Estimation"])
def get_version(project_id: str, version_id: str, workspace: ParallaxService = Depends(workspace_service)):
    version = workspace.repo.get_version(project_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@app.post("/api/v1/projects/{project_id}/clarify", response_model=EstimateVersion, tags=["Clarification"])
def answer_clarification(project_id: str, payload: ClarificationAnswer, request: Request, reader=Depends(visitor_reader),
                         workspace: ParallaxService = Depends(workspace_service)):
    enforce_estimate_limit(request)
    try:
        new_version = workspace.answer_clarification(
            project_id=project_id,
            question_id=payload.question_id,
            answer=payload.answer,
            notes=payload.notes,
            reader=reader,
        )
        return new_version
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except AIReaderUnavailable:
        raise
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/projects/{project_id}/actuals", tags=["Actuals & Learning"])
def record_actuals(project_id: str, payload: ActualWorkCreate, workspace: ParallaxService = Depends(workspace_service)):
    try:
        result = workspace.record_actuals(
            project_id=project_id,
            actual_hours=payload.actual_hours,
            item_actuals=payload.item_actuals,
            deviation_reasons=payload.deviation_reasons,
            requirement_actuals=payload.requirement_actuals,
        )
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/historical-cases", response_model=list[HistoricalCase], tags=["Historical Intelligence"])
def list_historical_cases(domain: Optional[str] = None, workspace: ParallaxService = Depends(workspace_service)):
    """Completed projects in this workspace (projects with recorded actuals)."""
    return workspace.repo.list_historical_cases(domain=domain)


@app.get("/api/v1/calibration", tags=["Actuals & Learning"])
def calibration_status(workspace: ParallaxService = Depends(workspace_service)):
    return workspace.calibration_status()


@app.get("/api/v1/datasets/sip", tags=["Historical Intelligence"])
def sip_dataset_summary():
    try:
        return empirical.dataset_summary()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/benchmark/run", tags=["Evaluation"])
def run_benchmark(workspace: ParallaxService = Depends(workspace_service)):
    try:
        return workspace.run_benchmark_suite()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


# Serve the built web UI from the same origin when it exists (production image).
# Mounted last so every API route above takes precedence.
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
