import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def main():
    parser = argparse.ArgumentParser(description="Fail when a critical adversarial case succeeds against the system.")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    report = json.loads(resolve_path(args.report).read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    critical_failures = summary.get("critical_failures", [])
    if critical_failures:
        print(f"ADVERSARIAL GATE FAIL: critical adversarial failures: {critical_failures}")
        print(f"Attack Success Rate: {summary.get('attack_success_rate')}%")
        return 1

    print("ADVERSARIAL GATE PASS")
    print(f"Adversarial Pass Rate: {summary.get('adversarial_pass_rate')}%")
    print(f"Attack Success Rate: {summary.get('attack_success_rate')}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
