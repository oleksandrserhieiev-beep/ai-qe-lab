import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from jira_requirements import normalize_requirement  # noqa: E402
from requirement_precheck import parse_issue_keys, precheck_requirement, validate_issue_key  # noqa: E402


def test_parse_issue_keys_normalizes_deduplicates_and_supports_separators():
    assert parse_issue_keys("aiqe-1, AIQE-2; aiqe-1\nAIQE-3") == ["AIQE-1", "AIQE-2", "AIQE-3"]


def test_validate_issue_key_rejects_wrong_project(monkeypatch):
    monkeypatch.setenv("JIRA_PROJECT_KEY", "AIQE")
    assert validate_issue_key("OTHER-1") == ["issue is outside configured project AIQE"]
    assert validate_issue_key("AIQE-1") == []


def test_precheck_rejects_wrong_status_and_missing_acceptance_criteria(monkeypatch):
    monkeypatch.setenv("JIRA_ALLOWED_STATUSES", "Ready for Refinement")
    monkeypatch.setenv("JIRA_REQUIRE_DESCRIPTION", "true")
    monkeypatch.setenv("JIRA_REQUIRE_ACCEPTANCE_CRITERIA", "true")

    reasons = precheck_requirement(
        {
            "status": "In Progress",
            "description": "Story description",
            "acceptance_criteria": "",
        }
    )

    assert any("status 'In Progress' is not eligible" in reason for reason in reasons)
    assert "acceptance criteria are missing" in reasons


def test_precheck_accepts_eligible_story(monkeypatch):
    monkeypatch.setenv("JIRA_ALLOWED_STATUSES", "Ready for Refinement,Ready for AI Review")
    monkeypatch.setenv("JIRA_REQUIRE_DESCRIPTION", "true")
    monkeypatch.setenv("JIRA_REQUIRE_ACCEPTANCE_CRITERIA", "true")

    assert precheck_requirement(
        {
            "status": "Ready for AI Review",
            "description": "As a shopper I want filtered products.",
            "acceptance_criteria": "Given a max price, returned products do not exceed it.",
        }
    ) == []


def test_normalize_requirement_extracts_explicit_ac_section_from_description(monkeypatch):
    monkeypatch.delenv("JIRA_ACCEPTANCE_CRITERIA_FIELD", raising=False)
    issue = {
        "key": "AIQE-1",
        "fields": {
            "summary": "Filter products",
            "description": "As a shopper I want filtered products.\nAcceptance Criteria:\nProducts must respect max price.",
            "status": {"name": "Ready for AI Review"},
            "issuetype": {"name": "Story"},
        },
    }

    normalized = normalize_requirement(issue)
    assert normalized["acceptance_criteria"] == "Products must respect max price."
