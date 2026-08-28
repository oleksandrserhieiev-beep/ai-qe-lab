import json
import os
import time

from anthropic import Anthropic, APIStatusError
from dotenv import load_dotenv


load_dotenv()

# Keep the stable rubric compact. Dynamic query/evidence/answer content stays in the user message.
JUDGE_SYSTEM = """Evaluate a Shopping Assistant using only supplied evidence.
Return JSON only with: correctness, groundedness, hallucination, constraint_adherence, context_coverage (0-100), context_sufficient, reason.
For abstention/refusal/out-of-domain, evidence can be sufficient when it supports abstention.
Use reason=null when all checks pass; otherwise one short reason."""

HIGH_RISK_LABELS = {
    "hallucination",
    "prompt_injection",
    "sensitive_data_handling",
    "conflicting_data",
    "policy_grounding",
}

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504, 529}
JUDGE_MAX_ATTEMPTS = int(os.getenv("JUDGE_MAX_ATTEMPTS", "4"))
JUDGE_RETRY_BASE_SECONDS = float(os.getenv("JUDGE_RETRY_BASE_SECONDS", "2"))
JUDGE_MAX_TOKENS = int(os.getenv("JUDGE_MAX_TOKENS", "180"))


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


def _create_judge_response(client, **kwargs):
    last_error = None

    for attempt in range(1, JUDGE_MAX_ATTEMPTS + 1):
        try:
            return client.messages.create(**kwargs), attempt
        except APIStatusError as exc:
            last_error = exc
            status_code = getattr(exc, "status_code", None)
            retryable = status_code in RETRYABLE_STATUS_CODES

            if not retryable or attempt >= JUDGE_MAX_ATTEMPTS:
                raise

            delay = JUDGE_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
            print(
                f"Judge API transient error {status_code}; "
                f"retry {attempt}/{JUDGE_MAX_ATTEMPTS} in {delay:.1f}s"
            )
            time.sleep(delay)

    raise last_error


def evaluate_ai_response(
    query,
    expected_behavior,
    actual_answer,
    retrieved_context,
    risk=None,
):
    api_key, judge_model = get_judge_configuration(risk=risk)
    client = Anthropic(api_key=api_key, max_retries=0)

    # Compact field labels reduce repeated Judge input while preserving the same semantic evidence.
    prompt = (
        f"Q:{query}\n"
        f"X:{expected_behavior}\n"
        f"E:{retrieved_context}\n"
        f"A:{actual_answer}\n"
        'JSON:{"correctness":true,"groundedness":true,"hallucination":false,'
        '"constraint_adherence":true,"context_coverage":100,'
        '"context_sufficient":true,"reason":null}'
    )

    response, attempts = _create_judge_response(
        client,
        model=judge_model,
        max_tokens=JUDGE_MAX_TOKENS,
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
        "api_attempts": attempts,
    }
    return result
