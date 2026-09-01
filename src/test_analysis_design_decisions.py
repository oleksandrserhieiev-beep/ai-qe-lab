import argparse
import json
from pathlib import Path


ALLOWED_DECISIONS = {"APPROVE", "REJECT", "EDIT", "EXTEND_EXISTING"}
DEFAULT_REPORT = Path("reports/test_analysis_design_batch.json")
DEFAULT_DECISIONS = Path("reports/test_analysis_design_decisions.json")


def build_decision_package(report: dict) -> dict:
    rows = []
    for item in report.get("results", []):
        if item.get("status") == "ERROR":
            continue
        issue_key = item["issue_key"]
        for proposal in item.get("result", {}).get("proposals", []):
            if proposal.get("test_kind") != "ai":
                continue
            rows.append({
                "issue_key": issue_key,
                "proposed_id": proposal["proposed_id"],
                "title": proposal["title"],
                "agent_action": proposal["action"],
                "target_suite": proposal["target_suite"],
                "oracle_type": proposal["oracle_type"],
                "existing_case_id": proposal.get("existing_case_id"),
                "proposal": proposal,
                "decision": "PENDING",
                "edited_proposal": None,
                "confirmed": False,
            })
    return {
        "source_run_timestamp": report.get("run_timestamp"),
        "decision_contract": sorted(ALLOWED_DECISIONS),
        "proposals": rows,
    }


def apply_decision(package: dict, *, issue_key: str, proposed_id: str, decision: str, confirmed: bool, edited_proposal: dict | None = None) -> dict:
    decision = decision.strip().upper()
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision: {decision}")
    if not confirmed:
        raise ValueError("Human confirmation is required before a decision can be applied")
    match = None
    for row in package.get("proposals", []):
        if row.get("issue_key") == issue_key and row.get("proposed_id") == proposed_id:
            match = row
            break
    if match is None:
        raise ValueError(f"Proposal {issue_key}/{proposed_id} was not found")
    if decision == "EDIT" and not edited_proposal:
        raise ValueError("EDIT requires edited_proposal JSON")
    if decision == "EXTEND_EXISTING" and not (match.get("existing_case_id") or (edited_proposal or {}).get("existing_case_id")):
        raise ValueError("EXTEND_EXISTING requires an existing_case_id")
    match["decision"] = decision
    match["edited_proposal"] = edited_proposal
    match["confirmed"] = True
    return match


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--report", default=str(DEFAULT_REPORT))
    build.add_argument("--output", default=str(DEFAULT_DECISIONS))

    decide = sub.add_parser("decide")
    decide.add_argument("--package", default=str(DEFAULT_DECISIONS))
    decide.add_argument("--issue-key", required=True)
    decide.add_argument("--proposal-id", required=True)
    decide.add_argument("--decision", required=True, choices=sorted(ALLOWED_DECISIONS))
    decide.add_argument("--confirm", action="store_true")
    decide.add_argument("--edited-json", default="")
    decide.add_argument("--output", default="reports/test_analysis_design_decision.json")

    args = parser.parse_args()
    if args.command == "build":
        result = build_decision_package(_read(Path(args.report)))
        _write(Path(args.output), result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    package = _read(Path(args.package))
    edited = json.loads(args.edited_json) if args.edited_json.strip() else None
    result = apply_decision(
        package,
        issue_key=args.issue_key,
        proposed_id=args.proposal_id,
        decision=args.decision,
        confirmed=args.confirm,
        edited_proposal=edited,
    )
    _write(Path(args.output), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
