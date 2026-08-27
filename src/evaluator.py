import json
from pathlib import Path

from llm_evaluator import evaluate_ai_response


BASE_DIR = Path(__file__).resolve().parent.parent

RESULTS_FILE = BASE_DIR / "reports" / "golden_results.json"
EVALUATED_FILE = BASE_DIR / "reports" / "golden_evaluated.json"


def evaluate_retrieval(case):
    expected_product = case.get("expected_retrieved_product")
    expected_source = case.get("expected_source")

    retrieved_ids = [
        item["id"]
        for item in case.get("retrieval", [])
    ]

    if expected_product:
        return expected_product in retrieved_ids

    if expected_source and expected_source.lower() != "none":
        return expected_source in retrieved_ids

    return True


def evaluate_case(case):
    retrieval_pass = evaluate_retrieval(case)

    query = case.get("query", "")
    expected_behavior = case.get(
        "expected_facts_behavior",
        "",
    )
    actual_answer = case.get(
        "actual_answer",
        "",
    )
    final_context = case.get(
        "final_context",
        "",
    )

    ai_evaluation = evaluate_ai_response(
        query=query,
        expected_behavior=expected_behavior,
        actual_answer=actual_answer,
        retrieved_context=final_context,
    )

    correctness = bool(
        ai_evaluation.get("correctness", False)
    )

    groundedness = bool(
        ai_evaluation.get("groundedness", False)
    )

    hallucination = bool(
        ai_evaluation.get("hallucination", False)
    )

    constraint_adherence = bool(
        ai_evaluation.get(
            "constraint_adherence",
            False,
        )
    )

    overall_pass = (
        retrieval_pass
        and correctness
        and groundedness
        and not hallucination
        and constraint_adherence
    )

    return {
        **case,
        "evaluation": {
            "retrieval_pass": retrieval_pass,
            "correctness": correctness,
            "groundedness": groundedness,
            "hallucination": hallucination,
            "constraint_adherence": constraint_adherence,
            "overall_pass": overall_pass,
            "reason": ai_evaluation.get(
                "reason",
                "",
            ),
        },
    }


def percentage(value, total):
    if total == 0:
        return 0.0

    return round(
        value / total * 100,
        2,
    )


def percentile(values, percentile_value):
    if not values:
        return 0.0

    sorted_values = sorted(values)

    index = (
        percentile_value / 100
    ) * (len(sorted_values) - 1)

    lower_index = int(index)
    upper_index = min(
        lower_index + 1,
        len(sorted_values) - 1,
    )

    fraction = index - lower_index

    result = (
        sorted_values[lower_index]
        + (
            sorted_values[upper_index]
            - sorted_values[lower_index]
        )
        * fraction
    )

    return round(result, 2)


def run_evaluator():
    with open(
        RESULTS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        results = json.load(file)

    evaluated_cases = []

    for number, case in enumerate(
        results,
        start=1,
    ):
        case_id = case.get(
            "case_id",
            "UNKNOWN",
        )

        print(
            f"[{number}/{len(results)}] "
            f"Evaluating {case_id}"
        )

        evaluated_case = evaluate_case(case)

        evaluated_cases.append(
            evaluated_case
        )

    total = len(evaluated_cases)

    overall_passed = sum(
        case["evaluation"]["overall_pass"]
        for case in evaluated_cases
    )

    retrieval_passed = sum(
        case["evaluation"]["retrieval_pass"]
        for case in evaluated_cases
    )

    correctness_passed = sum(
        case["evaluation"]["correctness"]
        for case in evaluated_cases
    )

    groundedness_passed = sum(
        case["evaluation"]["groundedness"]
        for case in evaluated_cases
    )

    constraint_passed = sum(
        case["evaluation"]["constraint_adherence"]
        for case in evaluated_cases
    )

    hallucinations = sum(
        case["evaluation"]["hallucination"]
        for case in evaluated_cases
    )

    # Operational metrics
    latencies = []
    input_tokens = []
    output_tokens = []

    for case in evaluated_cases:
        telemetry = case.get("telemetry", {})

        latency = telemetry.get("latency_ms")
        input_token_count = telemetry.get("input_tokens")
        output_token_count = telemetry.get("output_tokens")

        if latency is not None:
            latencies.append(float(latency))

        if input_token_count is not None:
            input_tokens.append(int(input_token_count))

        if output_token_count is not None:
            output_tokens.append(int(output_token_count))

    total_input_tokens = sum(input_tokens)
    total_output_tokens = sum(output_tokens)

    average_latency = (
        round(sum(latencies) / len(latencies), 2)
        if latencies
        else 0.0
    )

    p95_latency = percentile(
        latencies,
        95,
    )

    average_input_tokens = (
        round(
            total_input_tokens / len(input_tokens),
            2,
        )
        if input_tokens
        else 0.0
    )

    average_output_tokens = (
        round(
            total_output_tokens / len(output_tokens),
            2,
        )
        if output_tokens
        else 0.0
    )

    summary = {
        "total_cases": total,

        "passed": overall_passed,
        "failed": total - overall_passed,

        "overall_pass_rate": percentage(
            overall_passed,
            total,
        ),

        "retrieval_hit_rate": percentage(
            retrieval_passed,
            total,
        ),

        "correctness_rate": percentage(
            correctness_passed,
            total,
        ),

        "groundedness_rate": percentage(
            groundedness_passed,
            total,
        ),

        "constraint_adherence_rate": percentage(
            constraint_passed,
            total,
        ),

        "hallucination_rate": percentage(
            hallucinations,
            total,
        ),

        "operational_metrics": {
            "average_latency_ms": average_latency,
            "p95_latency_ms": p95_latency,

            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,

            "average_input_tokens_per_case":
                average_input_tokens,

            "average_output_tokens_per_case":
                average_output_tokens,
        },
    }

    output = {
        "summary": summary,
        "cases": evaluated_cases,
    }

    with open(
        EVALUATED_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\nAI Evaluation Summary")
    print("---------------------")

    print(
        f"Total cases: "
        f"{summary['total_cases']}"
    )

    print(
        f"Passed: "
        f"{summary['passed']}"
    )

    print(
        f"Failed: "
        f"{summary['failed']}"
    )

    print(
        f"Overall Pass Rate: "
        f"{summary['overall_pass_rate']}%"
    )

    print(
        f"Retrieval Hit Rate: "
        f"{summary['retrieval_hit_rate']}%"
    )

    print(
        f"Correctness Rate: "
        f"{summary['correctness_rate']}%"
    )

    print(
        f"Groundedness Rate: "
        f"{summary['groundedness_rate']}%"
    )

    print(
        f"Constraint Adherence Rate: "
        f"{summary['constraint_adherence_rate']}%"
    )

    print(
        f"Hallucination Rate: "
        f"{summary['hallucination_rate']}%"
    )

    print("\nOperational Metrics")
    print("-------------------")

    print(
        f"Average latency: "
        f"{average_latency} ms"
    )

    print(
        f"P95 latency: "
        f"{p95_latency} ms"
    )

    print(
        f"Total input tokens: "
        f"{total_input_tokens}"
    )

    print(
        f"Total output tokens: "
        f"{total_output_tokens}"
    )

    print(
        f"Average input tokens/case: "
        f"{average_input_tokens}"
    )

    print(
        f"Average output tokens/case: "
        f"{average_output_tokens}"
    )

    print(
        f"\nSaved to: "
        f"{EVALUATED_FILE}"
    )


if __name__ == "__main__":
    run_evaluator()