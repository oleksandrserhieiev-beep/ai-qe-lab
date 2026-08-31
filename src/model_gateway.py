import os
import time

import httpx
from anthropic import Anthropic

from context_builder import SYSTEM_INSTRUCTION


def provider_for_model(model):
    value = model.lower()
    if value.startswith("claude-"):
        return "anthropic"
    if value.startswith("gpt-"):
        return "openai"
    raise ValueError(f"Unsupported model family: {model}")


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
            response = client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
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
