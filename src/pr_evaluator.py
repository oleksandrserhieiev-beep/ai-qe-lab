import json
from pathlib import Path

from cost_reporting import summarize_usage, print_usage_summary
from llm_evaluator import evaluate_ai_response
from risk_reporting import build_risk_summary, print_risk_summary


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_FILE = BASE_DIR / "reports" / "pr_results.json"
EVALUATED_FILE = BASE_DIR / "reports" / "pr_evaluated.json"


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
    retrieval_pass = evaluate_retrieval(case)
    ai_evaluation = evaluate_ai_response(
        query=case.get("query", ""),
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
            "correctness": correctness,
            "groundedness": groundedness,
            "hallucination": hallucination,
            "constraint_adherence": constraint_adherence,
            "context_coverage": context_coverage,
            "context_sufficient": context_sufficient,
            "overall_pass": overall_pass,
            "reason": ai_evaluation.get("reason"),
            "judge_telemetry": ai_evaluation.get("_telemetry", {}),
        },
    }


def percentage(value, total):
    return round(value / total * 100, 2) if total else 0.0


def percentile(values, percentile_value):
    if not values:
        return 0.0
    values = sorted(values)
    index = (percentile_value / 100) * (len(values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return round(values[lower] + (values[upper] - values[lower]) * fraction, 2)


def run_evaluator():
    with open(RESULTS_FILE, "r", encoding="utf-8") as file:
        results = json.load(file)

    evaluated_cases = []
    for number, case in enumerate(results, start=1):
        print(f"[{number}/{len(results)}] Evaluating {case.get('case_id', 'UNKNOWN')}")
        evaluated_cases.append(evaluate_case(case))

    total = len(evaluated_cases)
    overall_passed = sum(c["evaluation"]["overall_pass"] for c in evaluated_cases)
    retrieval_passed = sum(c["evaluation"]["retrieval_pass"] for c in evaluated_cases)
    correctness_passed = sum(c["evaluation"]["correctness"] for c in evaluated_cases)
    groundedness_passed = sum(c["evaluation"]["groundedness"] for c in evaluated_cases)
    constraint_passed = sum(c["evaluation"]["constraint_adherence"] for c in evaluated_cases)
    hallucinations = sum(c["evaluation"]["hallucination"] for c in evaluated_cases)
    context_sufficient = sum(c["evaluation"]["context_sufficient"] for c in evaluated_cases)
    context_coverage = [c["evaluation"]["context_coverage"] for c in evaluated_cases]
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
        "correctness_rate": percentage(correctness_passed, total),
        "groundedness_rate": percentage(groundedness_passed, total),
        "constraint_adherence_rate": percentage(constraint_passed, total),
        "hallucination_rate": percentage(hallucinations, total),
        "average_context_coverage": round(sum(context_coverage) / len(context_coverage), 2) if context_coverage else 0.0,
        "context_sufficiency_rate": percentage(context_sufficient, total),
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
    with open(EVALUATED_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("\nAI Evaluation Summary")
    print("---------------------")
    print(f"Total cases: {total}")
    print(f"Passed: {overall_passed}")
    print(f"Failed: {total - overall_passed}")
    print(f"Overall Pass Rate: {summary['overall_pass_rate']}%")
    print(f"Retrieval Hit Rate: {summary['retrieval_hit_rate']}%")
    print(f"Correctness Rate: {summary['correctness_rate']}%")
    print(f"Groundedness Rate: {summary['groundedness_rate']}%")
    print(f"Constraint Adherence Rate: {summary['constraint_adherence_rate']}%")
    print(f"Hallucination Rate: {summary['hallucination_rate']}%")
    print(f"Average Context Coverage: {summary['average_context_coverage']}%")
    print(f"Context Sufficiency Rate: {summary['context_sufficiency_rate']}%")
    print_risk_summary(risk_report)

    print("\nOperational Metrics")
    print("-------------------")
    print(f"Average latency: {summary['operational_metrics']['average_latency_ms']} ms")
    print(f"P95 latency: {summary['operational_metrics']['p95_latency_ms']} ms")
    print_usage_summary(usage)
    print(f"\nSaved to: {EVALUATED_FILE}")


if __name__ == "__main__":
    run_evaluator()
