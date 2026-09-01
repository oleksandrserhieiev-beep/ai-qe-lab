import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from jira_requirements import load_requirement
from requirement_precheck import parse_issue_keys, validate_issue_key
from risk_analysis_agent import analyze_risks, build_risk_analysis_input


STATE_PATH = Path("reports/risk_analysis_batch_state.json")
REPORT_PATH = Path("reports/risk_analysis_batch.json")
DEFAULT_REVIEW_LABEL = "review-completed"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _review_label() -> str:
    return (os.getenv("JIRA_REVIEW_COMPLETED_LABEL") or DEFAULT_REVIEW_LABEL).strip()


def eligibility_reasons(requirement: dict, review_label: str | None = None) -> list[str]:
    reasons = []
    required_label = (review_label or _review_label()).casefold()
    labels = {str(label).strip().casefold() for label in requirement.get("labels") or []}
    if required_label not in labels:
        reasons.append(f"required label '{review_label or _review_label()}' is missing")
    if not str(requirement.get("acceptance_criteria") or "").strip():
        reasons.append("acceptance criteria are missing")
    return reasons


def _escape(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _append_summary(lines: list[str]) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _centered_markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(":---:" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_escape(value) for value in row) + " |")
    return lines


def check(raw_issue_keys: str) -> dict:
    issue_keys = parse_issue_keys(raw_issue_keys)
    if not issue_keys:
        raise ValueError("At least one Jira issue key is required")

    items = []
    eligible_requirements = []
    review_label = _review_label()

    for issue_key in issue_keys:
        item = {"issue_key": issue_key, "status": "PENDING", "reasons": []}
        key_reasons = validate_issue_key(issue_key)
        if key_reasons:
            item.update(status="INELIGIBLE", reasons=key_reasons)
            items.append(item)
            continue

        try:
            requirement = load_requirement(issue_key)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            reason = "ticket not found or inaccessible" if status_code == 404 else f"Jira returned HTTP {status_code}"
            item.update(status="INELIGIBLE", reasons=[reason])
            items.append(item)
            continue
        except Exception as exc:
            item.update(status="INELIGIBLE", reasons=[f"Jira load failed: {exc}"])
            items.append(item)
            continue

        reasons = eligibility_reasons(requirement, review_label)
        if reasons:
            item.update(status="INELIGIBLE", reasons=reasons)
        else:
            item["status"] = "ELIGIBLE"
            eligible_requirements.append(requirement)
        items.append(item)

    state = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "review_completed_label": review_label,
        "requested": len(issue_keys),
        "eligible": len(eligible_requirements),
        "ineligible": len(issue_keys) - len(eligible_requirements),
        "items": items,
        "eligible_requirements": eligible_requirements,
    }
    _write_json(STATE_PATH, state)

    rows = [[item["issue_key"], item["status"], "; ".join(item["reasons"]) or "-"] for item in items]
    _append_summary([
        "## Risk Analysis — Eligibility Check",
        "",
        f"**Required Jira label:** `{review_label}`  ",
        f"**Requested:** {state['requested']} | **Eligible:** {state['eligible']} | **Ineligible:** {state['ineligible']}",
        "",
        *_centered_markdown_table(["Issue", "Eligibility", "Reason"], rows),
        "",
        "No LLM call is made for ineligible tickets.",
    ])

    if not eligible_requirements:
        print("No eligible tickets for Risk Analysis.")
    else:
        print(f"Eligible tickets for Risk Analysis: {len(eligible_requirements)}")
    return state


def analyze() -> dict:
    state = _read_json(STATE_PATH)
    results = []
    total_tokens = 0
    total_cost = 0.0

    for requirement in state.get("eligible_requirements", []):
        issue_key = requirement["issue_key"]
        try:
            payload = build_risk_analysis_input(
                requirement,
                {"decision": "READY", "known_constraints": [], "dependencies": []},
            )
            result, telemetry = analyze_risks(payload)
            total_tokens += int(telemetry.get("total_tokens") or 0)
            total_cost += float(telemetry.get("estimated_cost_usd") or 0.0)
            results.append({"issue_key": issue_key, "status": "ANALYZED", "result": result, "telemetry": telemetry})
        except Exception as exc:
            results.append({"issue_key": issue_key, "status": "ERROR", "error": str(exc)})

    report = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "requested": state["requested"],
        "eligible": state["eligible"],
        "analyzed": sum(1 for item in results if item["status"] == "ANALYZED"),
        "failed": sum(1 for item in results if item["status"] == "ERROR"),
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(total_cost, 6),
        "eligibility": state["items"],
        "results": results,
    }
    _write_json(REPORT_PATH, report)

    if not results:
        print("No eligible tickets for Risk Analysis. LLM execution skipped.")
    else:
        print(f"Risk Analysis completed: {report['analyzed']} analyzed, {report['failed']} failed")
    return report


def _risk_rows(report: dict) -> list[dict]:
    rows = []
    for item in report.get("results", []):
        if item.get("status") != "ANALYZED":
            continue
        for risk in item["result"].get("risks", []):
            rows.append({"issue_key": item["issue_key"], **risk})
    return rows


def render_scores() -> None:
    report = _read_json(REPORT_PATH)
    risks = _risk_rows(report)
    rows = [
        [risk["issue_key"], risk["risk_id"], risk["likelihood"], risk["impact"], f"{risk['likelihood']} × {risk['impact']}", risk["risk_score"]]
        for risk in risks
    ]
    _append_summary([
        "## Risk Analysis — Likelihood × Impact",
        "",
        *_centered_markdown_table(["Issue", "Risk ID", "Likelihood", "Impact", "Calculation", "Risk Score"], rows),
        "" if rows else "No risks were produced.",
    ])
    print(f"Risk scores calculated deterministically for {len(rows)} risks.")


def render_prioritized() -> None:
    report = _read_json(REPORT_PATH)
    risks = sorted(_risk_rows(report), key=lambda risk: (-int(risk["risk_score"]), risk["issue_key"], risk["risk_id"]))
    rows = [
        [
            index,
            risk["issue_key"],
            risk["risk_type"],
            risk["category"],
            risk["risk_statement"],
            risk["likelihood"],
            risk["impact"],
            risk["risk_score"],
            str(risk["priority"]).upper(),
        ]
        for index, risk in enumerate(risks, start=1)
    ]
    _append_summary([
        "## Prioritized Risk Register",
        "",
        *_centered_markdown_table(
            ["#", "Issue", "Risk Type", "Category", "Risk", "Likelihood", "Impact", "Score", "Priority"],
            rows,
        ),
        "" if rows else "No risks were produced.",
        "",
        "**Human review required:** this register is a decision-support output. A person reviews the generated risks before deciding what to do next.",
        "",
        f"**LLM usage:** {report.get('total_tokens', 0):,} tokens | **Estimated cost:** ${report.get('estimated_cost_usd', 0.0):.6f}",
    ])
    print(f"Prioritized Risk Register contains {len(rows)} risks, sorted by Risk Score descending.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Jira-driven Risk Analysis Agent batch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Validate Jira ticket eligibility")
    check_parser.add_argument("issue_keys", help="One or more Jira issue keys separated by comma, space, or semicolon")
    subparsers.add_parser("analyze", help="Run Risk Analysis for eligible tickets")
    subparsers.add_parser("scores", help="Render Likelihood × Impact scoring")
    subparsers.add_parser("prioritized", help="Render prioritized risk register")

    args = parser.parse_args()
    if args.command == "check":
        check(args.issue_keys)
    elif args.command == "analyze":
        analyze()
    elif args.command == "scores":
        render_scores()
    elif args.command == "prioritized":
        render_prioritized()


if __name__ == "__main__":
    main()
