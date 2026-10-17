"""Jev overrun reading -> hours (SiP prior) and learning from per-requirement actuals."""
import pytest

from parallax import risk
from parallax.extractor import extract_scope_and_wbs
from parallax.jev import ClauseReading

CLAUSE = "Quáº£n lÃ½ danh sÃ¡ch khÃ¡ch hÃ ng vÃ  Ä‘Æ¡n hÃ ng."


def reading(overrun):
    return ClauseReading(kind="data_management", kind_confidence=0.9, kind_probabilities={}, tentative=0.05,
                         model="jev-test", provider="fake", extra={"overrun": overrun})


def req(version):
    return next(r for r in version.requirements if r.req_id != "REQ-00")


def test_sip_prior_is_loaded_and_ordered():
    prior = risk.sip_prior()
    assert prior is not None and prior.question == "overrun@v1"
    assert prior.factors[0] == 1.0 < prior.factors[1] < prior.factors[2]
    assert prior.thresholds[0] <= prior.thresholds[1]


def test_high_overrun_reading_adds_hours_and_explains_why():
    adj = risk.learn([])
    low = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.1)}, adjustments=adj)
    high = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj)
    assert req(low).risk_group == 0 and req(high).risk_group == 2
    assert req(low).estimated_hours_raw == req(high).estimated_hours_raw
    assert req(high).adjustment_factor > 1.2 and req(low).adjustment_factor == 1.0
    assert high.forecast.p50_hours > low.forecast.p50_hours
    assert any(f.category == "overrun_risk" for f in high.critic_findings)


def test_user_edit_wins_over_learned_factor():
    adj = risk.learn([])
    v = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj)
    item = next(w for w in v.wbs if w.component == "crud")
    edited = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj,
                                   manual_edits={"overrides": {item.item_id: {"hours": 50}}})
    e = next(w for w in edited.wbs if w.item_id == item.item_id)
    assert (e.optimistic_hours + 4 * e.most_likely_hours + e.pessimistic_hours) / 6 == pytest.approx(50, abs=1)


def test_requirement_actuals_teach_component_factors(tmp_path):
    from parallax.service import ParallaxService
    from parallax.storage import StorageRepository

    svc = ParallaxService(StorageRepository(tmp_path / "s.json"))
    base = None
    for i in range(4):
        p = svc.create_project(f"P{i}", "- BÃ¡o cÃ¡o doanh thu theo thÃ¡ng.\n- Gá»­i email nháº¯c lá»‹ch háº¹n.")
        v = svc.estimate_project(p.project_id)
        if base is None:
            base = v
        reqs = [r for r in v.requirements if r.req_id != "REQ-00"]
        report = next(r for r in reqs if "reporting" in r.components)
        other = next(r for r in reqs if r is not report)
        # Reporting keeps taking twice as long as estimated; the other requirement is on target.
        # Factors are relative (centred), so reporting ends up above 1 and the other below 1.
        result = svc.record_actuals(p.project_id, v.forecast.p50_hours,
                                    requirement_actuals={report.req_id: report.estimated_hours_raw * 2,
                                                         other.req_id: other.estimated_hours_raw})
        assert result["learning"]["requirements_recorded"] == 2
    learned = svc.adjustments()
    assert learned.component_factors["reporting"] > 1.15
    assert learned.component_observations["reporting"] == 4
    p = svc.create_project("After", "- BÃ¡o cÃ¡o doanh thu theo thÃ¡ng.\n- Gá»­i email nháº¯c lá»‹ch háº¹n.")
    after = svc.estimate_project(p.project_id)
    hours = lambda v, comp: sum(w.most_likely_hours for w in v.wbs if w.component == comp)  # noqa: E731
    assert hours(after, "reporting") > hours(base, "reporting") * 1.15
    with pytest.raises(ValueError):
        svc.record_actuals(p.project_id, 10, requirement_actuals={"REQ-99": 5})
