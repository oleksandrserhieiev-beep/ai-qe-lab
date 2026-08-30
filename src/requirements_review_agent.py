import json
import os
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from cost_reporting import estimate_cost


load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "requirements_review_prompt.txt"
PRIMARY_MAX_TOKENS = 3000
RETRY_MAX_TOKENS = 4000


class RequirementGap(BaseModel):
    category: str
    severity: str
    finding: str
    clarification_question: str = ""


class RequirementsReviewResult(BaseModel):
    decision: str
    readiness_score: int = Field(ge=0, le=100)
    summary: str
    gaps: list[RequirementGap]
    known_constraints: list[str]
    dependencies: list[str]
    testability_notes: list[str]
    recommended_next_action: str


def _configuration():
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("REQUIREMENTS_REVIEW_MODEL") or os.getenv("SUT_MODEL")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing in .env")
    if not model:
        raise ValueError("REQUIREMENTS_REVIEW_MODEL or SUT_MODEL is missing")
    return api_key, model


def _usage_value(usage, name):
    return int(getattr(usage, name, 0) or 0)


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as original_error:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Requirements Review Agent did not return valid JSON") from original_error
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as sliced_error:
            raise ValueError("Requirements Review Agent returned malformed or truncated JSON") from sliced_error


def _text_from_response(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def _call_agent(client, model: str, system_prompt: str, messages: list[dict], max_tokens: int):
    return client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )


def review_requirement(requirement: dict) -> tuple[dict, dict]:
    api_key, model = _configuration()
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=api_key)

    user_payload = json.dumps(requirement, ensure_ascii=False, indent=2)
    primary_messages = [
        {
            "role": "user",
            "content": (
                "Review this normalized Jira requirement. Treat absent information as absent; "
                "do not infer hidden acceptance criteria. Return one complete valid JSON object only.\n\n"
                f"{user_payload}"
            ),
        }
    ]

    start_time = time.perf_counter()
    responses = []
    response = _call_agent(client, model, system_prompt, primary_messages, PRIMARY_MAX_TOKENS)
    responses.append(response)
    text = _text_from_response(response)

    retry_used = False
    try:
        parsed = _extract_json(text)
    except ValueError:
        retry_used = True
        repair_messages = [
            *primary_messages,
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    "Your previous response was not a complete valid JSON object. "
                    "Return the full review again from the beginning as one complete valid JSON object only. "
                    "Do not add markdown or explanatory text."
                ),
            },
        ]
        response = _call_agent(client, model, system_prompt, repair_messages, RETRY_MAX_TOKENS)
        responses.append(response)
        text = _text_from_response(response)
        parsed = _extract_json(text)

    latency_ms = (time.perf_counter() - start_time) * 1000
    validated = RequirementsReviewResult.model_validate(parsed).model_dump()

    input_tokens = sum(_usage_value(item.usage, "input_tokens") for item in responses)
    output_tokens = sum(_usage_value(item.usage, "output_tokens") for item in responses)
    cache_creation_tokens = sum(_usage_value(item.usage, "cache_creation_input_tokens") for item in responses)
    cache_read_tokens = sum(_usage_value(item.usage, "cache_read_input_tokens") for item in responses)

    telemetry = {
        "agent": "requirements_review",
        "model": response.model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cache_creation_input_tokens": cache_creation_tokens,
        "cache_read_input_tokens": cache_read_tokens,
        "latency_ms": round(latency_ms, 2),
        "stop_reason": response.stop_reason,
        "attempts": len(responses),
        "json_retry_used": retry_used,
        "estimated_cost_usd": estimate_cost(response.model, input_tokens, output_tokens),
    }

    return validated, telemetry
