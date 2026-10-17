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
    assert prior.factors[0] == 1.0 < prior.factors[1] < prior.factors[2]  # kept as evidence, not applied
    assert prior.thresholds[0] <= prior.thresholds[1]


def test_high_overrun_reading_is_flagged_without_adding_hours_by_default():
    # SiP factors did not transfer to other organisations (Itemlet replication), so the default is a flag only.
    adj = risk.learn([])
    low = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.1)}, adjustments=adj)
    high = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj)
    assert req(low).risk_group == 0 and req(high).risk_group == 2
    assert req(high).adjustment_factor == req(low).adjustment_factor == 1.0
    flag = next(f for f in high.critic_findings if f.category == "overrun_risk")
    assert flag.action_taken == "flagged_for_human_review"


def test_overrun_hours_come_from_the_teams_own_actuals():
    class Obs:
        def __init__(self, g, ratio):
            import math
            self.risk_group, self.components, self.log_ratio = g, ["crud"], math.log(ratio)

    # Flagged requirements kept taking 1.6x their estimate, the others were on target.
    adj = risk.learn([Obs(2, 1.6)] * 6 + [Obs(0, 1.0)] * 6)
    assert adj.group_factors[2] > 1.1 and adj.group_factors[0] < 1.0
    high = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj)
    assert req(high).adjustment_factor > 1.1
    assert next(f for f in high.critic_findings if f.category == "overrun_risk").action_taken == "applied_to_wbs"


def test_user_edit_wins_over_learned_factor():
    adj = risk.learn([])
    v = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj)
    item = next(w for w in v.wbs if w.component == "crud")
    edited = extract_scope_and_wbs("p", f"- {CLAUSE}", readings={CLAUSE: reading(0.95)}, adjustments=adj,
                                   manual_edits={"overrides": {item.item_id: {"hours": 50}}})
    e = next(w for w in edited.wbs if w.item_id == item.item_id)
    assert (e.optimistic_hours + 4 * e.most_likely_hours + e.pessimistic_hours) / 6 == pytest.approx(50, abs=1)


def test_ranges_widen_after_misses_and_narrow_after_hits(tmp_path):
    from parallax.service import ParallaxService
    from parallax.storage import StorageRepository

    svc = ParallaxService(StorageRepository(tmp_path / "s.json"))
    brief = "- Báo cáo doanh thu theo tháng.\n- Gửi email nhắc lịch hẹn."
    first = None
    for i in range(3):  # three projects finishing far outside their range
        p = svc.create_project(f"P{i}", brief)
        v = svc.estimate_project(p.project_id)
        first = first or v
        r = svc.record_actuals(p.project_id, v.forecast.p90_hours * 3)
    assert r["calibration"]["range_level_after"] > 0.8 and r["calibration"]["range_checks"] == 3
    p = svc.create_project("After misses", brief)
    wide = svc.estimate_project(p.project_id).forecast
    assert wide.range_percentiles[0] < 10 and wide.range_percentiles[1] > 90
    width = lambda f: (f.p90_hours - f.p10_hours) / f.p50_hours  # noqa: E731
    assert width(wide) > width(first.forecast)


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
