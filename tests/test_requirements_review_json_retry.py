import pytest

from requirements_review_agent import _extract_json


def test_extract_json_rejects_truncated_json():
    with pytest.raises(ValueError, match="malformed or truncated JSON"):
        _extract_json('{"decision":"READY","summary":"unterminated}')


def test_extract_json_accepts_valid_json():
    payload = _extract_json('{"decision":"READY","readiness_score":100}')
    assert payload["decision"] == "READY"
    assert payload["readiness_score"] == 100
