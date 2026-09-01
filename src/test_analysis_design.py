from typing import Literal

from pydantic import BaseModel, Field, model_validator


OracleType = Literal["deterministic", "semantic"]
ProposalAction = Literal["ADD", "EXTEND_EXISTING", "SKIP"]
TargetSuite = Literal["pr_critical", "regression", "nightly", "golden_candidate"]
HealthSeverity = Literal["ERROR", "WARNING"]


class DatasetHealthFinding(BaseModel):
    severity: HealthSeverity
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    record_id: str | None = None


class Traceability(BaseModel):
    issue_key: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)
    risk_ids: list[str] = Field(min_length=1)


class SimilarCase(BaseModel):
    case_id: str = Field(min_length=1)
    similarity_score: float = Field(ge=0.0, le=1.0)
    coverage_note: str = Field(min_length=1)


class TestProposal(BaseModel):
    proposed_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    test_kind: Literal["functional", "ai"]
    traceability: Traceability
    oracle_type: OracleType
    target_suite: TargetSuite
    target_rationale: str = Field(min_length=1)
    action: ProposalAction
    input: dict
    expected: dict
    similar_cases: list[SimilarCase] = []
    existing_case_id: str | None = None
    proposed_extension: dict | None = None

    @model_validator(mode="after")
    def validate_action_contract(self):
        if self.action == "EXTEND_EXISTING":
            if not self.existing_case_id or not self.proposed_extension:
                raise ValueError("EXTEND_EXISTING requires existing_case_id and proposed_extension")
        return self


class TestAnalysisDesignResult(BaseModel):
    issue_key: str = Field(min_length=1)
    health_findings: list[DatasetHealthFinding] = []
    coverage_gaps: list[str] = []
    proposals: list[TestProposal] = []
    human_decision_required: bool = True

    @property
    def blocked(self) -> bool:
        return any(item.severity == "ERROR" for item in self.health_findings)


def dataset_health_check(records: list[dict], required_fields: set[str]) -> list[DatasetHealthFinding]:
    findings: list[DatasetHealthFinding] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        record_id = str(record.get("id") or "").strip() or None
        missing = sorted(
            field
            for field in required_fields
            if field not in record or record[field] is None or (isinstance(record[field], str) and not record[field].strip())
        )
        if missing:
            findings.append(DatasetHealthFinding(severity="ERROR", code="MISSING_REQUIRED_FIELDS", message=f"Missing required fields: {', '.join(missing)}", dataset="evaluation", record_id=record_id or f"row-{index + 1}"))
        if record_id:
            if record_id in seen_ids:
                findings.append(DatasetHealthFinding(severity="ERROR", code="DUPLICATE_ID", message=f"Duplicate record id: {record_id}", dataset="evaluation", record_id=record_id))
            seen_ids.add(record_id)
        if record.get("active") is False:
            findings.append(DatasetHealthFinding(severity="WARNING", code="INACTIVE_RECORD", message="Related record is inactive; review before extending or relying on its coverage", dataset="evaluation", record_id=record_id))
    return findings


def can_propose(findings: list[DatasetHealthFinding]) -> bool:
    return not any(item.severity == "ERROR" for item in findings)
