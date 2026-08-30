import pytest
from pydantic import ValidationError

from requirements_review_agent import RequirementsReviewResult


def _review(decision, gaps, action):
    return {
        "decision": decision,
        "readiness_score": 80,
        "summary": "review",
        "gaps": gaps,
        "known_constraints": [],
        "dependencies": [],
        "testability_notes": [],
        "recommended_next_action": action,
    }


def _gap(gap_type):
    return {
        "gap_type": gap_type,
        "criterion": "complete",
        "category": "acceptance_criteria",
        "severity": "high",
        "finding": "Expected behavior is incomplete.",
        "clarification_question": "What is the expected outcome?",
    }


def test_ready_allows_non_blocking_and_technical_findings():
    result = RequirementsReviewResult.model_validate(
        _review(
            "READY",
            [_gap("NON_BLOCKING_GAP"), _gap("TECHNICAL_CONTEXT_NEEDED")],
            "continue_to_risk_analysis",
        )
    )
    assert result.decision == "READY"


def test_ready_rejects_blocking_gap():
    with pytest.raises(ValidationError, match="READY review cannot contain BLOCKING_GAP"):
        RequirementsReviewResult.model_validate(
            _review("READY", [_gap("BLOCKING_GAP")], "continue_to_risk_analysis")
        )


def test_needs_clarification_requires_blocking_gap():
    with pytest.raises(ValidationError, match="requires at least one BLOCKING_GAP"):
        RequirementsReviewResult.model_validate(
            _review("NEEDS_CLARIFICATION", [_gap("NON_BLOCKING_GAP")], "clarify_requirement")
        )


def test_action_must_match_decision():
    with pytest.raises(ValidationError, match="recommended_next_action"):
        RequirementsReviewResult.model_validate(_review("READY", [], "clarify_requirement"))
