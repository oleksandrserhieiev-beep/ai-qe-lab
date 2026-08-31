import argparse
import json
from pathlib import Path

from risk_analysis_agent import build_risk_analysis_input


HANDOFF_VERSION = "v1"
READY_FOR_RISK_ANALYSIS = "READY_FOR_RISK_ANALYSIS"
BLOCKED = "BLOCKED"


def build_handoff_from_review_report(report: dict) -> dict:
    """Convert a Requirements Review report into an explicit Risk Analysis handoff state.

    READY reviews produce a validated, minimal RiskAnalysisInput payload. Any other
    review decision is represented as a blocked handoff and must not start Risk Analysis.
    """
    issue_key = report.get("issue_key") or ""
    review = report.get("review") or {}
    requirement = report.get("review_payload") or {}
    decision = review.get("decision")

    base = {
        "handoff_version": HANDOFF_VERSION,
        "issue_key": issue_key,
        "requirements_review_decision": decision,
        "requirements_review_content_hash": report.get("content_hash"),
        "requirements_review_run_id": report.get("batch_run_id"),
        "requirements_review_timestamp": report.get("run_timestamp"),
    }

    if decision != "READY":
        return {
            **base,
            "handoff_status": BLOCKED,
            "next_stage": None,
            "reason": "Risk Analysis is allowed only when Requirements Review = READY",
            "risk_analysis_input": None,
        }

    risk_input = build_risk_analysis_input(requirement, review)
    return {
        **base,
        "handoff_status": READY_FOR_RISK_ANALYSIS,
        "next_stage": "risk_analysis",
        "reason": "Requirements Review passed the READY gate",
        "risk_analysis_input": risk_input,
    }


def write_handoffs(reports_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    blocked = []

    for report_path in sorted(reports_dir.glob("requirements_review_*.json")):
        if report_path.name.startswith("requirements_review_batch_"):
            continue

        report = json.loads(report_path.read_text(encoding="utf-8"))
        handoff = build_handoff_from_review_report(report)
        issue_key = handoff["issue_key"] or report_path.stem
        output_path = output_dir / f"risk_analysis_handoff_{issue_key}.json"
        output_path.write_text(
            json.dumps(handoff, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        target = generated if handoff["handoff_status"] == READY_FOR_RISK_ANALYSIS else blocked
        target.append({"issue_key": issue_key, "artifact": str(output_path)})

    summary = {
        "handoff_version": HANDOFF_VERSION,
        "ready_for_risk_analysis": len(generated),
        "blocked": len(blocked),
        "ready_items": generated,
        "blocked_items": blocked,
    }
    (output_dir / "requirements_review_handoff_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Build deterministic Requirements Review -> Risk Analysis handoff artifacts"
    )
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--output-dir", default="reports/handoffs")
    args = parser.parse_args()
    write_handoffs(Path(args.reports_dir), Path(args.output_dir))


if __name__ == "__main__":
    main()
