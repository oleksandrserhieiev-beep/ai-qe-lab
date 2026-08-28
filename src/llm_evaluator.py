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

5. context_coverage
Estimate how much of the information required to satisfy the EXPECTED BEHAVIOR is available in the RETRIEVED CONTEXT itself.
Return an integer from 0 to 100.
100 means the context contains all information needed for the expected behavior.
0 means the context contains none of the required information.
For abstention, refusal, or out-of-domain cases, return 100 when the context/system evidence is sufficient to justify the expected abstention or refusal.
Do not judge the quality of the ACTUAL ANSWER when scoring context_coverage.

6. context_sufficient
Return true when the retrieved context is sufficient to produce the expected behavior without inventing missing facts.

Return ONLY valid JSON:

{{
  "correctness": true,
  "groundedness": true,
  "hallucination": false,
  "constraint_adherence": true,
  "context_coverage": 100,
  "context_sufficient": true,
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

    result = json.loads(text.strip())

    coverage = result.get("context_coverage", 0)

    try:
        coverage = int(round(float(coverage)))
    except (TypeError, ValueError):
        coverage = 0

    result["context_coverage"] = max(
        0,
        min(100, coverage),
    )

    result["context_sufficient"] = bool(
        result.get("context_sufficient", False)
    )

    return result
