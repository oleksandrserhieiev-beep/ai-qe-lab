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
        "labels": ["ai-review"],
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


def test_risk_output_contract():
    result = validate_risk_analysis_output(
        {
            "issue_key": "SCRUM-2",
            "summary": "Color filtering risks",
            "risks": [
                {
                    "risk_id": "RISK-1",
                    "category": "functional",
                    "risk_statement": "Filter may return products with a non-selected color.",
                    "likelihood": "medium",
                    "impact": "high",
                    "priority": "high",
                    "rationale": "Filtering directly affects product relevance.",
                    "evidence": ["AC requires selected color to limit results"],
                    "recommended_test_focus": ["exact color match", "no cross-color leakage"],
                }
            ],
            "overall_risk_level": "high",
            "recommended_next_action": "continue_to_test_analysis_and_design",
        }
    )

    assert result["risks"][0]["category"] == "functional"
