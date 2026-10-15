"""Verify quoted text against supplied source documents.

Use only extracted text and cite its provenance; this cannot establish that
an interpretation is semantically correct. It catches absent/fabricated spans.
"""
import re
import unicodedata

from .schemas import EstimateVersion, EvidenceSpan


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def validate_evidence_against_sources(version: EstimateVersion, source_texts: dict[str, str]) -> None:
    def verify(evidence: EvidenceSpan) -> None:
        original = source_texts.get(evidence.source_doc)
        if original is None:
            raise ValueError(f"Unknown source document: {evidence.source_doc}")
        if _normalize(evidence.quote) not in _normalize(original):
            raise ValueError(f"Quoted evidence not found in {evidence.source_doc}")

    for req in version.requirements:
        for ev in req.evidence:
            verify(ev)
    for finding in version.critic_findings:
        for ev in finding.supporting_evidence:
            verify(ev)
