"""Tests for the empirical (real SiP data) layer, the generic extractor and the learning loop."""
from datetime import date

import pytest

from parallax import empirical
from parallax.extractor import extract_scope_and_wbs, fold, segment
from parallax.provenance import validate_evidence_against_sources
from parallax.service import ParallaxService, shrunk_multiplier
from parallax.storage import StorageRepository

TECH_BRIEF = """Dự án: Ứng dụng điều phối kỹ thuật viên bảo trì điều hòa.
- Điều phối viên xếp lịch và phân công kỹ thuật viên theo khu vực, kỹ năng và ca làm.
- Kỹ thuật viên dùng điện thoại để nhận việc, chụp ảnh hiện trường và cập nhật trạng thái kể cả khi offline, tự đồng bộ khi có mạng.
- Gửi thông báo SMS/Zalo cho khách hàng khi kỹ thuật viên đang trên đường tới.
- Nhập danh sách khách hàng và thiết bị từ file CSV hiện có.
- Có thể cần thêm báo cáo năng suất kỹ thuật viên theo tháng."""


# ---------------------------------------------------------------- dataset ---
def test_sip_dataset_loads_real_tasks():
    tasks = empirical.load_sip_tasks()
    assert len(tasks) > 9000
    assert all(t.estimate_hours > 0 and t.actual_hours > 0 for t in tasks[:500])
    assert tasks[0].estimated_on < date(2005, 1, 1) < tasks[-1].estimated_on


def test_ratio_model_is_fitted_only_on_past_data():
    tasks = empirical.load_sip_tasks()
    train = [(t.estimate_hours, t.actual_hours) for t in tasks if t.estimated_on < empirical.HOLDOUT_CUTOFF]
    model = empirical.RatioQuantileModel.fit(train)
    p10, p50, p90 = model.predict(100.0)
    assert p10 <= p50 <= p90
    report = empirical.run_sip_benchmark()
    assert report["holdout"]["n_train"] == len(train)
    assert report["holdout"]["test_period"].startswith(str(empirical.HOLDOUT_CUTOFF.year))


def test_calibrated_forecast_beats_raw_estimates_on_holdout():
    holdout = empirical.run_sip_benchmark()["holdout"]
    assert holdout["calibrated"]["mae"] < holdout["baseline"]["mae"]
    # An 80% central interval should cover roughly 80% of unseen tasks.
    assert 70 <= holdout["calibrated"]["interval_coverage"] <= 90


def test_systemic_pool_is_centered_real_spread():
    pool = empirical.systemic_ratio_pool()
    assert len(pool) >= 30
    assert sorted(pool)[len(pool) // 2] == pytest.approx(1.0, abs=0.05)


# -------------------------------------------------------------- extractor ---
def test_fold_handles_vietnamese_diacritics():
    assert fold("Đăng nhập") == "dang nhap"


def test_segment_keeps_exact_clauses():
    clauses = segment("brief.txt", TECH_BRIEF)
    assert clauses[0].is_title
    assert all(c.text in TECH_BRIEF for c in clauses)
    assert sum(c.is_item for c in clauses) == 5


def test_free_form_brief_is_fully_covered():
    v = extract_scope_and_wbs("P-TECH", TECH_BRIEF)
    validate_evidence_against_sources(v, {"brief.txt": TECH_BRIEF})
    feature_reqs = [r for r in v.requirements if r.req_id != "REQ-00"]
    assert len(feature_reqs) == 5, "every bullet becomes a requirement"
    components = {c for r in feature_reqs for c in r.components}
    assert {"scheduling", "mobile", "offline", "notification", "import", "reporting"} <= components
    assert "integration" not in components, "offline self-sync is not an external integration"
    names = " ".join(w.name for w in v.wbs).lower()
    assert "erp" not in names
    # Every work item traces to a requirement that exists
    req_ids = {r.req_id for r in v.requirements}
    assert all(set(w.req_ids) <= req_ids for w in v.wbs)


def test_tentative_wording_becomes_scope_question():
    v = extract_scope_and_wbs("P-TECH", TECH_BRIEF)
    report_req = next(r for r in v.requirements if "reporting" in r.components)
    assert report_req.status.value == "assumed"
    q = next(q for q in v.clarifications if q.question_id == f"CLAR-{report_req.req_id}")
    assert q.hours_if_true > 0 and q.hours_if_false == 0
    v_no = extract_scope_and_wbs("P-TECH", TECH_BRIEF, clarification_answers={q.question_id: False})
    assert v_no.forecast.p50_hours < v.forecast.p50_hours
    assert next(r for r in v_no.requirements if r.req_id == report_req.req_id).in_scope is False
    assert next(x for x in v_no.clarifications if x.question_id == q.question_id).answer is False


def test_english_brief_and_generic_fallback():
    brief = "We need a portal where members can rate local bakeries. Admins must approve reviews."
    v = extract_scope_and_wbs("P-EN", brief)
    validate_evidence_against_sources(v, {"brief.txt": brief})
    assert len([r for r in v.requirements if r.req_id != "REQ-00"]) == 2
    assert v.forecast.p50_hours > 0


def test_unclassified_requirement_is_flagged_not_dropped():
    brief = "- Hệ thống phải tính điểm thưởng theo quy tắc riêng của từng chi nhánh."
    v = extract_scope_and_wbs("P-X", brief)
    assert any(r.components == ["generic"] for r in v.requirements)
    assert any(c.category == "estimation_risk" for c in v.critic_findings)


# -------------------------------------------------------- learning loop ---
def test_shrinkage_moves_gradually_and_is_bounded():
    assert shrunk_multiplier([], 3) == 1.0
    one = shrunk_multiplier([0.4], 3)
    many = shrunk_multiplier([0.4] * 20, 3)
    assert 1.0 < one < many < 1.5
    assert shrunk_multiplier([5.0] * 50, 3) == 2.0


def test_record_actuals_updates_calibration(tmp_path):
    repo = StorageRepository(tmp_path / "s.json")
    svc = ParallaxService(repo)
    p = svc.create_project("A", TECH_BRIEF, "field_service")
    v1 = svc.estimate_project(p.project_id)
    out = svc.record_actuals(p.project_id, v1.forecast.p50_hours * 0.7)
    assert out["calibration"]["multiplier_after"] < 1.0
    # Persisted across restarts
    assert StorageRepository(tmp_path / "s.json").get_calibration().multiplier == pytest.approx(abs=1e-4, expected=
        out["calibration"]["multiplier_after"]
    )
    # Re-recording the same project replaces, not duplicates, the observation
    svc.record_actuals(p.project_id, v1.forecast.p50_hours * 0.8)
    assert len(repo.get_calibration().observations) == 1


def test_reference_class_needs_five_real_projects(tmp_path):
    svc = ParallaxService(StorageRepository(tmp_path / "s.json"))
    for i in range(5):
        p = svc.create_project(f"P{i}", TECH_BRIEF, "field_service")
        v = svc.estimate_project(p.project_id)
        svc.record_actuals(p.project_id, v.forecast.p50_hours)
    new = svc.create_project("New", TECH_BRIEF, "field_service")
    v = svc.estimate_project(new.project_id)
    assert v.forecast.insufficient_historical_evidence is False
    assert v.forecast.reference_class_p50 is not None
