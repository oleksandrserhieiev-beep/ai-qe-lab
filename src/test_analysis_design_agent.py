import json
import os
import time
from pathlib import Path

from anthropic import Anthropic

from cost_reporting import estimate_cost
from test_analysis_design import TestAnalysisDesignResult

PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "test_analysis_design_prompt.txt"
PRIMARY_MAX_TOKENS = 6000
RETRY_MAX_TOKENS = 9000


def _configuration() -> tuple[str, str]:
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("TEST_ANALYSIS_DESIGN_MODEL") or os.getenv("RISK_ANALYSIS_MODEL") or os.getenv("SUT_MODEL")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing")
    if not model:
        raise ValueError("TEST_ANALYSIS_DESIGN_MODEL, RISK_ANALYSIS_MODEL or SUT_MODEL is missing")
    return api_key, model


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Test Analysis & Design Agent returned an empty response")
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError("Test Analysis & Design Agent returned truncated or malformed JSON") from exc


def _response_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def analyze_test_design(payload: dict) -> tuple[dict, dict]:
    api_key, model = _configuration()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=api_key)
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    base_message = "Analyze this requirement, reviewed risks, and governed dataset snapshot. Return one complete compact JSON object matching the TestAnalysisDesignResult contract only. Do not echo the dataset snapshot. Keep rationale and coverage notes concise.\n" + compact
    messages = [{"role": "user", "content": base_message}]
    responses = []
    started = time.perf_counter()
    result = None
    last_error = None
    for attempt, max_tokens in enumerate((PRIMARY_MAX_TOKENS, RETRY_MAX_TOKENS), start=1):
        response = client.messages.create(model=model, max_tokens=max_tokens, system=prompt, messages=messages)
        responses.append(response)
        text = _response_text(response)
        try:
            if response.stop_reason == "max_tokens":
                raise ValueError(f"response was truncated at max_tokens={max_tokens}")
            result = TestAnalysisDesignResult.model_validate(_extract_json(text)).model_dump()
            if result["issue_key"] != payload["issue_key"]:
                raise ValueError("output issue_key does not match input")
            break
        except Exception as exc:
            last_error = exc
            if attempt == 2:
                raise ValueError(f"Test Analysis & Design contract failure after retry: {exc}") from exc
            # Retry from the original input instead of feeding a truncated assistant JSON back.
            messages = [{
                "role": "user",
                "content": base_message + "\nPrevious attempt failed because its output was truncated or invalid. Return a smaller complete JSON object. Generate only material proposals; use concise strings and never reproduce full existing dataset records.",
            }]
    if result is None:
        raise ValueError(f"Test Analysis & Design did not produce a result: {last_error}")
    input_tokens = sum(int(getattr(r.usage, "input_tokens", 0) or 0) for r in responses)
    output_tokens = sum(int(getattr(r.usage, "output_tokens", 0) or 0) for r in responses)
    telemetry = {
        "agent": "test_analysis_design",
        "model": responses[-1].model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "attempts": len(responses),
        "contract_retry_used": len(responses) > 1,
        "stop_reason": responses[-1].stop_reason,
        "estimated_cost_usd": estimate_cost(responses[-1].model, input_tokens, output_tokens),
    }
    return result, telemetry
