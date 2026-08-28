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

    if path.is_absolute():
        return path

    return BASE_DIR / path


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
        ids = [
            case["case_id"]
            for case in critical_failures
        ]
        fail(f"Critical cases failed: {ids}")

    if summary["correctness_rate"] < MIN_CORRECTNESS:
        fail(
            f"Correctness below threshold: "
            f"{summary['correctness_rate']}% < {MIN_CORRECTNESS}%"
        )

    if summary["groundedness_rate"] < MIN_GROUNDEDNESS:
        fail(
            f"Groundedness below threshold: "
            f"{summary['groundedness_rate']}% < {MIN_GROUNDEDNESS}%"
        )

    if summary["retrieval_hit_rate"] < MIN_RETRIEVAL_HIT:
        fail(
            f"Retrieval Hit Rate below threshold: "
            f"{summary['retrieval_hit_rate']}% < {MIN_RETRIEVAL_HIT}%"
        )

    if (
        summary["constraint_adherence_rate"]
        < MIN_CONSTRAINT_ADHERENCE
    ):
        fail(
            f"Constraint Adherence below threshold: "
            f"{summary['constraint_adherence_rate']}% "
            f"< {MIN_CONSTRAINT_ADHERENCE}%"
        )

    if summary["hallucination_rate"] > MAX_HALLUCINATION:
        fail(
            f"Hallucination Rate above threshold: "
            f"{summary['hallucination_rate']}% > {MAX_HALLUCINATION}%"
        )

    print("QUALITY GATE PASS")
    print(f"Report: {report_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()