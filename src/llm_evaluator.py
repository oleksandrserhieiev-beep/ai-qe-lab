import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
JUDGE_MODEL = os.getenv("JUDGE_MODEL")

if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY is missing in .env")

if not JUDGE_MODEL:
    raise ValueError("JUDGE_MODEL is missing")


client = Anthropic(api_key=LLM_API_KEY)


def evaluate_ai_response(
    query,
    expected_behavior,
    actual_answer,
    retrieved_context,
):
    prompt = f"""
You are an AI quality evaluator.

Evaluate the Shopping Assistant response.

USER QUERY:
{query}

EXPECTED BEHAVIOR:
{expected_behavior}

RETRIEVED CONTEXT:
{retrieved_context}

ACTUAL ANSWER:
{actual_answer}

Evaluate these dimensions:

1. correctness
Does the answer satisfy the expected behavior?

2. groundedness
Are the factual claims in the answer supported by the retrieved context?

3. hallucination
Does the answer contain factual claims unsupported by the retrieved context?

4. constraint_adherence
Does the answer respect the constraints in the user query and expected behavior?

Return ONLY valid JSON:

{{
  "correctness": true,
  "groundedness": true,
  "hallucination": false,
  "constraint_adherence": true,
  "reason": "short explanation"
}}
"""

    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1000,
        thinking={"type": "disabled"},
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text = "".join(
        block.text
        for block in response.content
        if block.type == "text"
    )

    text = text.strip()

    if not text:
        raise ValueError(
            f"Judge returned no text. "
            f"model={response.model}, "
            f"stop_reason={response.stop_reason}, "
            f"content_types={[block.type for block in response.content]}"
        )

    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())