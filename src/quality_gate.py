import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

REPORT_FILE = BASE_DIR / "reports" / "golden_evaluated.json"

MIN_CORRECTNESS = 95.0
MIN_GROUNDEDNESS = 95.0
MIN_RETRIEVAL_HIT = 95.0
MIN_CONSTRAINT_ADHERENCE = 95.0
MAX_HALLUCINATION = 2.0


def fail(message):
    print(f"QUALITY GATE FAIL: {message}")
    sys.exit(1)


def main():
    with open(REPORT_FILE, "r", encoding="utf-8") as file:
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
        fail("Correctness below threshold")

    if summary["groundedness_rate"] < MIN_GROUNDEDNESS:
        fail("Groundedness below threshold")

    if summary["retrieval_hit_rate"] < MIN_RETRIEVAL_HIT:
        fail("Retrieval Hit Rate below threshold")

    if (
        summary["constraint_adherence_rate"]
        < MIN_CONSTRAINT_ADHERENCE
    ):
        fail("Constraint Adherence below threshold")

    if summary["hallucination_rate"] > MAX_HALLUCINATION:
        fail("Hallucination Rate above threshold")

    print("QUALITY GATE PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()