import argparse
import json
from pathlib import Path

from risk_analysis_jira_writeback import append_approved_risks

REPORT_PATH = Path("reports/risk_analysis_batch.json")


def approved_risks(issue_key: str) -> list[dict]:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    for item in report.get("results", []):
        if item.get("issue_key") == issue_key and item.get("status") in {"ANALYZED", "CACHED"}:
            return item.get("result", {}).get("risks", [])
    raise ValueError(f"No analyzed Risk Register found for {issue_key}")


def main():
    parser = argparse.ArgumentParser(description="Apply a human-approved Risk Register to Jira")
    parser.add_argument("issue_key")
    parser.add_argument("--approve", action="store_true", help="Required explicit human approval gate")
    args = parser.parse_args()
    if not args.approve:
        raise SystemExit("Jira was NOT updated: explicit --approve is required")
    result = append_approved_risks(args.issue_key, approved_risks(args.issue_key), approved=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
