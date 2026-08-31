import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()

BASE_FIELDS = [
    "summary",
    "description",
    "status",
    "issuetype",
    "priority",
    "labels",
    "components",
    "assignee",
    "reporter",
    "parent",
]


def _configuration():
    base_url = (os.getenv("JIRA_BASE_URL") or "").rstrip("/")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    missing = [
        name
        for name, value in (
            ("JIRA_BASE_URL", base_url),
            ("JIRA_EMAIL", email),
            ("JIRA_API_TOKEN", api_token),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing Jira configuration: {', '.join(missing)}")

    return base_url, email, api_token


def _adf_to_text(value: Any) -> str:
    """Flatten Jira Atlassian Document Format or plain values to readable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [_adf_to_text(item) for item in value]
        return "\n".join(part for part in parts if part).strip()
    if not isinstance(value, dict):
        return str(value).strip()

    node_type = value.get("type")
    if node_type == "text":
        return str(value.get("text") or "")
    if node_type == "hardBreak":
        return "\n"

    content = value.get("content") or []
    rendered = [_adf_to_text(item) for item in content]
    rendered = [part for part in rendered if part]

    if node_type in {"paragraph", "heading", "blockquote", "listItem"}:
        return " ".join(rendered).strip()
    if node_type in {"bulletList", "orderedList", "doc"}:
        return "\n".join(rendered).strip()

    return " ".join(rendered).strip()


def _acceptance_criteria_from_description(description: str) -> str:
    """Extract an explicit Acceptance Criteria section when AC is stored in Description."""
    if not description:
        return ""
    match = re.search(
        r"(?is)(?:^|\n)\s*(?:acceptance\s+criteria|acceptance\s+criterion|ac)\s*:?\s*(?:\n|$)(.+)$",
        description,
    )
    return match.group(1).strip() if match else ""


def fetch_issue(issue_key: str) -> dict:
    base_url, email, api_token = _configuration()
    url = f"{base_url}/rest/api/3/issue/{issue_key}"
    acceptance_criteria_field = (os.getenv("JIRA_ACCEPTANCE_CRITERIA_FIELD") or "").strip()
    fields = [*BASE_FIELDS]
    if acceptance_criteria_field:
        fields.append(acceptance_criteria_field)

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params={"fields": ",".join(fields)}, auth=(email, api_token))
        response.raise_for_status()
        return response.json()


def normalize_requirement(issue: dict) -> dict:
    fields = issue.get("fields") or {}
    acceptance_criteria_field = (os.getenv("JIRA_ACCEPTANCE_CRITERIA_FIELD") or "").strip()

    def _name(value):
        return (value or {}).get("name") if isinstance(value, dict) else None

    description = _adf_to_text(fields.get("description"))
    acceptance_criteria = ""
    if acceptance_criteria_field:
        acceptance_criteria = _adf_to_text(fields.get(acceptance_criteria_field))
    if not acceptance_criteria:
        acceptance_criteria = _acceptance_criteria_from_description(description)

    return {
        "source": "jira",
        "issue_key": issue.get("key"),
        "summary": fields.get("summary") or "",
        "description": description,
        "acceptance_criteria": acceptance_criteria,
        "status": _name(fields.get("status")),
        "issue_type": _name(fields.get("issuetype")),
        "priority": _name(fields.get("priority")),
        "labels": fields.get("labels") or [],
        "components": [item.get("name") for item in fields.get("components") or [] if item.get("name")],
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "parent_key": (fields.get("parent") or {}).get("key"),
    }


def load_requirement(issue_key: str) -> dict:
    return normalize_requirement(fetch_issue(issue_key))
