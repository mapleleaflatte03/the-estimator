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
    # Reference class contains only real completed projects: nothing is seeded.
    assert data["historical_cases_count"] >= 0


def test_store_is_isolated_from_workspace():
    from parallax.main import DATA_PATH

    assert "parallax-test-" in str(DATA_PATH)


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

    # 3. Active Clarification: the tentative ERP clause ("có thể cần") becomes a scope question
    erp_q = next(q for q in v1["clarifications"] if any("ERP" in ev["quote"] for ev in q["evidence"]))
    assert erp_q["sensitivity_spread_hours"] > 0
    clar_resp = client.post(
        f"/api/v1/projects/{project_id}/clarify",
        json={
            "question_id": erp_q["question_id"],
            "answer": False,
            "notes": "No ERP integration needed; export CSV is sufficient.",
        },
    )
    assert clar_resp.status_code == 200
    v2 = clar_resp.json()
    assert v2["version_id"] == "v2"
    assert v2["parent_version_id"] == "v1"
    assert v2["clarification_answers"] == {erp_q["question_id"]: False}
    assert v2["forecast"]["p50_hours"] < v1["forecast"]["p50_hours"]
    v2_erp = next(q for q in v2["clarifications"] if q["question_id"] == erp_q["question_id"])
    assert v2_erp["answer"] is False

    # Unknown question ids are rejected instead of silently creating versions
    bad = client.post(f"/api/v1/projects/{project_id}/clarify", json={"question_id": "CLAR-NOPE", "answer": True})
    assert bad.status_code == 400

    # 4. Version history is append-only
    versions = client.get(f"/api/v1/projects/{project_id}/versions").json()
    assert [v["version_id"] for v in versions] == ["v1", "v2"]

    # 5. Actuals close the loop: calibration multiplier is updated and persisted
    before = client.get("/api/v1/calibration").json()
    actual_hours = v2["forecast"]["p50_hours"] * 1.5
    actual_data = client.post(
        f"/api/v1/projects/{project_id}/actuals",
        json={"actual_hours": actual_hours, "deviation_reasons": ["Underestimated reporting"]},
    ).json()
    assert actual_data["baseline_version_id"] == "v2"
    assert actual_data["initial_version"]["version_id"] == "v1"
    cal = actual_data["calibration"]
    assert cal["multiplier_before"] == before["multiplier"]
    assert cal["multiplier_after"] > cal["multiplier_before"]
    after = client.get("/api/v1/calibration").json()
    assert after["multiplier"] == cal["multiplier_after"]

    # 6. A re-estimate now uses the learned multiplier; v1/v2 stay unchanged
    v3 = client.post(f"/api/v1/projects/{project_id}/estimate").json()
    # Re-estimates use the multiplier for this project's type (partially pooled with the global one)
    assert v3["forecast"]["calibration_multiplier"] == round(cal["type_multiplier_after"], 4)
    assert cal["type_multiplier_after"] >= cal["multiplier_after"] > 1.0
    assert v3["forecast"]["p50_hours"] > v2["forecast"]["p50_hours"]
    assert v3["clarification_answers"] == v2["clarification_answers"]
    assert client.get(f"/api/v1/projects/{project_id}/versions/v2").json() == v2

    # 7. Completed project now appears in the (real, unseeded) reference class
    cases = client.get("/api/v1/historical-cases").json()
    assert any(c["case_id"] == project_id for c in cases)


def test_benchmark_api_endpoint_uses_real_dataset():
    resp = client.post("/api/v1/benchmark/run")
    assert resp.status_code == 200
    data = resp.json()
    sip = data["sip"]
    assert sip["dataset"]["n_tasks"] > 9000
    holdout = sip["holdout"]
    assert holdout["n_test"] > 1000
    assert holdout["baseline"]["interval_coverage"] is None
    assert 0 <= holdout["calibrated"]["interval_coverage"] <= 100
    assert data["in_app"]["n_observations"] >= 0


def test_system_status_and_samples():
    status_resp = client.get("/api/v1/system/status").json()
    assert status_resp["dataset"]["available"] is True
    samples = client.get("/api/v1/sample-briefs").json()
    assert len(samples) >= 3 and all(s["brief_text"] for s in samples)


def test_wbs_edits_persist_across_versions():
    brief = "- Có thể cần thêm báo cáo doanh thu theo tháng.\n- Quản lý danh sách khách hàng và đơn hàng."
    pid = client.post("/api/v1/projects", json={"title": "Edit test", "brief_text": brief}).json()["project_id"]
    v1 = client.post(f"/api/v1/projects/{pid}/estimate").json()
    crud = next(w for w in v1["wbs"] if "CRUD-BE" in w["item_id"])
    report = next(w for w in v1["wbs"] if "REPORTING-FE" in w["item_id"])
    edits = {
        "overrides": {crud["item_id"]: {"hours": 80, "name": "API khách hàng & đơn hàng"}},
        "removed": [report["item_id"]],
        "added": [{"name": "Đào tạo người dùng", "hours": 12, "role": "QA"}],
    }
    resp = client.put(f"/api/v1/projects/{pid}/wbs", json=edits)
    assert resp.status_code == 200, resp.text
    v2 = resp.json()
    items = {w["item_id"]: w for w in v2["wbs"]}
    edited = items[crud["item_id"]]
    mean = (edited["optimistic_hours"] + 4 * edited["most_likely_hours"] + edited["pessimistic_hours"]) / 6
    assert abs(mean - 80) < 1 and edited["name"] == "API khách hàng & đơn hàng"
    assert report["item_id"] not in items
    assert any(w["name"] == "Đào tạo người dùng" for w in v2["wbs"])
    # Answering a clarification afterwards keeps the edits
    q = v2["clarifications"][0]["question_id"]
    v3 = client.post(f"/api/v1/projects/{pid}/clarify", json={"question_id": q, "answer": True}).json()
    assert v3["manual_edits"] == v2["manual_edits"]
    assert any(w["name"] == "API khách hàng & đơn hàng" for w in v3["wbs"])
    # Unknown ids are rejected
    bad = client.put(f"/api/v1/projects/{pid}/wbs", json={"overrides": {"NOPE-1": {"hours": 3}}})
    assert bad.status_code == 400


def test_exports_are_plain_language_and_excel_ready():
    brief = "- Có thể cần thêm báo cáo doanh thu theo tháng.\n- Gửi email nhắc lịch hẹn."
    pid = client.post("/api/v1/projects", json={"title": "Export test", "brief_text": brief}).json()["project_id"]
    client.post(f"/api/v1/projects/{pid}/estimate")
    md = client.get(f"/api/v1/projects/{pid}/export/proposal.md?confidence=80&rate=500000&people=2")
    assert md.status_code == 200 and "attachment" in md.headers["content-disposition"]
    text = md.text
    assert "# Dự toán: Export test" in text and "triệu đồng" in text and "Câu hỏi cần khách hàng xác nhận" in text
    assert "P50" not in text and "Monte Carlo" not in text
    csv_resp = client.get(f"/api/v1/projects/{pid}/export/wbs.csv")
    assert csv_resp.status_code == 200 and csv_resp.text.startswith("\ufeff")
    assert "Gửi email nhắc lịch hẹn." in csv_resp.text
    assert client.get("/api/v1/projects/NOPE/export/wbs.csv").status_code == 404


def test_reader_evaluation_endpoint():
    data = client.get("/api/v1/reader/evaluation").json()
    names = [s["reader"] for s in data["held_out"]["summary"]]
    assert names == ["rules", "jev", "hybrid", "shipped"]
    assert data["status"]["configured"] is False  # tests never call a paid provider
