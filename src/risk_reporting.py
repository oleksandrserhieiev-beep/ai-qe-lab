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
            "correctness_measured": 0,
            "correctness_passed": 0,
            "groundedness_measured": 0,
            "groundedness_passed": 0,
            "constraint_passed": 0,
            "hallucination_measured": 0,
            "hallucinations": 0,
            "context_coverage_scores": [],
        }
    )
    unclassified_cases = []

    for case in evaluated_cases:
        risks = normalize_risks(case.get("risk"))
        evaluation = case.get("evaluation", {})

        if not risks:
            unclassified_cases.append(case.get("case_id", "UNKNOWN"))
            continue

        for risk in risks:
            bucket = buckets[risk]
            bucket["total_cases"] += 1

            overall_pass = bool(evaluation.get("overall_pass", False))
            if overall_pass:
                bucket["passed"] += 1
            else:
                bucket["failed"] += 1

            bucket["retrieval_passed"] += int(bool(evaluation.get("retrieval_pass", False)))

            correctness = evaluation.get("correctness")
            if correctness is not None:
                bucket["correctness_measured"] += 1
                bucket["correctness_passed"] += int(bool(correctness))

            groundedness = evaluation.get("groundedness")
            if groundedness is not None:
                bucket["groundedness_measured"] += 1
                bucket["groundedness_passed"] += int(bool(groundedness))

            bucket["constraint_passed"] += int(
                bool(evaluation.get("constraint_adherence", False))
            )

            hallucination = evaluation.get("hallucination")
            if hallucination is not None:
                bucket["hallucination_measured"] += 1
                bucket["hallucinations"] += int(bool(hallucination))

            context_coverage = evaluation.get("context_coverage")
            if context_coverage is not None:
                bucket["context_coverage_scores"].append(float(context_coverage))

    risk_summary = {}
    for risk in sorted(buckets):
        bucket = buckets[risk]
        total = bucket["total_cases"]
        correctness_measured = bucket["correctness_measured"]
        groundedness_measured = bucket["groundedness_measured"]
        hallucination_measured = bucket["hallucination_measured"]

        risk_summary[risk] = {
            "total_cases": total,
            "passed": bucket["passed"],
            "failed": bucket["failed"],
            "pass_rate": percentage(bucket["passed"], total),
            "retrieval_hit_rate": percentage(bucket["retrieval_passed"], total),
            "correctness_rate": (
                percentage(bucket["correctness_passed"], correctness_measured)
                if correctness_measured else None
            ),
            "correctness_measured_cases": correctness_measured,
            "groundedness_rate": (
                percentage(bucket["groundedness_passed"], groundedness_measured)
                if groundedness_measured else None
            ),
            "groundedness_measured_cases": groundedness_measured,
            "constraint_adherence_rate": percentage(bucket["constraint_passed"], total),
            "hallucination_rate": (
                percentage(bucket["hallucinations"], hallucination_measured)
                if hallucination_measured else None
            ),
            "hallucination_measured_cases": hallucination_measured,
        }

        if bucket["context_coverage_scores"]:
            risk_summary[risk]["average_context_coverage"] = average(
                bucket["context_coverage_scores"]
            )

    return {
        "risk_summary": risk_summary,
        "risk_count": len(risk_summary),
        "unclassified_count": len(unclassified_cases),
        "unclassified_cases": unclassified_cases,
    }


def _semantic_metric_text(name, rate, measured_cases, inverse=False):
    if not measured_cases or rate is None:
        return f"{name} N/A (0 semantic cases)"

    noun = "case" if measured_cases == 1 else "cases"
    if inverse:
        hallucinations = round(rate * measured_cases / 100)
        return (
            f"{name} {rate}% "
            f"({hallucinations}/{measured_cases} hallucinated; {measured_cases} semantic {noun})"
        )

    passed = round(rate * measured_cases / 100)
    return f"{name} {rate}% ({passed}/{measured_cases}; {measured_cases} semantic {noun})"


def print_risk_summary(risk_report):
    print("\nAI Risk Summary")
    print("---------------")

    risk_summary = risk_report.get("risk_summary", {})
    if not risk_summary:
        print("No classified AI risks found.")
    else:
        for risk, metrics in risk_summary.items():
            groundedness_text = _semantic_metric_text(
                "Groundedness",
                metrics.get("groundedness_rate"),
                metrics.get("groundedness_measured_cases", 0),
            )
            hallucination_text = _semantic_metric_text(
                "Hallucination",
                metrics.get("hallucination_rate"),
                metrics.get("hallucination_measured_cases", 0),
                inverse=True,
            )
            print(
                f"{risk}: "
                f"{metrics['passed']}/{metrics['total_cases']} PASS "
                f"({metrics['pass_rate']}%), "
                f"{groundedness_text}, "
                f"{hallucination_text}"
            )

    print(f"Unclassified cases: {risk_report.get('unclassified_count', 0)}")
