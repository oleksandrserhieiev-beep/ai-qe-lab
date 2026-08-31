import os
import random
import time

import httpx
from anthropic import Anthropic

from context_builder import SYSTEM_INSTRUCTION

OPENAI_MAX_ATTEMPTS = 4
OPENAI_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
OPENAI_NON_RETRYABLE_ERROR_CODES = {
    "billing_hard_limit_reached",
    "credit_balance_exhausted",
    "insufficient_quota",
    "project_spend_limit_exceeded",
}


class ModelInvocationError(RuntimeError):
    def __init__(self, provider, model, message, *, status_code=None, error_code=None, retryable=False):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.error_code = error_code
        self.retryable = retryable

    def to_dict(self):
        return {
            "type": "MODEL_INVOCATION_ERROR",
            "provider": self.provider,
            "model": self.model,
            "status_code": self.status_code,
            "error_code": self.error_code,
            "retryable": self.retryable,
            "message": str(self),
        }


def provider_for_model(model):
    value = model.lower()
    if value.startswith("claude-"):
        return "anthropic"
    if value.startswith("gpt-"):
        return "openai"
    raise ValueError(f"Unsupported model family: {model}")


def _openai_error_details(response):
    try:
        payload = response.json()
    except ValueError:
        return None, response.text[:1000]

    error = payload.get("error") or {}
    error_code = error.get("code") or error.get("type")
    message = error.get("message") or response.text[:1000]
    return error_code, message


def _retry_delay_seconds(response, attempt):
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass
    return min((2 ** (attempt - 1)) + random.uniform(0.0, 0.5), 30.0)


def _post_openai_with_retry(client, key, payload, model):
    for attempt in range(1, OPENAI_MAX_ATTEMPTS + 1):
        try:
            response = client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
            )
        except httpx.RequestError as exc:
            if attempt == OPENAI_MAX_ATTEMPTS:
                raise ModelInvocationError(
                    "openai",
                    model,
                    f"OpenAI request failed after {attempt} attempts: {exc}",
                    retryable=True,
                ) from exc
            delay = min((2 ** (attempt - 1)) + random.uniform(0.0, 0.5), 30.0)
            print(f"OpenAI request error; retrying in {delay:.1f}s ({attempt}/{OPENAI_MAX_ATTEMPTS})")
            time.sleep(delay)
            continue

        if response.is_success:
            return response

        error_code, error_message = _openai_error_details(response)
        retryable = (
            response.status_code in OPENAI_RETRYABLE_STATUS_CODES
            and error_code not in OPENAI_NON_RETRYABLE_ERROR_CODES
        )

        if retryable and attempt < OPENAI_MAX_ATTEMPTS:
            delay = _retry_delay_seconds(response, attempt)
            print(
                f"OpenAI API returned {response.status_code}"
                f" ({error_code or 'unknown_error'}); retrying in {delay:.1f}s"
                f" ({attempt}/{OPENAI_MAX_ATTEMPTS})"
            )
            time.sleep(delay)
            continue

        raise ModelInvocationError(
            "openai",
            model,
            f"OpenAI API returned {response.status_code}: {error_message}",
            status_code=response.status_code,
            error_code=error_code,
            retryable=retryable,
        )

    raise AssertionError("OpenAI retry loop exited unexpectedly")


def generate_with_model(model, final_context):
    provider = provider_for_model(model)
    start = time.perf_counter()
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY (or LLM_API_KEY) is missing")
        response = Anthropic(api_key=key).messages.create(
            model=model,
            max_tokens=700,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": final_context}],
        )
        answer = "".join(block.text for block in response.content if block.type == "text")
        usage = response.usage
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    else:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is missing")
        payload = {
            "model": model,
            "instructions": SYSTEM_INSTRUCTION,
            "input": final_context,
            "max_output_tokens": 700,
        }
        with httpx.Client(timeout=120.0) as client:
            response = _post_openai_with_retry(client, key, payload, model)
            data = response.json()
        answer_parts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    answer_parts.append(content.get("text", ""))
        answer = "".join(answer_parts)
        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)

    return answer, {
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
    }
