import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Fail when a critical metamorphic relation fails.")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    path = Path(args.report)
    if not path.is_absolute():
        path = BASE_DIR / path
    with path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)
    failures = [case["case_id"] for case in report.get("cases", []) if case.get("criticality") == "critical" and not case.get("overall_pass")]
    if failures:
        print(f"METAMORPHIC GATE FAIL: critical relations failed: {failures}")
        return 1
    print("METAMORPHIC GATE PASS")
    print(f"Pass rate: {report.get('summary', {}).get('pass_rate')}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
