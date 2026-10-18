"""Verification test suite for the 3 Golden Brief benchmarks."""
import json
from pathlib import Path
import pytest

from parallax.extractor import extract_scope_and_wbs
from parallax.export import proposal_markdown
from parallax.provenance import validate_evidence_against_sources
from parallax.schemas import Project, VerificationStatus

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "datasets" / "golden_briefs"


def load_golden_brief(filename: str) -> dict:
    with open(GOLDEN_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "golden_brief_1_pm_portal.json",
        "golden_brief_2_ecommerce_sync.json",
        "golden_brief_3_ai_rag_support.json",
        "golden_brief_4_field_service.json",
        "golden_brief_5_dental_chain.json",
        "golden_brief_6_returns_portal.json",
        "golden_brief_7_fund_onboarding.json",
        "golden_brief_8_language_center.json",
        "golden_brief_9_site_inspection.json",
    ],
)
def test_golden_brief_extraction_and_provenance(fixture_name):
    data = load_golden_brief(fixture_name)
    brief_text = data["brief_text"]

    version = extract_scope_and_wbs(
        project_id=data["brief_id"],
        brief_text=brief_text,
        version_id="v1",
    )

    # 1. Provenance Attribution Check: Zero unsupported claims
    validate_evidence_against_sources(version, {"brief.txt": brief_text})

    # 2. Scope Completeness & DAG validity
    assert len(version.requirements) >= 4
    assert len(version.wbs) >= data.get("min_wbs_items", 5)

    # 3. Requirement Recall on ground truth quotes
    extracted_quotes = []
    for r in version.requirements:
        for ev in r.evidence:
            extracted_quotes.append(ev.quote)

    for expected_sub in data.get("expected_confirmed_quotes", []):
        matched = any(expected_sub.lower() in q.lower() for q in extracted_quotes)
        assert matched, f"Expected quote '{expected_sub}' was not found in extracted evidence"

    # 4. Forecast sanity check
    fc = version.forecast
    assert fc.p10_hours <= fc.p50_hours <= fc.p80_hours <= fc.p90_hours
    assert fc.p50_hours > 50.0


def test_golden_brief_1_active_clarification_sensitivity():
    """The tentative ERP clause becomes a scope question whose answer moves the forecast."""
    data = load_golden_brief("golden_brief_1_pm_portal.json")
    brief_text = data["brief_text"]
    v1 = extract_scope_and_wbs(project_id="GOLDEN-01", brief_text=brief_text, version_id="v1")
    erp_q = next(q for q in v1.clarifications if any("ERP" in ev.quote for ev in q.evidence))
    assert erp_q.current_assumption is False
    assert erp_q.affected_item_ids
    assert not any(i.item_id in erp_q.affected_item_ids for i in v1.wbs)

    v_with_erp = extract_scope_and_wbs(
        project_id="GOLDEN-01", brief_text=brief_text,
        clarification_answers={erp_q.question_id: True}, version_id="v_true",
    )
    v_no_erp = extract_scope_and_wbs(
        project_id="GOLDEN-01", brief_text=brief_text,
        clarification_answers={erp_q.question_id: False}, version_id="v_false",
    )
    assert not any(i.item_id in erp_q.affected_item_ids for i in v_no_erp.wbs)
    assert v1.forecast.p50_hours == v_no_erp.forecast.p50_hours
    proposal = proposal_markdown(Project(project_id="GOLDEN-01", title="Portal", brief_text=brief_text), v1, lang="en")
    assert "Pending scope (excluded until confirmed)" in proposal
    assert "Out of scope (confirmed not in this delivery)" not in proposal
    diff = v_with_erp.forecast.p50_hours - v_no_erp.forecast.p50_hours
    # The removed items' PERT mean is the sensitivity; Monte Carlo + QA share keep it close.
    assert diff >= 0.7 * erp_q.sensitivity_spread_hours, f"diff={diff:.1f}, spread={erp_q.sensitivity_spread_hours}"
