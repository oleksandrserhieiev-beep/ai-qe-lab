from requirements_review_cache import (
    build_review_payload,
    content_hash,
    get_cached_review,
    load_cache,
    put_cached_review,
    save_cache,
)


def test_review_payload_excludes_operational_jira_fields():
    requirement = {
        "issue_key": "SCRUM-2",
        "summary": "Search products",
        "description": "As a customer...",
        "acceptance_criteria": "Given...",
        "issue_type": "Story",
        "parent_key": "SCRUM-1",
        "status": "In Progress",
        "priority": "High",
        "labels": ["ai"],
        "components": ["Search"],
        "assignee": "Alex",
        "reporter": "PO",
    }

    payload = build_review_payload(requirement)

    assert payload == {
        "issue_key": "SCRUM-2",
        "summary": "Search products",
        "description": "As a customer...",
        "acceptance_criteria": "Given...",
        "issue_type": "Story",
        "parent_key": "SCRUM-1",
    }


def test_hash_changes_when_semantic_content_changes():
    first = {"issue_key": "SCRUM-2", "summary": "A", "description": "B", "acceptance_criteria": "C"}
    second = {**first, "acceptance_criteria": "Changed"}

    assert content_hash(first, model="claude", prompt_text="prompt") != content_hash(
        second, model="claude", prompt_text="prompt"
    )


def test_hash_changes_when_prompt_or_model_changes():
    payload = {"issue_key": "SCRUM-2", "summary": "A"}
    base = content_hash(payload, model="claude-a", prompt_text="prompt-a")

    assert base != content_hash(payload, model="claude-b", prompt_text="prompt-a")
    assert base != content_hash(payload, model="claude-a", prompt_text="prompt-b")


def test_cache_round_trip(tmp_path):
    path = tmp_path / "cache.json"
    cache = load_cache(path)
    review = {"decision": "READY", "readiness_score": 90}

    put_cached_review(
        cache,
        "SCRUM-2",
        "abc123",
        review=review,
        model="claude",
        reviewed_at="2026-08-31T08:00:00+00:00",
    )
    save_cache(cache, path)

    restored = load_cache(path)
    hit = get_cached_review(restored, "SCRUM-2", "abc123")
    miss = get_cached_review(restored, "SCRUM-2", "different")

    assert hit["review"] == review
    assert miss is None
