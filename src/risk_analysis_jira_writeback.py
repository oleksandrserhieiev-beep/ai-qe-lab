import os
from typing import Any

import httpx


def _configuration() -> tuple[str, str, str]:
    base_url = (os.getenv("JIRA_BASE_URL") or "").rstrip("/")
    email = os.getenv("JIRA_EMAIL") or ""
    token = os.getenv("JIRA_API_TOKEN") or ""
    missing = [name for name, value in (("JIRA_BASE_URL", base_url), ("JIRA_EMAIL", email), ("JIRA_API_TOKEN", token)) if not value]
    if missing:
        raise ValueError(f"Missing Jira configuration: {', '.join(missing)}")
    return base_url, email, token


def _text_node(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [_text_node(text)]}


def risk_register_adf(risks: list[dict]) -> list[dict]:
    content = [{"type": "heading", "attrs": {"level": 2}, "content": [_text_node("Reviewed Risk Register")]}]
    for risk in risks:
        content.extend([
            _paragraph(f"Risk ID: {risk['risk_id']}"),
            _paragraph(f"Risk Type: {risk['risk_type']}"),
            _paragraph(f"Category: {risk['category']}"),
            _paragraph(f"Risk: {risk['risk_statement']}"),
            _paragraph(f"Likelihood: {risk['likelihood']}"),
            _paragraph(f"Impact: {risk['impact']}"),
            _paragraph(f"Score: {risk['risk_score']}"),
            _paragraph(f"Priority: {str(risk['priority']).upper()}"),
            _paragraph("Mitigation: " + "; ".join(risk.get("mitigation") or [])),
            _paragraph("Recommended Test Focus: " + "; ".join(risk.get("recommended_test_focus") or [])),
        ])
    return content


def append_approved_risks(issue_key: str, risks: list[dict], *, approved: bool) -> dict:
    if not approved:
        raise ValueError("Explicit human approval is required before Jira write-back")
    if not risks:
        raise ValueError("No approved risks supplied for Jira write-back")
    base_url, email, token = _configuration()
    url = f"{base_url}/rest/api/3/issue/{issue_key}"
    auth = (email, token)
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params={"fields": "description,labels"}, auth=auth)
        response.raise_for_status()
        fields = response.json().get("fields") or {}
        description = fields.get("description") or {"type": "doc", "version": 1, "content": []}
        content = list(description.get("content") or [])
        content.extend(risk_register_adf(risks))
        labels = list(fields.get("labels") or [])
        completed_label = (os.getenv("JIRA_RISK_ANALYSIS_COMPLETED_LABEL") or "risk-analysis-completed").strip()
        if completed_label and completed_label not in labels:
            labels.append(completed_label)
        update = client.put(url, json={"fields": {"description": {"type": "doc", "version": 1, "content": content}, "labels": labels}}, auth=auth)
        update.raise_for_status()
    return {"issue_key": issue_key, "updated": True, "label": completed_label, "risk_count": len(risks)}
