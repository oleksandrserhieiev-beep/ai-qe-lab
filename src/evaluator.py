import argparse
import json
from pathlib import Path

from llm_evaluator import evaluate_ai_response
from retrieval_metrics import evaluate_constraint_retrieval
from risk_reporting import build_risk_summary, print_risk_summary


BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate AI/RAG execution results."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to execution results JSON file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to evaluated results JSON file.",
    )
    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def evaluate_retrieval(case):
    expected_product = case.get("expected_retrieved_product")
    expected_source = case.get("expected_source")
    retrieval = case.get("retrieval", [])
    retrieved_ids = [item["id"] for item in retrieval]

    if expected_product:
        return expected_product in retrieved_ids

    if expected_source and expected_source.lower() != "none":
        if expected_source.lower() == "products.json":
            return any(
                item.get("type") == "product"
                for item in retrieval
            )
        return expected_source in retrieved_ids

    return True


def evaluate_case(case):
    retrieval_pass = evaluate_retrieval(case)
    query = case.get("query", "")

    constraint_retrieval = evaluate_constraint_retrieval(
        query=query,
        retrieval=case.get("retrieval", []),
    )

    expected_behavior = case.get("expected_facts_behavior", "")
    actual_answer = case.get("actual_answer", "")
    final_context = case.get("final_context", "")

    ai_evaluation = evaluate_ai_response(
        query=query,
        expected_behavior=expected_behavior,
        actual_answer=actual_answer,
        retrieved_context=final_context,
    )

    correctness = bool(ai_evaluation.get("correctness", False))
    groundedness = bool(ai_evaluation.get("groundedness", False))
    hallucination = bool(ai_evaluation.get("hallucination", False))
    constraint_adherence = bool(
        ai_evaluation.get("constraint_adherence", False)
    )
    context_coverage = int(
        ai_evaluation.get("context_coverage", 0)
    )
    context_sufficient = bool(
        ai_evaluation.get("context_sufficient", False)
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
            "constraint_retrieval": constraint_retrieval,
            "context_coverage": context_coverage,
            "context_sufficient": context_sufficient,
            "correctness": correctness,
            "groundedness": groundedness,
            "hallucination": hallucination,
            "constraint_adherence": constraint_adherence,
            "overall_pass": overall_pass,
            "reason": ai_evaluation.get("reason", ""),
        },
    }


def percentage(value, total):
    if total == 0:
        return 0.0
    return round(value / total * 100, 2)


def average(values):
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def percentile(values, percentile_value):
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = (percentile_value / 100) * (len(sorted_values) - 1)
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = index - lower_index
    result = (
        sorted_values[lower_index]
        + (sorted_values[upper_index] - sorted_values[lower_index])
        * fraction
    )
    return round(result, 2)


def run_evaluator(results_file, evaluated_file):
    with open(results_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    evaluated_cases = []

    for number, case in enumerate(results, start=1):
        case_id = case.get("case_id", "UNKNOWN")
        print(f"[{number}/{len(results)}] Evaluating {case_id}")
        evaluated_cases.append(evaluate_case(case))

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

    context_coverage_scores = [
        case["evaluation"]["context_coverage"]
        for case in evaluated_cases
    ]
    context_sufficient_cases = sum(
        case["evaluation"]["context_sufficient"]
        for case in evaluated_cases
    )

    constraint_metric_cases = [
        case["evaluation"]["constraint_retrieval"]
        for case in evaluated_cases
        if case["evaluation"]["constraint_retrieval"]["applicable"]
    ]
    constraint_match_scores = [
        metric["constraint_match_score"]
        for metric in constraint_metric_cases
        if metric["constraint_match_score"] is not None
    ]
    constraint_precision_scores = [
        metric["constraint_precision_at_k"]
        for metric in constraint_metric_cases
        if metric["constraint_precision_at_k"] is not None
    ]

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
    p95_latency = percentile(latencies, 95)
    average_input_tokens = (
        round(total_input_tokens / len(input_tokens), 2)
        if input_tokens
        else 0.0
    )
    average_output_tokens = (
        round(total_output_tokens / len(output_tokens), 2)
        if output_tokens
        else 0.0
    )

    risk_report = build_risk_summary(evaluated_cases)

    summary = {
        "total_cases": total,
        "passed": overall_passed,
        "failed": total - overall_passed,
        "overall_pass_rate": percentage(overall_passed, total),
        "retrieval_hit_rate": percentage(retrieval_passed, total),
        "average_constraint_match_score": average(
            constraint_match_scores
        ),
        "average_constraint_precision_at_k": average(
            constraint_precision_scores
        ),
        "constraint_metric_cases": len(constraint_metric_cases),
        "average_context_coverage": average(
            context_coverage_scores
        ),
        "context_sufficiency_rate": percentage(
            context_sufficient_cases,
            total,
        ),
        "correctness_rate": percentage(correctness_passed, total),
        "groundedness_rate": percentage(groundedness_passed, total),
        "constraint_adherence_rate": percentage(
            constraint_passed,
            total,
        ),
        "hallucination_rate": percentage(hallucinations, total),
        "risk_count": risk_report["risk_count"],
        "unclassified_risk_cases": risk_report["unclassified_count"],
        "risk_summary": risk_report["risk_summary"],
        "operational_metrics": {
            "average_latency_ms": average_latency,
            "p95_latency_ms": p95_latency,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "average_input_tokens_per_case": average_input_tokens,
            "average_output_tokens_per_case": average_output_tokens,
        },
    }

    output = {
        "summary": summary,
        "risk_report": risk_report,
        "cases": evaluated_cases,
    }

    evaluated_file.parent.mkdir(parents=True, exist_ok=True)

    with open(evaluated_file, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("\nAI Evaluation Summary")
    print("---------------------")
    print(f"Total cases: {total}")
    print(f"Passed: {overall_passed}")
    print(f"Failed: {total - overall_passed}")
    print(f"Overall Pass Rate: {summary['overall_pass_rate']}%")
    print(f"Retrieval Hit Rate: {summary['retrieval_hit_rate']}%")
    print(
        f"Average Constraint Match: "
        f"{summary['average_constraint_match_score']}%"
    )
    print(
        f"Average Constraint Precision@K: "
        f"{summary['average_constraint_precision_at_k']}%"
    )
    print(
        f"Average Context Coverage: "
        f"{summary['average_context_coverage']}%"
    )
    print(
        f"Context Sufficiency Rate: "
        f"{summary['context_sufficiency_rate']}%"
    )
    print(f"Correctness Rate: {summary['correctness_rate']}%")
    print(f"Groundedness Rate: {summary['groundedness_rate']}%")
    print(
        f"Constraint Adherence Rate: "
        f"{summary['constraint_adherence_rate']}%"
    )
    print(f"Hallucination Rate: {summary['hallucination_rate']}%")

    print_risk_summary(risk_report)

    print("\nOperational Metrics")
    print("-------------------")
    print(f"Average latency: {average_latency} ms")
    print(f"P95 latency: {p95_latency} ms")
    print(f"Total input tokens: {total_input_tokens}")
    print(f"Total output tokens: {total_output_tokens}")
    print(f"\nSaved to: {evaluated_file}")


if __name__ == "__main__":
    args = parse_args()
    results_file = resolve_path(args.input)
    evaluated_file = resolve_path(args.output)
    run_evaluator(
        results_file=results_file,
        evaluated_file=evaluated_file,
    )
