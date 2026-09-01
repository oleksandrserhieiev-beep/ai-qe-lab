import pytest
from pydantic import ValidationError

from evaluate_risk_analysis_agent import evaluate_case
from risk_analysis_agent import RiskAnalysisInput, _extract_json, validate_risk_analysis_output


def test_execution_input_rejects_non_ready():
    with pytest.raises(ValidationError):
        RiskAnalysisInput.model_validate({
            "issue_key": "X-1", "summary": "x", "requirements_review_decision": "NEEDS_CLARIFICATION"
        })


def test_output_requires_at_least_one_risk():
    with pytest.raises(ValidationError):
        validate_risk_analysis_output({
            "issue_key": "X-1", "summary": "x", "risks": [], "overall_risk_level": "low",
            "recommended_next_action": "continue_to_test_analysis_and_design"
        })


def test_json_parser_accepts_fenced_json():
    assert _extract_json('```json\n{"issue_key":"X-1"}\n```')["issue_key"] == "X-1"


def test_deterministic_agent_evaluation_contract():
    case = {
        "case_id": "T-1", "expected_categories": ["functional", "data"],
        "required_focus_terms": ["color"], "forbidden_claim_terms": ["payment"],
        "min_risks": 1, "max_risks": 4,
    }
    result = {
        "risks": [{
            "category": "functional", "risk_statement": "Wrong color may be returned",
            "recommended_test_focus": ["exact color match"]
        }]
    }
    evaluation = evaluate_case(case, result)
    assert evaluation["passed"] is True
    assert evaluation["expected_category_recall"] == 0.5
