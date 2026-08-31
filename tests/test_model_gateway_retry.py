import sys
from pathlib import Path

import httpx
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import model_gateway  # noqa: E402
from model_gateway import ModelInvocationError, _post_openai_with_retry  # noqa: E402


class StubClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def post(self, *args, **kwargs):
        response = self.responses[self.calls]
        self.calls += 1
        return response


def _response(status_code, payload, headers=None):
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    return httpx.Response(status_code, json=payload, headers=headers, request=request)


def test_openai_429_rate_limit_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(model_gateway.time, "sleep", lambda _: None)
    client = StubClient([
        _response(
            429,
            {"error": {"type": "rate_limit_exceeded", "code": "rate_limit_exceeded", "message": "Slow down"}},
            headers={"retry-after": "0"},
        ),
        _response(200, {"output": [], "usage": {}}),
    ])

    response = _post_openai_with_retry(client, "test-key", {"model": "gpt-test"}, "gpt-test")

    assert response.status_code == 200
    assert client.calls == 2


def test_openai_quota_429_is_not_retried(monkeypatch):
    monkeypatch.setattr(model_gateway.time, "sleep", lambda _: None)
    client = StubClient([
        _response(
            429,
            {"error": {"type": "insufficient_quota", "code": "insufficient_quota", "message": "Quota exhausted"}},
        )
    ])

    with pytest.raises(ModelInvocationError) as exc_info:
        _post_openai_with_retry(client, "test-key", {"model": "gpt-test"}, "gpt-test")

    error = exc_info.value
    assert client.calls == 1
    assert error.status_code == 429
    assert error.error_code == "insufficient_quota"
    assert error.retryable is False
    assert error.to_dict()["type"] == "MODEL_INVOCATION_ERROR"
