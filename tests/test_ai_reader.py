"""AI reader (Jev) integration: merging rules with readings, caching and spend guards. No network."""
import pytest

from parallax import jev
from parallax.extractor import extract_scope_and_wbs
from parallax.jev import ClauseReading, JevReader


def reading(kind, conf=0.95, tentative=0.05):
    return ClauseReading(kind=kind, kind_confidence=conf, kind_probabilities={kind: conf}, tentative=tentative,
                         model="jev-test", provider="fake")


def feature_reqs(version):
    return [r for r in version.requirements if r.req_id != "REQ-00"]


def test_rules_bug_fixes_vietnamese_ai_and_phone_number():
    v = extract_scope_and_wbs("p", "- Lưu lại lịch sử ai đã sửa hồ sơ nào.\n- Khách đăng ký bằng số điện thoại.")
    comps = {c for r in feature_reqs(v) for c in r.components}
    assert "ai" not in comps and "mobile" not in comps
    v2 = extract_scope_and_wbs("p", "- Trợ lý AI tóm tắt cuộc họp.")
    assert "ai" in feature_reqs(v2)[0].components


def test_ai_kind_used_when_rules_find_nothing():
    clause = "Tính hoa hồng cho cộng tác viên theo bậc thang."
    rules_only = extract_scope_and_wbs("p", f"- {clause}")
    assert feature_reqs(rules_only)[0].components == ["generic"]
    v = extract_scope_and_wbs("p", f"- {clause}", readings={clause: reading("data_management")})
    req = feature_reqs(v)[0]
    assert req.components == ["crud"]
    assert req.ai_reading["added_component"] == "crud"
    assert v.reader == "rules+jev" and v.reader_model == "jev-test"


def test_ai_extra_kind_becomes_question_not_hours():
    clause = "Quản lý dự án: tạo dự án, gán người phụ trách, theo dõi tiến độ."
    brief = f"- {clause}"
    base = extract_scope_and_wbs("p", brief)
    v = extract_scope_and_wbs("p", brief, readings={clause: reading("scheduling")})
    q = next(q for q in v.clarifications if q.question_id.endswith("-AI"))
    assert q.current_assumption is False and q.hours_if_true > 0
    assert v.forecast.p50_hours == pytest.approx(base.forecast.p50_hours, rel=0.01)
    yes = extract_scope_and_wbs("p", brief, readings={clause: reading("scheduling")},
                                clarification_answers={q.question_id: True})
    assert yes.forecast.p50_hours > v.forecast.p50_hours
    assert any("SCHEDULING" in w.item_id for w in yes.wbs)


def test_ai_tentative_reading_creates_scope_question():
    clause = "Phần tích điểm cho khách thân thiết thì để anh hỏi lại sếp."
    v = extract_scope_and_wbs("p", f"- {clause}", readings={clause: reading("data_management", tentative=0.95)})
    req = feature_reqs(v)[0]
    assert req.status.value == "assumed" and req.ai_reading["flagged_tentative"] is True
    q = next(q for q in v.clarifications if q.question_id == f"CLAR-{req.req_id}")
    assert "AI" in q.context_reason


def test_low_confidence_reading_is_ignored():
    clause = "Tính hoa hồng cho cộng tác viên theo bậc thang."
    v = extract_scope_and_wbs("p", f"- {clause}", readings={clause: reading("auth", conf=0.3, tentative=0.4)})
    req = feature_reqs(v)[0]
    assert req.components == ["generic"] and req.status.value == "confirmed"


class FakeReader(JevReader):
    def __init__(self, credits=50, **kw):
        super().__init__(cache_path=None, **kw)
        self.provider, self.url, self.key = "fake", "http://fake", "k"
        self.cache = {}
        self.credits = credits
        self.batches = []

    def _call(self, batch):
        self.batches.append(batch)
        self.credits -= 1
        self.credits_remaining = self.credits
        out = {t: reading("reporting") for t in batch}
        for t, r in out.items():
            self.cache[jev._cache_key(t)] = jev.asdict(r)
        return out


def test_reader_caches_and_batches():
    r = FakeReader()
    texts = [f"Báo cáo số {i}" for i in range(5)]
    assert len(r.read(texts)) == 5
    assert len(r.batches) == 3  # 2 + 2 + 1 clauses per call
    r.read(texts)
    assert len(r.batches) == 3, "cached clauses must not be re-sent"


def test_reader_respects_credit_floor_and_hourly_cap():
    low = FakeReader(credits=5, min_credits=4)
    low.read(["a1", "a2", "a3", "a4", "a5", "a6"])
    assert low.credits_remaining == 4 and not low.status()["available"]
    capped = FakeReader(max_calls_per_hour=1)
    capped.read(["b1", "b2", "b3", "b4"])
    assert len(capped.batches) == 1


def test_disabled_reader_never_calls(monkeypatch):
    monkeypatch.setenv("JEV_DISABLED", "1")
    monkeypatch.setenv("JEVSTATION_API_KEY", "x")
    r = JevReader()
    assert not r.configured and r.read(["anything"]) == {}


def test_rejected_ai_suggestions_get_muted(tmp_path):
    from parallax.service import ParallaxService
    from parallax.storage import StorageRepository

    clause = "Quản lý dự án: tạo dự án, gán người phụ trách, theo dõi tiến độ."
    fake = FakeReader()
    fake.cache[jev._cache_key(clause)] = jev.asdict(reading("scheduling"))
    svc = ParallaxService(StorageRepository(tmp_path / "s.json"), reader=fake)
    for i in range(3):
        p = svc.create_project(f"P{i}", f"- {clause}")
        v = svc.estimate_project(p.project_id)
        q = next(q for q in v.clarifications if q.question_id.endswith("-AI"))
        svc.answer_clarification(p.project_id, q.question_id, False)
    summary = svc.feedback_summary()
    assert summary["answered"] == 3 and summary["accepted"] == 0
    assert summary["by_component"][0]["muted"] is True
    p = svc.create_project("After", f"- {clause}")
    v = svc.estimate_project(p.project_id)
    assert not any(q.question_id.endswith("-AI") for q in v.clarifications), "muted kinds are no longer suggested"
