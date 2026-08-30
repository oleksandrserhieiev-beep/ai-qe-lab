import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from jira_requirements import normalize_requirement  # noqa: E402
from requirements_review_agent import _extract_json, RequirementsReviewResult  # noqa: E402


def test_normalize_requirement_flattens_jira_adf_description():
    issue = {
        "key": "SCRUM-1",
        "fields": {
            "summary": "Recommend products",
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "As a customer I want recommendations."}],
                    },
                    {
                        "type": "bulletList",
                        "content": [
                            {
                                "type": "listItem",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "Respect max price."}],
                                    }
                                ],
                            }
                        ],
                    },
                ],
            },
            "status": {"name": "To Do"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "labels": ["ai-qe"],
            "components": [{"name": "Shopping Assistant"}],
            "assignee": {"displayName": "QA User"},
            "reporter": {"displayName": "PO User"},
            "parent": {"key": "SCRUM-EPIC"},
        },
    }

    normalized = normalize_requirement(issue)

    assert normalized["issue_key"] == "SCRUM-1"
    assert "As a customer I want recommendations." in normalized["description"]
    assert "Respect max price." in normalized["description"]
    assert normalized["status"] == "To Do"
    assert normalized["components"] == ["Shopping Assistant"]


def test_extract_json_accepts_fenced_json_and_schema_validates():
    raw = """```json
    {
      "decision": "NEEDS_CLARIFICATION",
      "readiness_score": 65,
      "summary": "Missing negative behavior.",
      "gaps": [
        {
          "category": "negative_flow",
          "severity": "medium",
          "finding": "No failure behavior is defined.",
          "clarification_question": "What should happen when no match exists?"
        }
      ],
      "known_constraints": ["maximum price"],
      "dependencies": [],
      "testability_notes": ["Expected no-match behavior is required."],
      "recommended_next_action": "clarify_requirement"
    }
    ```"""

    parsed = _extract_json(raw)
    validated = RequirementsReviewResult.model_validate(parsed)

    assert validated.decision == "NEEDS_CLARIFICATION"
    assert validated.readiness_score == 65
    assert validated.gaps[0].category == "negative_flow"
