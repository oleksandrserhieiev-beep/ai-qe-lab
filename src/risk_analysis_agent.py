import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "risk_analysis_prompt.txt"

RiskCategory = Literal["functional", "integration", "data", "ai", "security", "resilience", "performance", "business"]
RiskLevel = Literal["critical", "high", "medium", "low"]
Likelihood = Literal["high", "medium", "low"]
Impact = Literal["high", "medium", "low"]


class RiskItem(BaseModel):
    risk_id: str = Field(min_length=1)
    category: RiskCategory
    risk_statement: str = Field(min_length=1)
    likelihood: Likelihood
    impact: Impact
    priority: RiskLevel
    rationale: str = Field(min_length=1)
    evidence: list[str] = []
    recommended_test_focus: list[str] = []


class RiskAnalysisResult(BaseModel):
    issue_key: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    risks: list[RiskItem]
    overall_risk_level: RiskLevel
    recommended_next_action: Literal["continue_to_test_analysis_and_design"]


class RiskAnalysisInput(BaseModel):
    issue_key: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    description: str = ""
    acceptance_criteria: str = ""
    components: list[str] = []
    requirements_review_decision: Literal["READY"]
    known_constraints: list[str] = []
    dependencies: list[str] = []
    retrieved_evidence: list[dict] = []

    @model_validator(mode="after")
    def require_ready_gate(self):
        if self.requirements_review_decision != "READY":
            raise ValueError("Risk Analysis can run only after Requirements Review = READY")
        return self


def build_risk_analysis_input(requirement: dict, requirements_review: dict, retrieved_evidence: list[dict] | None = None) -> dict:
    """Build the intentionally small hand-off contract for Risk Analysis.

    Operational Jira metadata is deliberately excluded. Cross-document evidence is
    represented as a bounded list and will be populated by a later retrieval slice.
    """
    payload = RiskAnalysisInput(
        issue_key=requirement.get("issue_key") or "",
        summary=requirement.get("summary") or "",
        description=requirement.get("description") or "",
        acceptance_criteria=requirement.get("acceptance_criteria") or "",
        components=requirement.get("components") or [],
        requirements_review_decision=requirements_review.get("decision"),
        known_constraints=requirements_review.get("known_constraints") or [],
        dependencies=requirements_review.get("dependencies") or [],
        retrieved_evidence=retrieved_evidence or [],
    )
    return payload.model_dump()


def validate_risk_analysis_output(payload: dict) -> dict:
    return RiskAnalysisResult.model_validate(payload).model_dump()


def compact_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
