import os
import time

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
SUT_MODEL = os.getenv("SUT_MODEL")

if not SUT_MODEL:
    raise ValueError("SUT_MODEL is missing")

if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY is missing in .env")


client = Anthropic(api_key=LLM_API_KEY)


def generate_answer(final_context):
    start_time = time.perf_counter()

    response = client.messages.create(
        model=SUT_MODEL,
        max_tokens=1000,
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
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms": round(latency_ms, 2),
        "stop_reason": response.stop_reason,
    }

    return answer, telemetry