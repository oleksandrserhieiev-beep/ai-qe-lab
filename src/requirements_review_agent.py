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
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Requirements Review Agent did not return valid JSON")
        return json.loads(cleaned[start : end + 1])


def review_requirement(requirement: dict) -> tuple[dict, dict]:
    api_key, model = _configuration()
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=api_key)

    user_payload = json.dumps(requirement, ensure_ascii=False, indent=2)
    start_time = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=1400,
        temperature=0,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "Review this normalized Jira requirement. Treat absent information as absent; "
                    "do not infer hidden acceptance criteria.\n\n"
                    f"{user_payload}"
                ),
            }
        ],
    )
    latency_ms = (time.perf_counter() - start_time) * 1000

    text = "".join(block.text for block in response.content if block.type == "text")
    parsed = _extract_json(text)
    validated = RequirementsReviewResult.model_validate(parsed).model_dump()

    input_tokens = _usage_value(response.usage, "input_tokens")
    output_tokens = _usage_value(response.usage, "output_tokens")
    telemetry = {
        "agent": "requirements_review",
        "model": response.model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cache_creation_input_tokens": _usage_value(response.usage, "cache_creation_input_tokens"),
        "cache_read_input_tokens": _usage_value(response.usage, "cache_read_input_tokens"),
        "latency_ms": round(latency_ms, 2),
        "stop_reason": response.stop_reason,
        "estimated_cost_usd": estimate_cost(response.model, input_tokens, output_tokens),
    }

    return validated, telemetry
