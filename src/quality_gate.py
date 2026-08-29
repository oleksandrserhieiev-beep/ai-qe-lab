import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MIN_CORRECTNESS = 95.0
MIN_GROUNDEDNESS = 95.0
MIN_RETRIEVAL_HIT = 95.0
MIN_CONSTRAINT_ADHERENCE = 95.0
MAX_HALLUCINATION = 2.0


def fail(message):
    print(f"QUALITY GATE FAIL: {message}")
    sys.exit(1)


def resolve_path(path_value):
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run AI quality gate against an evaluation report."
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to evaluated JSON report.",
    )
    return parser.parse_args()


def _check_minimum(summary, metric, threshold, label):
    value = summary.get(metric)
    if value is None:
        print(f"QUALITY GATE INFO: {label} N/A (no applicable semantic cases)")
        return
    if value < threshold:
        fail(f"{label} below threshold: {value}% < {threshold}%")


def _check_maximum(summary, metric, threshold, label):
    value = summary.get(metric)
    if value is None:
        print(f"QUALITY GATE INFO: {label} N/A (no applicable semantic cases)")
        return
    if value > threshold:
        fail(f"{label} above threshold: {value}% > {threshold}%")


def main():
    args = parse_args()
    report_file = resolve_path(args.report)

    if not report_file.exists():
        fail(f"Report file not found: {report_file}")

    with open(report_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    summary = data["summary"]
    cases = data["cases"]

    critical_failures = [
        case
        for case in cases
        if case.get("criticality") == "critical"
        and not case["evaluation"]["overall_pass"]
    ]

    if critical_failures:
        ids = [case["case_id"] for case in critical_failures]
        fail(f"Critical cases failed: {ids}")

    _check_minimum(summary, "correctness_rate", MIN_CORRECTNESS, "Correctness")
    _check_minimum(summary, "groundedness_rate", MIN_GROUNDEDNESS, "Groundedness")
    _check_minimum(summary, "retrieval_hit_rate", MIN_RETRIEVAL_HIT, "Retrieval Hit Rate")
    _check_minimum(
        summary,
        "constraint_adherence_rate",
        MIN_CONSTRAINT_ADHERENCE,
        "Constraint Adherence",
    )
    _check_maximum(summary, "hallucination_rate", MAX_HALLUCINATION, "Hallucination Rate")

    print("QUALITY GATE PASS")
    print(f"Report: {report_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()
