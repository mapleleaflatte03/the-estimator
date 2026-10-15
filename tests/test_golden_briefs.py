"""Verification test suite for the 3 Golden Brief benchmarks."""
import json
from pathlib import Path
import pytest

from parallax.extractor import extract_scope_and_wbs
from parallax.provenance import validate_evidence_against_sources
from parallax.schemas import VerificationStatus

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
    """Verify that clarifying ERP integration impacts the forecast by sensitivity spread."""
    data = load_golden_brief("golden_brief_1_pm_portal.json")
    brief_text = data["brief_text"]

    # Version with ERP = True
    v_with_erp = extract_scope_and_wbs(
        project_id="GOLDEN-01",
        brief_text=brief_text,
        clarification_answers={"CLAR-ERP": True},
        version_id="v_true",
    )

    # Version with ERP = False
    v_no_erp = extract_scope_and_wbs(
        project_id="GOLDEN-01",
        brief_text=brief_text,
        clarification_answers={"CLAR-ERP": False},
        version_id="v_false",
    )

    diff = v_with_erp.forecast.p50_hours - v_no_erp.forecast.p50_hours
    # ERP connector is 55 likely hours + 25 likely hours QA/retry = ~80-100 hours difference
    assert diff >= 60.0, f"Expected sensitivity spread >= 60 hours, got {diff:.1f}"
