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


def fake_keys(*credits):
    return [jev.JevKey(f"KEY_{i}", "fake", "http://fake", "jev", f"secret{i}", credits=c)
            for i, c in enumerate(credits, start=1)]


class FakeReader(JevReader):
    """Simulates the JevStation API: <= 5 questions cost 1 credit, empty keys answer 402."""

    def __init__(self, credits=(50,), answer_keys_style="single", **kw):
        super().__init__(cache_path=None, keys=fake_keys(*credits), **kw)
        self.cache = {}
        self.bodies = []
        self.style = answer_keys_style

    def _post(self, key, body):
        if key.credits is not None and key.credits <= 0:
            raise jev.JevError("HTTP 402: not enough credits", 402)
        assert len(body["questions"]) <= jev.QUESTIONS_PER_CALL
        self.bodies.append((key.name, body))
        key.credits -= 1
        answers = {}
        for qkey, spec in body["questions"].items():
            out_key = qkey if self.style == "single" else "broken_" + qkey
            if spec["type"] == "choice":
                answers[out_key] = {"type": "choice", "choice": "reporting", "confidence": 0.9,
                                    "probabilities": {"reporting": 0.9}}
            else:
                answers[out_key] = {"type": "noul", "noul": 0.8 if qkey.endswith("overrun") else 0.1}
        return {"model": "jev-test", "answers": answers, "credits": {"charged": 1, "remaining": key.credits}}


def test_reader_packs_five_questions_per_call_and_caches():
    r = FakeReader()
    texts = [f"Báo cáo số {i}" for i in range(5)]
    out = r.read(texts)
    assert len(out) == 5 and out[texts[0]].extra["overrun"] == 0.8
    assert len(r.bodies) == 3  # 5 clauses x 3 questions = 15 questions = 3 calls of 5
    assert all(len(b["questions"]) == 5 for _, b in r.bodies)
    r.read(texts)
    assert len(r.bodies) == 3, "cached answers must not be re-sent"


def test_new_question_only_costs_the_new_question():
    r = FakeReader()
    text = "Báo cáo doanh thu"
    r.cache[jev._legacy_key(text)] = jev.asdict(reading("reporting"))  # old kind+tentative reading
    r.read([text])
    (_, body), = r.bodies
    assert list(body["questions"]) == ["c0_overrun"]


def test_pool_fails_over_to_next_key_when_one_is_empty():
    r = FakeReader(credits=(0, 3))
    out = r.read([f"x{i}" for i in range(5)])  # 3 calls needed
    assert len(out) == 5
    assert {name for name, _ in r.bodies} == {"KEY_2"}
    assert r.keys[0].credits == 0 and r.keys[1].credits == 0
    assert r.credits_charged == 3


def test_reader_respects_credit_floor_and_hourly_cap():
    low = FakeReader(credits=(5,), min_credits=4)
    low.read([f"a{i}" for i in range(6)])
    assert low.credits_remaining == 4 and not low.status()["available"]
    capped = FakeReader(max_calls_per_hour=1)
    capped.read(["b1", "b2", "b3", "b4"])
    assert len(capped.bodies) == 1


def test_reader_halts_when_paid_answers_cannot_be_parsed():
    r = FakeReader(answer_keys_style="broken")
    assert r.read([f"t{i}" for i in range(10)]) == {}
    assert len(r.bodies) == 1, "a charged call with no usable answers must stop all further spending"
    assert r.status()["halted"]


def test_disabled_reader_never_calls(monkeypatch):
    monkeypatch.setenv("JEV_DISABLED", "1")
    monkeypatch.setenv("JEVSTATION_API_KEY", "x")
    r = JevReader()
    assert not r.configured and r.read(["anything"]) == {}


def test_key_pool_discovers_numbered_keys(monkeypatch):
    monkeypatch.delenv("JEV_DISABLED", raising=False)
    monkeypatch.setenv("JEVSTATION_API_KEY", "a")
    monkeypatch.setenv("JEVSTATION_API_KEY_10", "c")
    monkeypatch.setenv("JEVSTATION_API_KEY_2", "b")
    monkeypatch.setenv("JEVSTATION_API_KEY_3", "b")  # duplicate secret counted once
    names = [k.name for k in jev.discover_keys()]
    assert names == ["JEVSTATION_API_KEY", "JEVSTATION_API_KEY_2", "JEVSTATION_API_KEY_10"]
    assert all("secret" not in str(k.public()) for k in jev.discover_keys())


def test_estimate_requires_ai_reader(monkeypatch, tmp_path):
    from parallax.service import AIReaderUnavailable, ParallaxService
    from parallax.storage import StorageRepository

    monkeypatch.setenv("JEV_REQUIRED", "1")
    svc = ParallaxService(StorageRepository(tmp_path / "s.json"), reader=FakeReader(credits=(0,)))
    p = svc.create_project("P", "- Quản lý khách hàng.\n- Báo cáo doanh thu.")
    with pytest.raises(AIReaderUnavailable, match="2/2"):
        svc.estimate_project(p.project_id)
    ok = ParallaxService(StorageRepository(tmp_path / "t.json"), reader=FakeReader())
    p = ok.create_project("P", "- Quản lý khách hàng.\n- Báo cáo doanh thu.")
    v = ok.estimate_project(p.project_id)
    assert v.reader == "rules+jev"
    assert all(r.ai_reading and r.ai_reading["overrun"] == 0.8 for r in v.requirements if r.req_id != "REQ-00")


def test_disabled_reader_never_overwrites_cache_file(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text('{"k": {"kind": "auth"}}', encoding="utf-8")
    monkeypatch.setenv("JEV_DISABLED", "1")
    r = JevReader(cache_path=cache_file)
    r.read(["a clause nobody has read"])
    assert cache_file.read_text(encoding="utf-8") == '{"k": {"kind": "auth"}}'


@pytest.mark.parametrize(
    "text, tentative",
    [
        ("Anh chị đang cân nhắc có làm thêm app cho phụ huynh hay không.", True),
        ("If budget allows, we would like a chatbot.", True),
        ("Hệ thống cần nhắc lịch hẹn cho bệnh nhân.", False),  # "cần nhắc" (remind) folds like "cân nhắc"
        ("Kiểm tra khách đã thanh toán hay không.", False),
        # round 5 (dev)
        ("Chatbot trả lời câu hỏi giá dịch vụ thì để xem ngân sách đã.", True),
        ("Ben em dang tinh co nen ket noi voi MISA khong.", True),
        ("Down the line we may want to plug this into our ERP.", True),
        ("Not sure yet whether we need a mobile app.", True),
        ("Support agents can search returns by order number.", False),
        ("Nhân viên có thể tìm bệnh nhân theo số điện thoại.", False),
    ],
)
def test_round4_hedges(text, tentative):
    from parallax.extractor import _HEDGES, fold

    assert bool(_HEDGES.search(fold(text))) is tentative


def test_round4_migration_and_search_patterns():
    from parallax.extractor import _match_components

    keys = {c.key for c in _match_components("Chuyển dữ liệu khách hàng từ file Excel cũ sang hệ thống mới.")}
    assert "migration" in keys
    assert "search" in {c.key for c in _match_components("Tìm hồ sơ ứng viên theo kỹ năng và mức lương.")}


def test_rejected_ai_suggestions_get_muted(tmp_path):
    from parallax.service import ParallaxService
    from parallax.storage import StorageRepository

    clause = "Quản lý dự án: tạo dự án, gán người phụ trách, theo dõi tiến độ."
    fake = FakeReader()
    fake.cache[jev._legacy_key(clause)] = jev.asdict(reading("scheduling"))
    fake.cache[jev._cache_key(clause, jev.OVERRUN_Q)] = {"answer": {"noul": 0.2}, "model": "jev-test"}
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
