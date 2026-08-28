import json
import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
CURRENT_REPORT = REPORTS_DIR / "pr_evaluated.json"

MAX_HALLUCINATION = 2.0
MIN_CORRECTNESS = 95.0
MIN_GROUNDEDNESS = 95.0
MIN_RETRIEVAL_HIT = 95.0
MIN_CONSTRAINT_ADHERENCE = 95.0

MAX_ATTEMPTS = 3


def find_value(data, possible_keys):
    if isinstance(data, dict):
        for key, value in data.items():
            normalized = key.lower().replace(" ", "_")

            if normalized in possible_keys:
                return value

        for value in data.values():
            result = find_value(value, possible_keys)
            if result is not None:
                return result

    elif isinstance(data, list):
        for item in data:
            result = find_value(item, possible_keys)
            if result is not None:
                return result

    return None


def read_metrics(report_path):
    with open(report_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "hallucination": find_value(
            data,
            {
                "hallucination_rate",
                "hallucination",
            },
        ),
        "correctness": find_value(
            data,
            {
                "correctness_rate",
                "correctness",
            },
        ),
        "groundedness": find_value(
            data,
            {
                "groundedness_rate",
                "groundedness",
            },
        ),
        "retrieval_hit": find_value(
            data,
            {
                "retrieval_hit_rate",
                "retrieval_hit",
            },
        ),
        "constraint_adherence": find_value(
            data,
            {
                "constraint_adherence_rate",
                "constraint_adherence",
            },
        ),
    }


def validate_non_hallucination_metrics(metrics):
    failures = []

    if metrics["correctness"] is not None:
        if metrics["correctness"] < MIN_CORRECTNESS:
            failures.append(
                f"Correctness {metrics['correctness']}% < {MIN_CORRECTNESS}%"
            )

    if metrics["groundedness"] is not None:
        if metrics["groundedness"] < MIN_GROUNDEDNESS:
            failures.append(
                f"Groundedness {metrics['groundedness']}% < {MIN_GROUNDEDNESS}%"
            )

    if metrics["retrieval_hit"] is not None:
        if metrics["retrieval_hit"] < MIN_RETRIEVAL_HIT:
            failures.append(
                f"Retrieval Hit {metrics['retrieval_hit']}% < {MIN_RETRIEVAL_HIT}%"
            )

    if metrics["constraint_adherence"] is not None:
        if metrics["constraint_adherence"] < MIN_CONSTRAINT_ADHERENCE:
            failures.append(
                f"Constraint Adherence "
                f"{metrics['constraint_adherence']}% "
                f"< {MIN_CONSTRAINT_ADHERENCE}%"
            )

    return failures


def run_evaluation():
    subprocess.run(
        [sys.executable, str(BASE_DIR / "src" / "pr_evaluation_runner.py")],
        check=True,
    )

    subprocess.run(
        [sys.executable, str(BASE_DIR / "src" / "pr_evaluator.py")],
        check=True,
    )


def save_attempt(attempt):
    destination = REPORTS_DIR / f"pr_evaluated_attempt_{attempt}.json"
    shutil.copy2(CURRENT_REPORT, destination)
    return destination


def main():
    print("\nHallucination Retry Policy")
    print("--------------------------")

    hallucination_failures = 0
    clean_report = None

    # Attempt 1 already exists from workflow
    for attempt in range(1, MAX_ATTEMPTS + 1):

        if attempt > 1:
            print(f"\nAutomatic confirmation rerun #{attempt}")
            run_evaluation()

        attempt_report = save_attempt(attempt)
        metrics = read_metrics(attempt_report)

        print(f"\nAttempt {attempt}")
        print(f"Hallucination Rate: {metrics['hallucination']}%")

        non_hallucination_failures = (
            validate_non_hallucination_metrics(metrics)
        )

        if non_hallucination_failures:
            print("\nNON-HALLUCINATION QUALITY FAILURE")

            for failure in non_hallucination_failures:
                print(f"- {failure}")

            print("\nNo automatic retry policy applies.")
            sys.exit(1)

        hallucination_rate = metrics["hallucination"]

        if hallucination_rate is None:
            print("ERROR: Hallucination Rate not found in report.")
            sys.exit(1)

        if hallucination_rate <= MAX_HALLUCINATION:
            print("Hallucination check: PASS")
            clean_report = attempt_report

            # First run clean: no reason to execute confirmation reruns
            if attempt == 1:
                print("\nNo hallucination retry required.")
                sys.exit(0)

        else:
            print("Hallucination check: FAIL")
            hallucination_failures += 1

        # Only continue to attempts 2/3 when first attempt hallucinated
        if attempt == 1 and hallucination_rate <= MAX_HALLUCINATION:
            break

    print("\nHallucination Confirmation Summary")
    print("----------------------------------")
    print(f"Attempts: {MAX_ATTEMPTS}")
    print(
        f"Attempts exceeding threshold: "
        f"{hallucination_failures}/{MAX_ATTEMPTS}"
    )

    if hallucination_failures >= 2:
        print("\nHALLUCINATION POLICY FAIL")
        print("Hallucination reproduced in majority of confirmation runs.")
        sys.exit(1)

    if hallucination_failures == 1:
        print("\nHALLUCINATION POLICY WARNING")
        print("Hallucination occurred in 1/3 runs.")
        print("Classification: FLAKY / NON-DETERMINISTIC")

        # Restore a clean report so normal quality_gate.py
        # can evaluate the remaining metrics.
        if clean_report:
            shutil.copy2(clean_report, CURRENT_REPORT)

        sys.exit(0)

    print("\nHALLUCINATION POLICY PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()