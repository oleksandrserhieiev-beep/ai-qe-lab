from pathlib import Path


PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "requirements_review_prompt.txt"


def test_prompt_contains_primary_quality_criteria_and_gap_types():
    prompt = PROMPT_PATH.read_text(encoding="utf-8").lower()
    for criterion in ["unambiguous", "complete", "consistent", "singular", "verifiable"]:
        assert criterion in prompt
    for gap_type in ["blocking_gap", "non_blocking_gap", "technical_context_needed"]:
        assert gap_type in prompt
