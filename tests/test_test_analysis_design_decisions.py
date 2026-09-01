import pytest

from test_analysis_design_decisions import apply_decision, build_decision_package


def _report():
    return {
        "run_timestamp": "2026-09-01T00:00:00Z",
        "results": [{
            "issue_key": "SCRUM-7",
            "status": "ANALYZED",
            "result": {
                "proposals": [
                    {
                        "proposed_id": "SCRUM-7-F1",
                        "title": "Missing price functional handling",
                        "test_kind": "functional",
                        "steps": ["Submit budget-constrained request"],
                        "expected": {"behavior": "Missing price does not satisfy budget"},
                    },
                    {
                        "proposed_id": "SCRUM-7-A1",
                        "title": "Missing price",
                        "test_kind": "ai",
                        "action": "ADD",
                        "target_suite": "pr_critical",
                        "oracle_type": "semantic",
                        "existing_case_id": None,
                    },
                ]
            },
        }],
    }


def test_build_decision_package_starts_pending_and_excludes_functional():
    package = build_decision_package(_report())
    assert len(package["proposals"]) == 1
    row = package["proposals"][0]
    assert row["proposed_id"] == "SCRUM-7-A1"
    assert row["decision"] == "PENDING"
    assert row["confirmed"] is False


def test_decision_requires_explicit_confirmation():
    package = build_decision_package(_report())
    with pytest.raises(ValueError, match="Human confirmation"):
        apply_decision(package, issue_key="SCRUM-7", proposed_id="SCRUM-7-A1", decision="APPROVE", confirmed=False)


def test_approve_is_recorded_only_after_confirmation():
    package = build_decision_package(_report())
    row = apply_decision(package, issue_key="SCRUM-7", proposed_id="SCRUM-7-A1", decision="APPROVE", confirmed=True)
    assert row["decision"] == "APPROVE"
    assert row["confirmed"] is True
