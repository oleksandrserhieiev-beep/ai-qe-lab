import os
import re


ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*-\d+$")


def parse_issue_keys(raw: str) -> list[str]:
    tokens = re.split(r"[\s,;]+", raw.strip())
    seen = set()
    result = []
    for token in tokens:
        key = token.strip().upper()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    return result


def allowed_statuses() -> set[str]:
    raw = os.getenv("JIRA_ALLOWED_STATUSES", "Ready for Refinement,Ready for AI Review")
    return {item.strip().casefold() for item in raw.split(",") if item.strip()}


def validate_issue_key(issue_key: str) -> list[str]:
    reasons = []
    if not ISSUE_KEY_PATTERN.match(issue_key):
        reasons.append("invalid Jira issue key format")
        return reasons

    project_key = (os.getenv("JIRA_PROJECT_KEY") or "").strip().upper()
    if project_key and not issue_key.startswith(f"{project_key}-"):
        reasons.append(f"issue is outside configured project {project_key}")
    return reasons


def precheck_requirement(requirement: dict) -> list[str]:
    reasons = []
    status = str(requirement.get("status") or "").strip()
    if status.casefold() not in allowed_statuses():
        allowed = ", ".join(sorted(os.getenv("JIRA_ALLOWED_STATUSES", "Ready for Refinement,Ready for AI Review").split(",")))
        reasons.append(f"status '{status or 'missing'}' is not eligible; allowed: {allowed}")

    require_description = os.getenv("JIRA_REQUIRE_DESCRIPTION", "true").strip().lower() in {"1", "true", "yes", "y"}
    if require_description and not str(requirement.get("description") or "").strip():
        reasons.append("description is missing")

    require_ac = os.getenv("JIRA_REQUIRE_ACCEPTANCE_CRITERIA", "true").strip().lower() in {"1", "true", "yes", "y"}
    if require_ac and not str(requirement.get("acceptance_criteria") or "").strip():
        reasons.append("acceptance criteria are missing")

    return reasons
