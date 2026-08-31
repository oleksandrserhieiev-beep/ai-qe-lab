from requirements_review_handoff import (
    BLOCKED,
    READY_FOR_RISK_ANALYSIS,
    build_handoff_from_review_report,
)


def _report(decision: str):
    return {
        "run_timestamp": "2026-08-31T20:00:00+00:00",
        "batch_run_id": "REQ-1",
        "issue_key": "SCRUM-2",
        "content_hash": "abc123",
        "review_payload": {
            "issue_key": "SCRUM-2",
            "summary": "Filter products by color",
            "description": "Customer can filter products by color.",
            "acceptance_criteria": "Selected color limits results to matching products.",
            "components": ["shopping"],
        },
        "review": {
            "decision": decision,
            "known_constraints": ["color must match"],
            "dependencies": ["product catalogue"],
        },
    }


def test_ready_review_creates_risk_analysis_handoff():
    handoff = build_handoff_from_review_report(_report("READY"))

    assert handoff["handoff_status"] == READY_FOR_RISK_ANALYSIS
    assert handoff["next_stage"] == "risk_analysis"
    assert handoff["risk_analysis_input"]["issue_key"] == "SCRUM-2"
    assert handoff["risk_analysis_input"]["requirements_review_decision"] == "READY"
    assert handoff["requirements_review_content_hash"] == "abc123"


def test_needs_clarification_blocks_risk_analysis_handoff():
    handoff = build_handoff_from_review_report(_report("NEEDS_CLARIFICATION"))

    assert handoff["handoff_status"] == BLOCKED
    assert handoff["next_stage"] is None
    assert handoff["risk_analysis_input"] is None
