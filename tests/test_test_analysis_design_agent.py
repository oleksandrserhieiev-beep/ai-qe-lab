import json

import pytest

import test_analysis_design_agent as agent


def test_extract_json_rejects_truncated_payload_with_clear_error():
    with pytest.raises(ValueError, match="truncated or malformed JSON"):
        agent._extract_json('{"issue_key":"SCRUM-6","proposals":[{"title":"unterminated')


def test_extract_json_accepts_fenced_complete_payload():
    payload = {"issue_key": "SCRUM-6", "health_findings": [], "coverage_gaps": [], "proposals": [], "human_decision_required": True}
    text = "```json\n" + json.dumps(payload) + "\n```"
    assert agent._extract_json(text) == payload


def test_normalise_contract_repairs_common_model_aliases():
    raw = {
        "proposals": [{
            "proposal_id": "TP-1",
            "name": "Missing price",
            "test_type": "AI-specific",
            "traceability": {"jira_issue": "SCRUM-7", "ac": ["Do not invent price"], "risks": ["R-AI-PRICE-01"]},
            "oracle": "semantic_llm",
            "target_suite": "PR Critical",
            "rationale": "Critical unsupported claim",
            "action": "add",
            "query": "Find a product whose price is missing",
            "expected_behavior": "Do not invent a price",
            "similar_cases": [{"existing_case_id": "G-001", "similarity": 0.6, "note": "Related price coverage"}],
        }]
    }
    result = agent._normalise_contract(raw, "SCRUM-7")
    proposal = result["proposals"][0]
    assert proposal["proposed_id"] == "TP-1"
    assert proposal["traceability"]["issue_key"] == "SCRUM-7"
    assert proposal["target_suite"] == "pr_critical"
    assert proposal["oracle_type"] == "semantic"
    assert proposal["action"] == "ADD"
    assert proposal["similar_cases"][0]["case_id"] == "G-001"
