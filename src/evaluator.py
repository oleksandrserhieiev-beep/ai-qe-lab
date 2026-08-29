import argparse
import json
from pathlib import Path

from cost_reporting import summarize_usage, print_usage_summary
from judge_routing import build_evaluation_plan, deterministic_evaluation
from llm_evaluator import evaluate_ai_response
from retrieval_metrics import evaluate_constraint_retrieval
from risk_reporting import build_risk_summary, print_risk_summary


BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate AI/RAG execution results.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


def evaluate_retrieval(case):
    expected_product = case.get("expected_retrieved_product")
    expected_source = case.get("expected_source")
    retrieval = case.get("retrieval", [])
    retrieved_ids = [item["id"] for item in retrieval]
    if expected_product:
        return expected_product in retrieved_ids
    if expected_source and expected_source.lower() != "none":
        if expected_source.lower() == "products.json":
            return any(item.get("type") == "product" for item in retrieval)
        return expected_source in retrieved_ids
    return True


def evaluate_case(case):
    query = case.get("query", "")
    retrieval_pass = evaluate_retrieval(case)
    constraint_retrieval = evaluate_constraint_retrieval(
        query=query,
        retrieval=case.get("retrieval", []),
    )
    plan = build_evaluation_plan(
        case=case,
        retrieval_pass=retrieval_pass,
        constraint_retrieval=constraint_retrieval,
    )

    if plan["route"] == "deterministic_only":
        deterministic = deterministic_evaluation(
            retrieval_pass=retrieval_pass,
            constraint_retrieval=constraint_retrieval,
            plan=plan,
        )
        return {
            **case,
            "evaluation": {
                "retrieval_pass": retrieval_pass,
                "constraint_retrieval": constraint_retrieval,
                "deterministic_assertions": {
                    "factual": plan.get("factual_assertion"),
                    "product": plan.get("product_assertion"),
                    "signals": plan.get("deterministic_signals", []),
                },
                "context_coverage": None,
                "context_sufficient": None,
                "correctness": None,
                "groundedness": None,
                "hallucination": None,
                "constraint_adherence": deterministic["constraint_adherence"],
                "overall_pass": deterministic["overall_pass"],
                "reason": plan["reason"],
                "judge_route": plan["route"],
                "judge_telemetry": {},
            },
        }

    ai_evaluation = evaluate_ai_response(
        query=query,
        expected_behavior=case.get("expected_facts_behavior", ""),
        actual_answer=case.get("actual_answer", ""),
        retrieved_context=case.get("retrieved_context") or case.get("final_context", ""),
        risk=case.get("risk"),
    )

    correctness = bool(ai_evaluation.get("correctness", False))
    groundedness = bool(ai_evaluation.get("groundedness", False))
    hallucination = bool(ai_evaluation.get("hallucination", False))
    constraint_adherence = bool(ai_evaluation.get("constraint_adherence", False))
    context_coverage = int(ai_evaluation.get("context_coverage", 0))
    context_sufficient = bool(ai_evaluation.get("context_sufficient", False))
    overall_pass = retrieval_pass and correctness and groundedness and not hallucination and constraint_adherence

    return {
        **case,
        "evaluation": {
            "retrieval_pass": retrieval_pass,
            "constraint_retrieval": constraint_retrieval,
            "deterministic_assertions": {
                "factual": plan.get("factual_assertion"),
                "product": plan.get("product_assertion"),
            },
            "context_coverage": context_coverage,
            "context_sufficient": context_sufficient,
            "correctness": correctness,
            "groundedness": groundedness,
            "hallucination": hallucination,
            "constraint_adherence": constraint_adherence,
            "overall_pass": overall_pass,
            "reason": ai_evaluation.get("reason"),
            "judge_route": plan["route"],
            "judge_telemetry": ai_evaluation.get("_telemetry", {}),
        },
    }


def percentage(value, total):
    return round(value / total * 100, 2) if total else 0.0


def average(values):
    return round(sum(values) / len(values), 2) if values else 0.0


def semantic_rate(cases, metric, positive=True):
    measured = [
        c["evaluation"][metric]
        for c in cases
        if c["evaluation"].get(metric) is not None
    ]
    if not measured:
        return 100.0, 0
    passed = sum(bool(value) == positive for value in measured)
    return percentage(passed, len(measured)), len(measured)


def percentile(values, percentile_value):
    if not values:
        return 0.0
    values = sorted(values)
    index = (percentile_value / 100) * (len(values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return round(values[lower] + (values[upper] - values[lower]) * fraction, 2)


def run_evaluator(results_file, evaluated_file):
    with open(results_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    evaluated_cases = []
    for number, case in enumerate(results, start=1):
        print(f"[{number}/{len(results)}] Evaluating {case.get('case_id', 'UNKNOWN')}")
        evaluated_cases.append(evaluate_case(case))

    total = len(evaluated_cases)
    overall_passed = sum(c["evaluation"]["overall_pass"] for c in evaluated_cases)
    retrieval_passed = sum(c["evaluation"]["retrieval_pass"] for c in evaluated_cases)
    constraint_passed = sum(c["evaluation"]["constraint_adherence"] for c in evaluated_cases)

    correctness_rate, correctness_cases = semantic_rate(evaluated_cases, "correctness")
    groundedness_rate, groundedness_cases = semantic_rate(evaluated_cases, "groundedness")
    hallucination_pass_rate, hallucination_cases = semantic_rate(
        evaluated_cases, "hallucination", positive=False
    )
    hallucination_rate = round(100.0 - hallucination_pass_rate, 2)
    context_sufficiency_rate, context_sufficiency_cases = semantic_rate(
        evaluated_cases, "context_sufficient"
    )
    context_coverage_scores = [
        c["evaluation"]["context_coverage"]
        for c in evaluated_cases
        if c["evaluation"].get("context_coverage") is not None
    ]

    constraint_metric_cases = [
        c["evaluation"]["constraint_retrieval"]
        for c in evaluated_cases
        if c["evaluation"]["constraint_retrieval"]["applicable"]
    ]
    constraint_match_scores = [
        m["constraint_match_score"]
        for m in constraint_metric_cases
        if m["constraint_match_score"] is not None
    ]
    constraint_precision_scores = [
        m["constraint_precision_at_k"]
        for m in constraint_metric_cases
        if m["constraint_precision_at_k"] is not None
    ]

    semantic_judge_cases = sum(
        c["evaluation"].get("judge_route") == "semantic_judge"
        for c in evaluated_cases
    )
    deterministic_only_cases = total - semantic_judge_cases

    latencies = [
        float(c.get("telemetry", {}).get("latency_ms"))
        for c in evaluated_cases
        if c.get("telemetry", {}).get("latency_ms") is not None
    ]
    risk_report = build_risk_summary(evaluated_cases)
    usage = summarize_usage(evaluated_cases)

    summary = {
        "total_cases": total,
        "passed": overall_passed,
        "failed": total - overall_passed,
        "overall_pass_rate": percentage(overall_passed, total),
        "retrieval_hit_rate": percentage(retrieval_passed, total),
        "average_constraint_match_score": average(constraint_match_scores),
        "average_constraint_precision_at_k": average(constraint_precision_scores),
        "constraint_metric_cases": len(constraint_metric_cases),
        "average_context_coverage": average(context_coverage_scores) if context_coverage_scores else 100.0,
        "context_sufficiency_rate": context_sufficiency_rate,
        "correctness_rate": correctness_rate,
        "groundedness_rate": groundedness_rate,
        "constraint_adherence_rate": percentage(constraint_passed, total),
        "hallucination_rate": hallucination_rate,
        "semantic_metric_case_counts": {
            "correctness": correctness_cases,
            "groundedness": groundedness_cases,
            "hallucination": hallucination_cases,
            "context_sufficiency": context_sufficiency_cases,
        },
        "judge_routing": {
            "semantic_judge_cases": semantic_judge_cases,
            "deterministic_only_cases": deterministic_only_cases,
            "judge_call_reduction_percent": percentage(deterministic_only_cases, total),
        },
        "risk_count": risk_report["risk_count"],
        "unclassified_risk_cases": risk_report["unclassified_count"],
        "risk_summary": risk_report["risk_summary"],
        "operational_metrics": {
            "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "p95_latency_ms": percentile(latencies, 95),
            "token_cost": usage,
        },
    }

    output = {"summary": summary, "risk_report": risk_report, "cases": evaluated_cases}
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
    print(f"Average Constraint Match: {summary['average_constraint_match_score']}%")
    print(f"Average Constraint Precision@K: {summary['average_constraint_precision_at_k']}%")
    print(f"Average Context Coverage: {summary['average_context_coverage']}%")
    print(f"Context Sufficiency Rate: {summary['context_sufficiency_rate']}%")
    print(f"Correctness Rate: {summary['correctness_rate']}% ({correctness_cases} judged)")
    print(f"Groundedness Rate: {summary['groundedness_rate']}% ({groundedness_cases} judged)")
    print(f"Constraint Adherence Rate: {summary['constraint_adherence_rate']}%")
    print(f"Hallucination Rate: {summary['hallucination_rate']}% ({hallucination_cases} judged)")
    print("\nJudge Routing")
    print("-------------")
    print(f"Semantic Judge cases: {semantic_judge_cases}/{total}")
    print(f"Deterministic-only cases: {deterministic_only_cases}/{total}")
    print(f"Judge call reduction: {summary['judge_routing']['judge_call_reduction_percent']}%")
    print_risk_summary(risk_report)
    print_usage_summary(usage)
    print(f"\nSaved to: {evaluated_file}")


if __name__ == "__main__":
    args = parse_args()
    run_evaluator(resolve_path(args.input), resolve_path(args.output))
