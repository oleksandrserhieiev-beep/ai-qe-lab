import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

JUDGE_SYSTEM = """You are an AI quality evaluator for a Shopping Assistant.
Return only valid JSON. Evaluate only semantic qualities that require model judgment.
Metrics: correctness, groundedness, hallucination, constraint_adherence, context_coverage (0-100), context_sufficient.
For abstention/refusal/out-of-domain cases, context may be sufficient when evidence justifies abstention.
Set reason to null when all checks pass. When any check fails, provide one short diagnostic reason.
Do not restate the query, evidence, answer, rubric, or JSON schema outside the JSON object."""

HIGH_RISK_LABELS = {
    "hallucination",
    "prompt_injection",
    "sensitive_data_handling",
    "conflicting_data",
    "policy_grounding",
}


def get_judge_configuration(risk=None):
    api_key = os.getenv("LLM_API_KEY")
    primary_model = os.getenv("JUDGE_MODEL")
    light_model = os.getenv("JUDGE_MODEL_LIGHT")

    if not api_key:
        raise ValueError("LLM_API_KEY is missing in .env")
    if not primary_model:
        raise ValueError("JUDGE_MODEL is missing")

    risks = risk if isinstance(risk, list) else [risk] if risk else []
    use_primary = not light_model or any(item in HIGH_RISK_LABELS for item in risks)
    return api_key, primary_model if use_primary else light_model


def _usage_value(usage, name):
    return int(getattr(usage, name, 0) or 0)


def evaluate_ai_response(
    query,
    expected_behavior,
    actual_answer,
    retrieved_context,
    risk=None,
):
    api_key, judge_model = get_judge_configuration(risk=risk)
    client = Anthropic(api_key=api_key)

    prompt = f"""QUERY:
{query}

EXPECTED:
{expected_behavior}

EVIDENCE:
{retrieved_context}

ANSWER:
{actual_answer}

Return exactly:
{{"correctness":true,"groundedness":true,"hallucination":false,"constraint_adherence":true,"context_coverage":100,"context_sufficient":true,"reason":null}}"""

    response = client.messages.create(
        model=judge_model,
        max_tokens=350,
        thinking={"type": "disabled"},
        system=[
            {
                "type": "text",
                "text": JUDGE_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    if not text:
        raise ValueError(
            f"Judge returned no text. model={response.model}, "
            f"stop_reason={response.stop_reason}, "
            f"content_types={[block.type for block in response.content]}"
        )

    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    result = json.loads(text.strip())

    try:
        coverage = int(round(float(result.get("context_coverage", 0))))
    except (TypeError, ValueError):
        coverage = 0

    result["context_coverage"] = max(0, min(100, coverage))
    result["context_sufficient"] = bool(result.get("context_sufficient", False))
    result["reason"] = result.get("reason") or None
    result["_telemetry"] = {
        "model": response.model,
        "input_tokens": _usage_value(response.usage, "input_tokens"),
        "output_tokens": _usage_value(response.usage, "output_tokens"),
        "cache_creation_input_tokens": _usage_value(
            response.usage, "cache_creation_input_tokens"
        ),
        "cache_read_input_tokens": _usage_value(
            response.usage, "cache_read_input_tokens"
        ),
        "stop_reason": response.stop_reason,
    }
    return result
