import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from jira_requirements import load_requirement
from requirement_precheck import parse_issue_keys, precheck_requirement, validate_issue_key
from requirements_review_agent import review_requirement


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_github_summary(batch: dict):
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    totals = batch["totals"]
    lines = [
        "## Requirements Review Batch",
        "",
        f"**Run ID:** `{batch['run_id']}`  ",
        f"**Requested:** {totals['requested']}  ",
        f"**Eligible / executed:** {totals['executed']}  ",
        f"**Rejected before LLM:** {totals['rejected']}  ",
        f"**Failed during execution:** {totals['failed']}  ",
        f"**Total tokens:** {totals['total_tokens']:,}  ",
        f"**Estimated cost:** ${totals['estimated_cost_usd']:.6f}",
        "",
        "| Issue | Pre-check | Agent result | Tokens | Cost |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for item in batch["issues"]:
        precheck = item["precheck"]
        decision = item.get("decision") or item.get("error") or "-"
        tokens = item.get("total_tokens", 0)
        cost = item.get("estimated_cost_usd", 0.0)
        reason = "; ".join(item.get("rejection_reasons", []))
        precheck_text = precheck if not reason else f"{precheck}: {reason}"
        lines.append(f"| `{item['issue_key']}` | {precheck_text} | {decision} | {tokens:,} | ${cost:.6f} |")

    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def run_batch(raw_issue_keys: str) -> dict:
    issue_keys = parse_issue_keys(raw_issue_keys)
    run_id = "REQ-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    issues = []
    total_input = 0
    total_output = 0
    total_cost = 0.0
    executed = 0
    rejected = 0
    failed = 0

    for issue_key in issue_keys:
        item = {"issue_key": issue_key, "precheck": "PENDING"}
        key_reasons = validate_issue_key(issue_key)
        if key_reasons:
            item.update(precheck="REJECTED", rejection_reasons=key_reasons)
            rejected += 1
            issues.append(item)
            continue

        try:
            requirement = load_requirement(issue_key)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            message = "issue not found or inaccessible" if status_code == 404 else f"Jira returned HTTP {status_code}"
            item.update(precheck="REJECTED", rejection_reasons=[message])
            rejected += 1
            issues.append(item)
            continue
        except Exception as exc:  # configuration/network errors are visible but do not call the LLM
            item.update(precheck="REJECTED", rejection_reasons=[f"Jira load failed: {exc}"])
            rejected += 1
            issues.append(item)
            continue

        reasons = precheck_requirement(requirement)
        if reasons:
            item.update(precheck="REJECTED", rejection_reasons=reasons, requirement=requirement)
            rejected += 1
            issues.append(item)
            continue

        item["precheck"] = "ELIGIBLE"
        try:
            review, telemetry = review_requirement(requirement)
            executed += 1
            total_input += telemetry["input_tokens"]
            total_output += telemetry["output_tokens"]
            total_cost += float(telemetry.get("estimated_cost_usd") or 0.0)
            item.update(
                decision=review["decision"],
                readiness_score=review["readiness_score"],
                total_tokens=telemetry["total_tokens"],
                estimated_cost_usd=float(telemetry.get("estimated_cost_usd") or 0.0),
                report=f"reports/requirements_review_{issue_key}.json",
            )
            _write_json(
                Path(item["report"]),
                {
                    "run_timestamp": datetime.now(timezone.utc).isoformat(),
                    "batch_run_id": run_id,
                    "issue_key": issue_key,
                    "requirement": requirement,
                    "review": review,
                    "telemetry": telemetry,
                },
            )
        except Exception as exc:
            failed += 1
            item.update(error=f"agent execution failed: {exc}")
        issues.append(item)

    batch = {
        "run_id": run_id,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
        "totals": {
            "requested": len(issue_keys),
            "executed": executed,
            "rejected": rejected,
            "failed": failed,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "estimated_cost_usd": round(total_cost, 6),
        },
    }
    _write_json(Path("reports") / f"requirements_review_batch_{run_id}.json", batch)
    _append_github_summary(batch)
    return batch


def main():
    parser = argparse.ArgumentParser(description="Run Requirements Review Agent for a manual batch of Jira issues")
    parser.add_argument("issue_keys", help="Comma/space/semicolon-separated Jira issue keys")
    args = parser.parse_args()

    batch = run_batch(args.issue_keys)
    totals = batch["totals"]
    print(f"Run ID: {batch['run_id']}")
    print(f"Requested: {totals['requested']}")
    print(f"Executed: {totals['executed']}")
    print(f"Rejected before LLM: {totals['rejected']}")
    print(f"Failed during execution: {totals['failed']}")
    print(f"Usage: {totals['input_tokens']} input + {totals['output_tokens']} output = {totals['total_tokens']} tokens")
    print(f"Estimated batch cost: ${totals['estimated_cost_usd']:.6f}")
    for item in batch["issues"]:
        if item["precheck"] == "REJECTED":
            print(f"{item['issue_key']}: REJECTED - {'; '.join(item['rejection_reasons'])}")
        elif item.get("error"):
            print(f"{item['issue_key']}: ERROR - {item['error']}")
        else:
            print(f"{item['issue_key']}: {item['decision']} ({item['readiness_score']}/100)")


if __name__ == "__main__":
    main()
