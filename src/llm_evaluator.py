import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

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
        model=LLM_MODEL,
        max_tokens=500,
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

    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())