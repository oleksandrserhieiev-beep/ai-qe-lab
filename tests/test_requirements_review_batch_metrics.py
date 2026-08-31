from run_requirements_review_batch import _batch_quality_metrics, _cached_entry_for_run, _safe_rate


def test_safe_rate_handles_zero_denominator():
    assert _safe_rate(0, 0) == 0.0
    assert _safe_rate(5, 7) == 71.4


def test_force_review_bypasses_matching_cache_entry():
    cache = {
        "issues": {
            "SCRUM-1": {
                "content_hash": "abc",
                "review": {"decision": "READY", "readiness_score": 90},
            }
        }
    }

    assert _cached_entry_for_run(cache, "SCRUM-1", "abc", force_review=False) is not None
    assert _cached_entry_for_run(cache, "SCRUM-1", "abc", force_review=True) is None


def test_batch_quality_metrics_counts_quality_cache_and_llm_paths():
    issues = [
        {"issue_key": "SCRUM-1", "precheck": "ELIGIBLE", "cache_hit": True, "decision": "READY"},
        {
            "issue_key": "SCRUM-2",
            "precheck": "ELIGIBLE",
            "cache_hit": True,
            "decision": "NEEDS_CLARIFICATION",
        },
        {"issue_key": "SCRUM-3", "precheck": "ELIGIBLE", "cache_hit": False, "decision": "READY"},
        {
            "issue_key": "SCRUM-4",
            "precheck": "ELIGIBLE",
            "cache_hit": False,
            "decision": "NEEDS_CLARIFICATION",
        },
        {"issue_key": "SCRUM-5", "precheck": "ELIGIBLE", "cache_hit": False, "error": "provider failure"},
        {"issue_key": "SCRUM-6", "precheck": "REJECTED", "rejection_reasons": ["acceptance criteria are missing"]},
    ]

    assert _batch_quality_metrics(issues) == {
        "eligible": 5,
        "ready": 2,
        "needs_clarification": 2,
        "cache_hits": 2,
        "llm_attempted": 3,
        "cache_hit_rate_pct": 40.0,
        "llm_execution_rate_pct": 60.0,
        "avoided_llm_calls": 2,
    }
