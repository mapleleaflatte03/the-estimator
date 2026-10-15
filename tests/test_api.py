"""Integration tests for the PARALLAX FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from parallax.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "parallax-estimator-api"
    assert data["historical_cases_count"] >= 5


def test_full_project_lifecycle_api():
    brief_content = (
        "Cần xây dựng một cổng thông tin quản lý dự án cho doanh nghiệp. "
        "Yêu cầu hỗ trợ SSO login qua Google OAuth và email công ty. "
        "Có tính năng báo cáo tiến độ và bảng điều khiển dashboard thống kê. "
        "Hệ thống có thể cần kết nối với hệ thống legacy ERP cũ để đối soát dữ liệu."
    )

    # 1. Create project
    create_resp = client.post(
        "/api/v1/projects",
        json={
            "title": "Corporate Project Management Portal",
            "project_type": "internal_tool",
            "brief_text": brief_content,
        },
    )
    assert create_resp.status_code == 201
    project = create_resp.json()
    project_id = project["project_id"]
    assert project["status"] == "intake"

    # 2. Estimate project (generates v1)
    est_resp = client.post(f"/api/v1/projects/{project_id}/estimate")
    assert est_resp.status_code == 200
    v1 = est_resp.json()
    assert v1["version_id"] == "v1"
    assert v1["project_id"] == project_id
    assert v1["parent_version_id"] is None
    assert len(v1["requirements"]) >= 3
    assert len(v1["wbs"]) >= 5
    assert len(v1["clarifications"]) >= 1

    # Verify forecast quantiles
    forecast = v1["forecast"]
    assert forecast["p10_hours"] <= forecast["p50_hours"] <= forecast["p80_hours"] <= forecast["p90_hours"]
    assert forecast["bottom_up_p50"] > 0

    # 3. Active Clarification: Answer ERP question -> creates v2
    clar_resp = client.post(
        f"/api/v1/projects/{project_id}/clarify",
        json={
            "question_id": "CLAR-ERP",
            "answer": False,
            "notes": "No ERP integration needed; export CSV is sufficient.",
        },
    )
    assert clar_resp.status_code == 200
    v2 = clar_resp.json()
    assert v2["version_id"] == "v2"
    assert v2["parent_version_id"] == "v1"

    # Since ERP was false, estimate should be lower than when ERP was included
    assert v2["forecast"]["p50_hours"] < v1["forecast"]["p50_hours"]

    # 4. Check version history: immutability verified (v1 unchanged, v2 appended)
    versions_resp = client.get(f"/api/v1/projects/{project_id}/versions")
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 2
    assert versions[0]["version_id"] == "v1"
    assert versions[1]["version_id"] == "v2"

    # 5. Ingest Actuals: compare against baseline v1
    actual_resp = client.post(
        f"/api/v1/projects/{project_id}/actuals",
        json={
            "actual_hours": 175.0,
            "deviation_reasons": ["Frontend scope simplified, testing completed faster"],
        },
    )
    assert actual_resp.status_code == 200
    actual_data = actual_resp.json()
    assert actual_data["baseline_version_id"] == "v1"
    assert actual_data["actual_hours"] == 175.0
    assert "delta_hours" in actual_data


def test_benchmark_api_endpoint():
    resp = client.post("/api/v1/benchmark/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_name"] == "PARALLAX-Baseline-v1"
    assert data["n_cases"] >= 10
    assert data["mae"] > 0
    assert 0 <= data["interval_coverage"] <= 100
