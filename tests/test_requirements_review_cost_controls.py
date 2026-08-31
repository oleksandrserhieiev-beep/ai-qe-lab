from pathlib import Path

from requirements_review_agent import PRIMARY_MAX_TOKENS, RETRY_MAX_TOKENS


PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "requirements_review_prompt.txt"


def test_requirements_review_output_budget_is_bounded():
    assert PRIMARY_MAX_TOKENS <= 1800
    assert RETRY_MAX_TOKENS <= 2800


def test_prompt_requests_concise_non_duplicate_output():
    prompt = PROMPT_PATH.read_text(encoding="utf-8").lower()
    assert "be concise" in prompt
    assert "consolidate duplicate" in prompt
    assert "do not repeat" in prompt
