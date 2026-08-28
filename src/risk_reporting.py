from collections import defaultdict


def percentage(value, total):
    if total == 0:
        return 0.0

    return round(value / total * 100, 2)


def average(values):
    if not values:
        return 0.0

    return round(sum(values) / len(values), 2)


def normalize_risks(value):
    if value is None:
        return []

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, list):
        return []

    normalized = []

    for risk in value:
        if risk is None:
            continue

        risk_name = str(risk).strip()

        if risk_name and risk_name not in normalized:
            normalized.append(risk_name)

    return normalized


def build_risk_summary(evaluated_cases):
    buckets = defaultdict(
        lambda: {
            "total_cases": 0,
            "passed": 0,
            "failed": 0,
            "retrieval_passed": 0,
            "correctness_passed": 0,
            "groundedness_passed": 0,
            "constraint_passed": 0,
            "hallucinations": 0,
            "context_coverage_scores": [],
        }
    )

    unclassified_cases = []

    for case in evaluated_cases:
        risks = normalize_risks(case.get("risk"))
        evaluation = case.get("evaluation", {})

        if not risks:
            unclassified_cases.append(
                case.get("case_id", "UNKNOWN")
            )
            continue

        for risk in risks:
            bucket = buckets[risk]
            bucket["total_cases"] += 1

            overall_pass = bool(
                evaluation.get("overall_pass", False)
            )

            if overall_pass:
                bucket["passed"] += 1
            else:
                bucket["failed"] += 1

            bucket["retrieval_passed"] += int(
                bool(evaluation.get("retrieval_pass", False))
            )
            bucket["correctness_passed"] += int(
                bool(evaluation.get("correctness", False))
            )
            bucket["groundedness_passed"] += int(
                bool(evaluation.get("groundedness", False))
            )
            bucket["constraint_passed"] += int(
                bool(
                    evaluation.get(
                        "constraint_adherence",
                        False,
                    )
                )
            )
            bucket["hallucinations"] += int(
                bool(evaluation.get("hallucination", False))
            )

            context_coverage = evaluation.get(
                "context_coverage"
            )

            if context_coverage is not None:
                bucket["context_coverage_scores"].append(
                    float(context_coverage)
                )

    risk_summary = {}

    for risk in sorted(buckets):
        bucket = buckets[risk]
        total = bucket["total_cases"]

        risk_summary[risk] = {
            "total_cases": total,
            "passed": bucket["passed"],
            "failed": bucket["failed"],
            "pass_rate": percentage(
                bucket["passed"],
                total,
            ),
            "retrieval_hit_rate": percentage(
                bucket["retrieval_passed"],
                total,
            ),
            "correctness_rate": percentage(
                bucket["correctness_passed"],
                total,
            ),
            "groundedness_rate": percentage(
                bucket["groundedness_passed"],
                total,
            ),
            "constraint_adherence_rate": percentage(
                bucket["constraint_passed"],
                total,
            ),
            "hallucination_rate": percentage(
                bucket["hallucinations"],
                total,
            ),
        }

        if bucket["context_coverage_scores"]:
            risk_summary[risk][
                "average_context_coverage"
            ] = average(
                bucket["context_coverage_scores"]
            )

    return {
        "risk_summary": risk_summary,
        "risk_count": len(risk_summary),
        "unclassified_count": len(unclassified_cases),
        "unclassified_cases": unclassified_cases,
    }


def print_risk_summary(risk_report):
    print("\nAI Risk Summary")
    print("---------------")

    risk_summary = risk_report.get(
        "risk_summary",
        {},
    )

    if not risk_summary:
        print("No classified AI risks found.")
    else:
        for risk, metrics in risk_summary.items():
            print(
                f"{risk}: "
                f"{metrics['passed']}/{metrics['total_cases']} PASS "
                f"({metrics['pass_rate']}%), "
                f"Groundedness {metrics['groundedness_rate']}%, "
                f"Hallucination {metrics['hallucination_rate']}%"
            )

    unclassified_count = risk_report.get(
        "unclassified_count",
        0,
    )

    print(
        f"Unclassified cases: {unclassified_count}"
    )
