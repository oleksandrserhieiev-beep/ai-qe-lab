import json
import os
import time
from pathlib import Path
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

from cost_reporting import estimate_cost


load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "risk_analysis_prompt.txt"
PRIMARY_MAX_TOKENS = 2200
RETRY_MAX_TOKENS = 3200

RiskCategory = Literal["functional", "integration", "data", "ai", "security", "resilience", "performance", "business"]
RiskLevel = Literal["critical", "high", "medium", "low"]
Likelihood = Literal["high", "medium", "low"]
Impact = Literal["high", "medium", "low"]


class RiskItem(BaseModel):
    risk_id: str = Field(min_length=1)
    category: RiskCategory
    risk_statement: str = Field(min_length=1)
    likelihood: Likelihood
    impact: Impact
    priority: RiskLevel
    rationale: str = Field(min_length=1)
    evidence: list[str] = []
    recommended_test_focus: list[str] = []


class RiskAnalysisResult(BaseModel):
    issue_key: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    risks: list[RiskItem] = Field(min_length=1)
    overall_risk_level: RiskLevel
    recommended_next_action: Literal["continue_to_test_analysis_and_design"]


class RiskAnalysisInput(BaseModel):
    issue_key: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    description: str = ""
    acceptance_criteria: str = ""
    components: list[str] = []
    requirements_review_decision: Literal["READY"]
    known_constraints: list[str] = []
    dependencies: list[str] = []
    retrieved_evidence: list[dict] = []

    @model_validator(mode="after")
    def require_ready_gate(self):
        if self.requirements_review_decision != "READY":
            raise ValueError("Risk Analysis can run only after Requirements Review = READY")
        return self


def build_risk_analysis_input(requirement: dict, requirements_review: dict, retrieved_evidence: list[dict] | None = None) -> dict:
    payload = RiskAnalysisInput(
        issue_key=requirement.get("issue_key") or "",
        summary=requirement.get("summary") or "",
        description=requirement.get("description") or "",
        acceptance_criteria=requirement.get("acceptance_criteria") or "",
        components=requirement.get("components") or [],
        requirements_review_decision=requirements_review.get("decision"),
        known_constraints=requirements_review.get("known_constraints") or [],
        dependencies=requirements_review.get("dependencies") or [],
        retrieved_evidence=retrieved_evidence or [],
    )
    return payload.model_dump()


def validate_risk_analysis_output(payload: dict) -> dict:
    return RiskAnalysisResult.model_validate(payload).model_dump()


def compact_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _configuration() -> tuple[str, str]:
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("RISK_ANALYSIS_MODEL") or os.getenv("REQUIREMENTS_REVIEW_MODEL") or os.getenv("SUT_MODEL")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing")
    if not model:
        raise ValueError("RISK_ANALYSIS_MODEL, REQUIREMENTS_REVIEW_MODEL or SUT_MODEL is missing")
    return api_key, model


def _usage_value(usage, name: str) -> int:
    return int(getattr(usage, name, 0) or 0)


def _text_from_response(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Risk Analysis Agent returned an empty response")
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
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("Risk Analysis Agent did not return valid JSON") from original_error
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as sliced_error:
            raise ValueError("Risk Analysis Agent returned malformed or truncated JSON") from sliced_error


def _call_agent(client, model: str, system_prompt: str, messages: list[dict], max_tokens: int):
    return client.messages.create(model=model, max_tokens=max_tokens, system=system_prompt, messages=messages)


def analyze_risks(payload: dict) -> tuple[dict, dict]:
    validated_input = RiskAnalysisInput.model_validate(payload).model_dump()
    api_key, model = _configuration()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=api_key)
    messages = [{
        "role": "user",
        "content": "Analyze this READY requirement for material test-driving risks. Return one complete JSON object only.\n" + compact_payload(validated_input),
    }]

    start = time.perf_counter()
    responses = []
    last_error = None
    for attempt, max_tokens in enumerate((PRIMARY_MAX_TOKENS, RETRY_MAX_TOKENS), start=1):
        response = _call_agent(client, model, prompt, messages, max_tokens)
        responses.append(response)
        text = _text_from_response(response)
        try:
            result = validate_risk_analysis_output(_extract_json(text))
            if result["issue_key"] != validated_input["issue_key"]:
                raise ValueError("Risk Analysis output issue_key does not match input")
            break
        except Exception as exc:
            last_error = exc
            if attempt == 2:
                raise ValueError(f"Risk Analysis Agent contract failure after retry: {exc}") from exc
            messages.extend([
                {"role": "assistant", "content": text},
                {"role": "user", "content": "Repair the response. Return one complete valid JSON object matching the required schema only."},
            ])

    latency_ms = (time.perf_counter() - start) * 1000
    input_tokens = sum(_usage_value(item.usage, "input_tokens") for item in responses)
    output_tokens = sum(_usage_value(item.usage, "output_tokens") for item in responses)
    telemetry = {
        "agent": "risk_analysis",
        "model": responses[-1].model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": round(latency_ms, 2),
        "stop_reason": responses[-1].stop_reason,
        "attempts": len(responses),
        "contract_retry_used": len(responses) > 1,
        "estimated_cost_usd": estimate_cost(responses[-1].model, input_tokens, output_tokens),
    }
    return result, telemetry
