"""A committed sentence that shares work with an earlier sentence stays in the quote."""
from datetime import datetime, timezone

from parallax.export import proposal_markdown, wbs_csv
from parallax.extractor import extract_scope_and_wbs
from parallax.schemas import Project

BRIEF = "\n".join([
    "- The box must stay between 2 and 8 degrees. If the logger goes outside that range, the receiving bench is alerted before they accept the box.",
    "- Email the clinic when a box is rejected.",
    "- Keep a record of who changed the recorded temperature.",
    "- We might add a driver mobile app later, if the paper run-sheets keep getting lost.",
])


def test_shared_sentence_is_quoted_once_and_audit_has_its_own_hours():
    version = extract_scope_and_wbs("PRJ-SHARED", BRIEF, version_id="v1")
    notices = [w for w in version.wbs if w.name.startswith("Notification service")]
    assert len(notices) == 1
    email = next(r for r in version.requirements if r.evidence and r.evidence[0].quote.startswith("Email the clinic"))
    assert email.req_id in notices[0].req_ids
    assert email.req_id != notices[0].req_ids[0]

    audit = [w for w in version.wbs if w.component == "audit"]
    assert len(audit) == 1
    assert audit[0].most_likely_hours > 0
    changed = next(r for r in version.requirements if r.evidence and "who changed" in r.evidence[0].quote)
    assert changed.req_id == audit[0].req_ids[0]

    project = Project(
        project_id="PRJ-SHARED", title="Blood bank sample handover", brief_text=BRIEF,
        created_at=datetime.now(timezone.utc),
    )
    text = proposal_markdown(project, version, lang="en")
    assert "Email the clinic when a box is rejected." in text
    assert "who changed the recorded temperature" in text
    assert "already counted above" in text
    owned = [ln for ln in text.splitlines() if ln.startswith("- Notification service") and "(Server)" in ln]
    shared = [ln for ln in text.splitlines() if ln.startswith("- Notification service") and "under" in ln]
    assert len(owned) == 1 and len(shared) == 1
    assert "### Email the clinic when a box is rejected. —" not in text

    sheet = wbs_csv(version, lang="en")
    assert "Email the clinic when a box is rejected." in sheet
    assert "who changed the recorded temperature" in sheet
    assert sheet.count("Notification service") == 1

    mobile = next(q for q in version.clarifications if "driver mobile app" in q.question_text)
    assert "paper run-sheets" in mobile.question_text
    assert "…" not in mobile.question_text
    assert "1 work item." in mobile.context_reason
    assert "item(s)" not in mobile.context_reason
