import argparse
import json
from pathlib import Path


QUALITY_METRICS = [
    ("overall_pass_rate", "Overall pass rate", True, "%"),
    ("correctness_rate", "Correctness", True, "%"),
    ("groundedness_rate", "Groundedness", True, "%"),
    ("retrieval_hit_rate", "Retrieval hit rate", True, "%"),
    ("constraint_adherence_rate", "Constraint adherence", True, "%"),
    ("hallucination_rate", "Hallucination rate", False, "%"),
]

OPERATIONAL_METRICS = [
    ("avg_latency_ms", "Average latency", False, " ms"),
    ("p95_latency_ms", "P95 latency", False, " ms"),
    ("total_input_tokens", "Input tokens", False, ""),
    ("total_output_tokens", "Output tokens", False, ""),
    ("total_tokens", "Total tokens", False, ""),
    ("avg_tokens_per_case", "Average tokens / case", False, ""),
]


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def comparison_status(model_a, model_b, higher_is_better):
    if model_a is None or model_b is None or model_a == model_b:
        return "same"
    model_b_is_better = model_b > model_a if higher_is_better else model_b < model_a
    return "better" if model_b_is_better else "worse"


def _signal(status):
    return {"better": "B better", "worse": "B worse", "same": "Same"}[status]


def _format(value, suffix=""):
    if value is None:
        return "N/A"
    return f"{value}{suffix}"


def _metric_table(section, definitions, model_a_name, model_b_name):
    lines = [
        f"| Metric | {model_a_name} | {model_b_name} | Delta B-A | Signal |",
        "|---|---:|---:|---:|---|",
    ]
    for key, label, higher_is_better, suffix in definitions:
        values = section.get(key, {})
        a = values.get("model_a")
        b = values.get("model_b")
        delta = values.get("delta_b_minus_a")
        status = comparison_status(a, b, higher_is_better)
        lines.append(
            f"| {label} | {_format(a, suffix)} | {_format(b, suffix)} | "
            f"{_format(delta, suffix)} | {_signal(status)} |"
        )
    return lines


def _failed_cases(report):
    failed = []
    for case in report.get("cases", []):
        evaluation = case.get("evaluation", {})
        if not evaluation.get("overall_pass", False):
            reason = str(evaluation.get("reason") or "No reason reported").replace("\n", " ")
            if len(reason) > 180:
                reason = reason[:177] + "..."
            failed.append((case.get("case_id", "UNKNOWN"), reason))
    return failed


def build_report(comparison, evaluated_a, evaluated_b, model_a_name, model_b_name):
    lines = [
        f"## Back-to-Back: `{model_a_name}` vs `{model_b_name}`",
        "",
        "### Quality metrics",
        "",
        *_metric_table(comparison.get("quality_comparison", {}), QUALITY_METRICS, model_a_name, model_b_name),
        "",
        "### Operational metrics",
        "",
        *_metric_table(comparison.get("operational_comparison", {}), OPERATIONAL_METRICS, model_a_name, model_b_name),
        "",
        "### Case outcomes",
        "",
    ]

    outcomes = comparison.get("case_outcomes", {})
    lines.append(
        f"Improved: **{outcomes.get('improved', 0)}** | "
        f"Regressed: **{outcomes.get('regressed', 0)}** | "
        f"Unchanged: **{outcomes.get('unchanged', 0)}**"
    )

    interesting = [
        case for case in comparison.get("case_comparison", [])
        if case.get("status") != "unchanged"
        or not case.get("model_a_pass", False)
        or not case.get("model_b_pass", False)
    ]
    if interesting:
        lines.extend([
            "",
            f"| Case | {model_a_name} | {model_b_name} | Outcome |",
            "|---|---|---|---|",
        ])
        for case in interesting:
            lines.append(
                f"| {case.get('case_id')} | "
                f"{'PASS' if case.get('model_a_pass') else 'FAIL'} | "
                f"{'PASS' if case.get('model_b_pass') else 'FAIL'} | "
                f"{case.get('status')} |"
            )

    for model_name, report in ((model_a_name, evaluated_a), (model_b_name, evaluated_b)):
        failed = _failed_cases(report)
        lines.extend(["", f"### Failed cases — `{model_name}`", ""])
        if not failed:
            lines.append("No failed cases.")
        else:
            lines.extend(["| Case | Reason |", "|---|---|"])
            for case_id, reason in failed:
                lines.append(f"| {case_id} | {reason.replace('|', '/')} |")

    critical = comparison.get("decision_signals", {}).get("critical_regressions", [])
    lines.extend([
        "",
        "### Decision signal",
        "",
        f"Critical regressions: **{', '.join(critical) if critical else 'None'}**",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Render a readable back-to-back AI model report.")
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--model-a-report", required=True)
    parser.add_argument("--model-b-report", required=True)
    parser.add_argument("--model-a-name", required=True)
    parser.add_argument("--model-b-name", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = build_report(
        _load(args.comparison),
        _load(args.model_a_report),
        _load(args.model_b_report),
        args.model_a_name,
        args.model_b_name,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
