from test_analysis_design import TestAnalysisDesignResult, TestProposal, can_propose, dataset_health_check
from test_analysis_design_cache import content_fingerprint


def test_dataset_errors_block_proposals_but_warnings_do_not():
    required = {"id", "input", "expected", "active"}
    broken = dataset_health_check([{"id": "E-1", "input": {}, "active": True}], required)
    assert can_propose(broken) is False
    warnings = dataset_health_check([{"id": "E-2", "input": {"q": "x"}, "expected": {"ok": True}, "active": False}], required)
    assert can_propose(warnings) is True
    assert warnings[0].severity == "WARNING"


def test_extend_existing_requires_before_after_contract():
    proposal = TestProposal(
        proposed_id="P-1",
        title="Extend grounding coverage",
        test_kind="ai",
        traceability={"issue_key": "SCRUM-5", "acceptance_criteria": ["AC-2"], "risk_ids": ["R1"]},
        oracle_type="semantic",
        target_suite="regression",
        target_rationale="Semantic grounding coverage is valuable but not required on every PR.",
        action="EXTEND_EXISTING",
        input={"query": "recommend a jacket"},
        expected={"grounded": True},
        similar_cases=[{"case_id": "AI-043", "similarity_score": 0.68, "coverage_note": "Same grounding intent; missing insufficient-context branch."}],
        existing_case_id="AI-043",
        proposed_extension={"add_expected_behavior": "refuse unsupported recommendation when context is insufficient"},
    )
    assert proposal.action == "EXTEND_EXISTING"
    assert proposal.traceability.risk_ids == ["R1"]


def test_result_blocks_on_dataset_error():
    result = TestAnalysisDesignResult(issue_key="SCRUM-5", health_findings=[{"severity": "ERROR", "code": "BROKEN_REFERENCE", "message": "Referenced fixture does not exist", "dataset": "evaluation", "record_id": "AI-1"}])
    assert result.blocked is True


def test_cache_changes_when_dataset_or_risks_change():
    common = dict(issue_key="SCRUM-5", acceptance_criteria="AC", model="claude-sonnet-5", prompt_text="v1")
    a = content_fingerprint(**common, risks=[{"id": "R1"}], dataset_snapshot={"sha": "aaa"})
    b = content_fingerprint(**common, risks=[{"id": "R1"}], dataset_snapshot={"sha": "bbb"})
    c = content_fingerprint(**common, risks=[{"id": "R2"}], dataset_snapshot={"sha": "aaa"})
    assert a != b
    assert a != c
