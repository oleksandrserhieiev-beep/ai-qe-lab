from pathlib import Path

from agent_content_cache import fingerprint, get_cached, load_cache, put_cached, save_cache


def test_fingerprint_changes_when_semantic_input_changes():
    first = fingerprint(agent="risk", semantic_input={"issue_key": "AX-1", "ac": "A"}, model="m1", prompt_text="p1")
    second = fingerprint(agent="risk", semantic_input={"issue_key": "AX-1", "ac": "B"}, model="m1", prompt_text="p1")
    assert first != second


def test_fingerprint_changes_when_model_or_prompt_changes():
    base = fingerprint(agent="risk", semantic_input={"issue_key": "AX-1"}, model="m1", prompt_text="p1")
    assert base != fingerprint(agent="risk", semantic_input={"issue_key": "AX-1"}, model="m2", prompt_text="p1")
    assert base != fingerprint(agent="risk", semantic_input={"issue_key": "AX-1"}, model="m1", prompt_text="p2")


def test_cache_round_trip(tmp_path: Path):
    path = tmp_path / "cache.json"
    cache = load_cache(path)
    content_hash = fingerprint(agent="risk", semantic_input={"issue_key": "AX-1"}, model="m1", prompt_text="p1")
    put_cached(cache, "AX-1", content_hash, result={"risks": [{"risk_id": "R-1"}]}, model="m1", created_at="2026-09-01T00:00:00Z")
    save_cache(cache, path)

    loaded = load_cache(path)
    entry = get_cached(loaded, "AX-1", content_hash)
    assert entry is not None
    assert entry["result"]["risks"][0]["risk_id"] == "R-1"


def test_cache_miss_when_hash_changes(tmp_path: Path):
    path = tmp_path / "cache.json"
    cache = load_cache(path)
    put_cached(cache, "AX-1", "old", result={"risks": []}, model="m1", created_at="2026-09-01T00:00:00Z")
    assert get_cached(cache, "AX-1", "new") is None
