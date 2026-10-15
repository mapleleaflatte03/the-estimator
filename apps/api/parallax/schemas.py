"""Core immutable-ish data contracts for evidence-backed work estimates.

Note: Pydantic validates shape, not truth. To validate actual citations, call
validate_evidence_against_sources() from provenance.py with original text.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class VerificationStatus(str, Enum):
    CONFIRMED = "confirmed"
    ASSUMED = "assumed"
    MISSING = "missing"


class EvidenceSpan(BaseModel):
    source_doc: str = Field(min_length=1)
    quote: str = Field(min_length=5)
    location: Optional[str] = None


class RequirementNode(BaseModel):
    req_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str
    status: VerificationStatus
    evidence: list[EvidenceSpan] = Field(default_factory=list)

    @model_validator(mode="after")
    def confirmed_needs_evidence(self):
        if self.status == VerificationStatus.CONFIRMED and not self.evidence:
            raise ValueError(f"{self.req_id}: confirmed requirements require evidence")
        return self


class WorkItem(BaseModel):
    item_id: str = Field(min_length=1)
    req_ids: list[str] = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    optimistic_hours: float = Field(gt=0, allow_inf_nan=False)
    most_likely_hours: float = Field(gt=0, allow_inf_nan=False)
    pessimistic_hours: float = Field(gt=0, allow_inf_nan=False)
    assumption_id: Optional[str] = None

    @model_validator(mode="after")
    def check_three_point_order(self):
        if not (self.optimistic_hours <= self.most_likely_hours <= self.pessimistic_hours):
            raise ValueError(f"{self.item_id}: must satisfy optimistic <= likely <= pessimistic")
        return self


class CriticFinding(BaseModel):
    finding_id: str = Field(min_length=1)
    category: str
    claim: str = Field(min_length=1)
    verified_by_evidence: bool
    supporting_evidence: list[EvidenceSpan] = Field(default_factory=list)
    action_taken: str

    @model_validator(mode="after")
    def no_unverified_auto_apply(self):
        if self.verified_by_evidence and not self.supporting_evidence:
            raise ValueError("Verified critic finding must cite evidence")
        if not self.verified_by_evidence and self.action_taken == "applied_to_wbs":
            raise ValueError("Unverified critic finding cannot be applied automatically")
        return self


class ClarificationQuestion(BaseModel):
    question_id: str
    assumption_id: str
    question_text: str
    context_reason: str
    hours_if_false: float = Field(ge=0, allow_inf_nan=False)
    hours_if_true: float = Field(ge=0, allow_inf_nan=False)
    prior_probability: Optional[float] = Field(default=None, ge=0, le=1)

    @property
    def sensitivity_spread_hours(self) -> float:
        """Sensitivity proxy, NOT an expected value-of-information estimate."""
        return abs(self.hours_if_true - self.hours_if_false)


class ProbabilisticForecast(BaseModel):
    p10_hours: float = Field(ge=0, allow_inf_nan=False)
    p50_hours: float = Field(ge=0, allow_inf_nan=False)
    p80_hours: float = Field(ge=0, allow_inf_nan=False)
    p90_hours: float = Field(ge=0, allow_inf_nan=False)
    mean_hours: float = Field(ge=0, allow_inf_nan=False)
    std_hours: float = Field(ge=0, allow_inf_nan=False)
    bottom_up_p50: float = Field(ge=0, allow_inf_nan=False)
    reference_class_p50: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    divergence_warning: Optional[str] = None
    insufficient_historical_evidence: bool = False

    @model_validator(mode="after")
    def sorted_quantiles(self):
        if not self.p10_hours <= self.p50_hours <= self.p80_hours <= self.p90_hours:
            raise ValueError("Quantiles must satisfy P10 <= P50 <= P80 <= P90")
        return self


class EstimateVersion(BaseModel):
    version_id: str
    project_id: str
    parent_version_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_tag: str
    requirements: list[RequirementNode]
    wbs: list[WorkItem]
    critic_findings: list[CriticFinding] = Field(default_factory=list)
    clarifications: list[ClarificationQuestion] = Field(default_factory=list)
    forecast: ProbabilisticForecast

    @model_validator(mode="after")
    def verify_links_and_acyclic_graph(self):
        req_ids = [r.req_id for r in self.requirements]
        item_ids = [w.item_id for w in self.wbs]
        if len(req_ids) != len(set(req_ids)) or len(item_ids) != len(set(item_ids)):
            raise ValueError("Requirement and work item identifiers must be unique")
        known_req = set(req_ids)
        known_items = set(item_ids)
        graph = {}
        for item in self.wbs:
            if not set(item.req_ids).issubset(known_req):
                raise ValueError(f"{item.item_id}: work item refers to missing requirement")
            if not set(item.dependencies).issubset(known_items):
                raise ValueError(f"{item.item_id}: dependency refers to missing work item")
            graph[item.item_id] = item.dependencies

        visiting, visited = set(), set()

        def visit(node):
            if node in visiting:
                raise ValueError(f"Cycle detected in scope graph near {node}")
            if node in visited:
                return
            visiting.add(node)
            for other in graph[node]:
                visit(other)
            visiting.remove(node)
            visited.add(node)

        for item_id in graph:
            visit(item_id)
        return self


class Project(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    project_type: str = "custom_software"
    brief_text: str = Field(min_length=1)
    documents: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "intake"
    current_version_id: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1)
    project_type: str = "custom_software"
    brief_text: str = Field(min_length=1)
    documents: Optional[dict[str, str]] = None


class HistoricalCase(BaseModel):
    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    domain: str = "software"
    actual_hours: float = Field(gt=0)
    task_count: int = Field(gt=0)
    complexity_score: float = Field(ge=0.0, le=10.0, default=5.0)
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ActualWork(BaseModel):
    actual_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    actual_hours: float = Field(gt=0)
    item_actuals: dict[str, float] = Field(default_factory=dict)
    deviation_reasons: list[str] = Field(default_factory=list)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationRun(BaseModel):
    run_id: str = Field(min_length=1)
    dataset_name: str = Field(min_length=1)
    split: str = "validation"
    model_tag: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[str, float] = Field(default_factory=dict)
    gate_decision: Optional[dict] = None


class ClarificationAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answer: bool
    notes: Optional[str] = None
