from pathlib import Path

from agent_content_cache import fingerprint, get_cached, load_cache, put_cached, save_cache


DEFAULT_CACHE_PATH = Path(".cache/test-analysis-design/cache.json")
AGENT_NAME = "test_analysis_design"


def content_fingerprint(*, issue_key: str, acceptance_criteria: str, risks: list[dict], dataset_snapshot: dict, model: str, prompt_text: str) -> str:
    semantic_input = {
        "issue_key": issue_key,
        "acceptance_criteria": acceptance_criteria,
        "risks": risks,
        "dataset_snapshot": dataset_snapshot,
    }
    return fingerprint(agent=AGENT_NAME, semantic_input=semantic_input, model=model, prompt_text=prompt_text)


__all__ = ["DEFAULT_CACHE_PATH", "content_fingerprint", "get_cached", "load_cache", "put_cached", "save_cache"]
