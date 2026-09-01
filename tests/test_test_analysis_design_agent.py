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
