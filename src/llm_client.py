import os
import time

from anthropic import Anthropic
from dotenv import load_dotenv

from context_builder import SYSTEM_INSTRUCTION


load_dotenv()


def _configuration():
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("SUT_MODEL")
    if not model:
        raise ValueError("SUT_MODEL is missing")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing in .env")
    return api_key, model


def _usage_value(usage, name):
    return int(getattr(usage, name, 0) or 0)


def generate_answer(final_context):
    api_key, model = _configuration()
    client = Anthropic(api_key=api_key)
    start_time = time.perf_counter()

    response = client.messages.create(
        model=model,
        max_tokens=700,
        system=[
            {
                "type": "text",
                "text": SYSTEM_INSTRUCTION,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": final_context,
            }
        ],
    )

    latency_ms = (time.perf_counter() - start_time) * 1000

    answer = "".join(
        block.text
        for block in response.content
        if block.type == "text"
    )

    telemetry = {
        "model": response.model,
        "input_tokens": _usage_value(response.usage, "input_tokens"),
        "output_tokens": _usage_value(response.usage, "output_tokens"),
        "cache_creation_input_tokens": _usage_value(
            response.usage, "cache_creation_input_tokens"
        ),
        "cache_read_input_tokens": _usage_value(
            response.usage, "cache_read_input_tokens"
        ),
        "latency_ms": round(latency_ms, 2),
        "stop_reason": response.stop_reason,
    }

    return answer, telemetry
