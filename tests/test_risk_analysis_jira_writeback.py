import pytest

from risk_analysis_jira_writeback import append_approved_risks, risk_register_adf


def sample_risk():
    return {
        "risk_id": "R-1",
        "risk_type": "ai",
        "category": "ai",
        "risk_statement": "Unsupported claim",
        "likelihood": 4,
        "impact": 5,
        "risk_score": 20,
        "priority": "critical",
        "mitigation": ["Ground claims"],
        "recommended_test_focus": ["Missing attribute"],
    }


def test_writeback_requires_explicit_human_approval():
    with pytest.raises(ValueError, match="Explicit human approval"):
        append_approved_risks("SCRUM-1", [sample_risk()], approved=False)


def test_risk_register_contains_governed_fields():
    content = risk_register_adf([sample_risk()])
    rendered = " ".join(node.get("content", [{}])[0].get("text", "") for node in content)
    assert "Reviewed Risk Register" in rendered
    assert "Risk ID: R-1" in rendered
    assert "Priority: CRITICAL" in rendered
    assert "Mitigation: Ground claims" in rendered
    assert "Recommended Test Focus: Missing attribute" in rendered
