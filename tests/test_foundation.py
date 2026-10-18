import pytest
from pydantic import ValidationError

from parallax.calibration import propose_multiplier, apply_multiplier
from parallax.export import hours_at
from parallax.estimation.engine import run_correlated_monte_carlo, synthesize_forecast
from parallax.evaluation.benchmark import (
    PredictionRecord,
    evaluate_predictions,
    calibration_gate_decision,
)
from parallax.provenance import validate_evidence_against_sources
from parallax.schemas import (
    CriticFinding,
    EvidenceSpan,
    EstimateVersion,
    ProbabilisticForecast,
    RequirementNode,
    VerificationStatus,
    WorkItem,
)


def work(item_id="WI-1", dependencies=None):
    return WorkItem(
        item_id=item_id, req_ids=["REQ-1"], name="API integration", role="Backend",
        dependencies=dependencies or [], optimistic_hours=12,
        most_likely_hours=20, pessimistic_hours=45,
    )


def test_require_confirmed_evidence():
    with pytest.raises(ValidationError):
        RequirementNode(req_id="REQ-1", title="SSO", description="SSO integration",
                        status=VerificationStatus.CONFIRMED, evidence=[])


def test_critic_cannot_auto_apply_unverified_finding():
    with pytest.raises(ValidationError):
        CriticFinding(finding_id="CR-1", category="omitted_qa", claim="Missing QA",
                      verified_by_evidence=False, action_taken="applied_to_wbs")


def test_three_point_order():
    with pytest.raises(ValidationError):
        WorkItem(item_id="WI-1", req_ids=["REQ-1"], name="Testing", role="QA",
                 optimistic_hours=30, most_likely_hours=20, pessimistic_hours=40)


def make_version(wbs, evidence_quote="The system must support SSO login."):
    return EstimateVersion(
        version_id="v1", project_id="p1", model_tag="P_v1",
        requirements=[RequirementNode(
            req_id="REQ-1", title="SSO", description="Single Sign-on",
            status=VerificationStatus.CONFIRMED,
            evidence=[EvidenceSpan(source_doc="brief.txt", quote=evidence_quote)],
        )],
        wbs=wbs,
        forecast=synthesize_forecast(wbs),
    )


def test_evidence_quote_checked_against_original_text():
    version = make_version([work()])
    validate_evidence_against_sources(version, {"brief.txt": "The system must support SSO login."})
    with pytest.raises(ValueError, match="not found"):
        validate_evidence_against_sources(version, {"brief.txt": "No SSO requirement mentioned"})


def test_graph_cycle_rejected():
    with pytest.raises(ValidationError, match="Cycle"):
        make_version([work("WI-1", ["WI-2"]), work("WI-2", ["WI-1"])])


def test_forecast_is_deterministic_and_sorted():
    a = run_correlated_monte_carlo([work()], seed=11)
    b = run_correlated_monte_carlo([work()], seed=11)
    assert a == b
    assert a["p10"] <= a["p50"] <= a["p80"] <= a["p90"]


def test_shared_risk_adds_uncertainty():
    many_items = [work(str(i)) for i in range(30)]
    independent = run_correlated_monte_carlo(many_items, systemic_uncertainty_cv=0, seed=3)
    correlated = run_correlated_monte_carlo(many_items, systemic_uncertainty_cv=0.2, seed=3)
    assert correlated["p90"] - correlated["p10"] > independent["p90"] - independent["p10"]


def test_historical_disagreement_flagged_not_blended():
    forecast = synthesize_forecast([work()], comparable_actual_hours=[100, 110, 120, 130, 140])
    assert forecast.reference_class_p50 == 120
    assert "disagree" in forecast.divergence_warning
    assert forecast.p50_hours == forecast.bottom_up_p50


def test_confidence_slider_uses_actual_percentile_after_range_adapts():
    version = make_version([work()])
    version.forecast = synthesize_forecast([work()], interval_alpha=0.1)
    curve = dict(version.forecast.percentile_curve)
    assert version.forecast.range_percentiles == [5.0, 95.0]
    assert hours_at(version, 10) == pytest.approx(curve[10])
    assert hours_at(version, 90) == pytest.approx(curve[90])


def records(actual=120, predicted=100, n=30):
    return [
        PredictionRecord(case_id=f"case-{i}", actual_hours=actual, pred_p50=predicted,
                         pred_low=predicted * 0.8, pred_high=predicted * 1.4)
        for i in range(n)
    ]


def test_calibration_gate_rejects_worse_mae():
    before = evaluate_predictions("before", records(predicted=120))
    after = evaluate_predictions("after", records(predicted=70))
    decision = calibration_gate_decision(before, after)
    assert not decision["accepted"]


def test_training_calibration_candidate_and_validation_gate():
    train = records(actual=120, predicted=100)
    multiplier = propose_multiplier(train)
    assert multiplier == 1.2
    # For demonstration, separate IDs; in real use, these must be genuinely held out.
    validation = [PredictionRecord(case_id=f"validation-{i}", actual_hours=120,
                                   pred_p50=100, pred_low=80, pred_high=140)
                  for i in range(30)]
    before = evaluate_predictions("before", validation)
    after = evaluate_predictions("after", apply_multiplier(validation, multiplier))
    assert calibration_gate_decision(before, after)["accepted"]


def test_gate_rejects_using_final_test_set():
    before = evaluate_predictions("before", records(), split="test")
    after = evaluate_predictions("after", records(), split="test")
    with pytest.raises(ValueError, match="validation split"):
        calibration_gate_decision(before, after)
