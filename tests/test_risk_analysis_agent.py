import pytest
from pydantic import ValidationError

from risk_analysis_agent import build_risk_analysis_input, validate_risk_analysis_output


def _requirement():
    return {
        "issue_key": "SCRUM-2",
        "summary": "Filter products by color",
        "description": "Customer can filter products by color.",
        "acceptance_criteria": "Selected color limits results to matching products.",
        "components": ["shopping"],
        "status": "In Progress",
        "priority": "High",
        "labels": ["review-completed"],
        "assignee": "someone",
    }


def _review(decision="READY"):
    return {
        "decision": decision,
        "known_constraints": ["color must match"],
        "dependencies": ["product catalogue"],
    }


def test_risk_input_requires_ready_review():
    with pytest.raises(ValidationError):
        build_risk_analysis_input(_requirement(), _review("NEEDS_CLARIFICATION"))


def test_risk_input_keeps_only_semantic_handoff_fields():
    payload = build_risk_analysis_input(_requirement(), _review())

    assert payload["issue_key"] == "SCRUM-2"
    assert payload["requirements_review_decision"] == "READY"
    assert payload["retrieved_evidence"] == []
    assert "status" not in payload
    assert "priority" not in payload
    assert "labels" not in payload
    assert "assignee" not in payload


def test_risk_output_calculates_score_priority_and_sorting_deterministically():
    result = validate_risk_analysis_output(
        {
            "issue_key": "SCRUM-2",
            "summary": "Color filtering risks",
            "risks": [
                {
                    "risk_id": "RISK-LOW",
                    "risk_type": "functional",
                    "category": "functional",
                    "risk_statement": "Filter may return a minor display mismatch.",
                    "likelihood": 2,
                    "impact": 2,
                    "rationale": "Filtering affects visible results.",
                    "evidence": ["AC requires selected color to limit results"],
                    "recommended_test_focus": ["exact color match"],
                },
                {
                    "risk_id": "RISK-HIGH",
                    "risk_type": "functional",
                    "category": "data",
                    "risk_statement": "Incorrect catalogue color data may return wrong products.",
                    "likelihood": 4,
                    "impact": 5,
                    "rationale": "Filtering depends on catalogue color data.",
                    "evidence": ["selected color must match returned products"],
                    "recommended_test_focus": ["catalogue color integrity"],
                },
            ],
            "recommended_next_action": "continue_to_test_analysis_and_design",
        }
    )

    assert result["risks"][0]["risk_id"] == "RISK-HIGH"
    assert result["risks"][0]["risk_score"] == 20
    assert result["risks"][0]["priority"] == "critical"
    assert result["risks"][1]["risk_score"] == 4
    assert result["risks"][1]["priority"] == "low"
    assert result["overall_risk_level"] == "critical"


def test_likelihood_and_impact_are_limited_to_one_through_five():
    with pytest.raises(ValidationError):
        validate_risk_analysis_output(
            {
                "issue_key": "SCRUM-2",
                "summary": "Invalid scale",
                "risks": [
                    {
                        "risk_id": "RISK-1",
                        "risk_type": "functional",
                        "category": "functional",
                        "risk_statement": "Example",
                        "likelihood": 6,
                        "impact": 2,
                        "rationale": "Example",
                    }
                ],
                "recommended_next_action": "continue_to_test_analysis_and_design",
            }
        )
