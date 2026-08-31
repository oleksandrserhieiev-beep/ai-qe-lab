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

# Retrieval is intentionally excluded from the model verdict because both models
# receive the same retrieved context in the back-to-back experiment.
VERDICT_QUALITY_METRICS = [
    ("correctness_rate", True),
    ("groundedness_rate", True),
    ("constraint_adherence_rate", True),
    ("hallucination_rate", False),
]

OPERATIONAL_METRICS = [
    ("avg_latency_ms", "Average latency", False, " ms"),
    ("p95_latency_ms", "P95 latency", False, " ms"),
    ("total_input_tokens", "Input tokens", False, ""),
    ("total_output_tokens", "Output tokens", False, ""),
    ("total_tokens", "Total tokens", False, ""),
    ("avg_tokens_per_case", "Average tokens / case", False, ""),
]

VERDICT_OPERATIONAL_METRICS = [
    "avg_latency_ms",
    "p95_latency_ms",
    "total_tokens",
    "avg_tokens_per_case",
]


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def comparison_status(model_a, model_b, higher_is_better):
    if model_a is None or model_b is None or model_a == model_b:
        return "same"
    model_b_is_better = model_b > model_a if higher_is_better else model_b < model_a
    return "better" if model_b_is_better else "worse"


def _signal(status, model_a_name, model_b_name):
    return {
        "better": f"{model_b_name} better",
        "worse": f"{model_a_name} better",
        "same": "Same",
    }[status]


def _format(value, suffix=""):
    if value is None:
        return "N/A"
    return f"{value}{suffix}"


def _metric_rows(section, definitions, model_a_name, model_b_name):
    rows = []
    for key, label, higher_is_better, suffix in definitions:
        values = section.get(key, {})
        a = values.get("model_a")
        b = values.get("model_b")
        delta = values.get("delta_b_minus_a")
        status = comparison_status(a, b, higher_is_better)
        rows.append(
            {
                "label": label,
                "a": _format(a, suffix),
                "b": _format(b, suffix),
                "delta": _format(delta, suffix),
                "signal": _signal(status, model_a_name, model_b_name),
                "status": status,
            }
        )
    return rows


def _markdown_metric_table(section, definitions, model_a_name, model_b_name):
    lines = [
        f"| Metric | {model_a_name} | {model_b_name} | Delta B-A | Better |",
        "|---|---:|---:|---:|---|",
    ]
    for row in _metric_rows(section, definitions, model_a_name, model_b_name):
        lines.append(
            f"| {row['label']} | {row['a']} | {row['b']} | {row['delta']} | {row['signal']} |"
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


def _metric_wins(section, definitions):
    a_wins = b_wins = 0
    for key, higher_is_better in definitions:
        values = section.get(key, {})
        status = comparison_status(values.get("model_a"), values.get("model_b"), higher_is_better)
        if status == "better":
            b_wins += 1
        elif status == "worse":
            a_wins += 1
    return a_wins, b_wins


def build_verdict(comparison, model_a_name, model_b_name):
    quality = comparison.get("quality_comparison", {})
    operational = comparison.get("operational_comparison", {})
    decision = comparison.get("decision_signals", {})

    critical_regressions = decision.get("critical_regressions", []) or []
    if critical_regressions:
        return {
            "winner": model_a_name,
            "basis": "quality",
            "reason": (
                f"{model_b_name} introduces critical regression(s): "
                f"{', '.join(critical_regressions)}."
            ),
        }

    pass_rate = quality.get("overall_pass_rate", {})
    a_pass = pass_rate.get("model_a")
    b_pass = pass_rate.get("model_b")
    if a_pass is not None and b_pass is not None and a_pass != b_pass:
        if b_pass > a_pass:
            winner, loser, delta = model_b_name, model_a_name, round(b_pass - a_pass, 2)
        else:
            winner, loser, delta = model_a_name, model_b_name, round(a_pass - b_pass, 2)
        return {
            "winner": winner,
            "basis": "quality",
            "reason": f"{winner} has the higher overall pass rate by {delta} percentage points versus {loser}.",
        }

    quality_a_wins, quality_b_wins = _metric_wins(quality, VERDICT_QUALITY_METRICS)
    if quality_a_wins != quality_b_wins:
        winner = model_a_name if quality_a_wins > quality_b_wins else model_b_name
        return {
            "winner": winner,
            "basis": "quality",
            "reason": (
                f"Overall pass rate is tied, but {winner} wins more model-quality metrics "
                f"({max(quality_a_wins, quality_b_wins)} vs {min(quality_a_wins, quality_b_wins)})."
            ),
        }

    op_a_wins = op_b_wins = 0
    for key in VERDICT_OPERATIONAL_METRICS:
        values = operational.get(key, {})
        status = comparison_status(values.get("model_a"), values.get("model_b"), higher_is_better=False)
        if status == "better":
            op_b_wins += 1
        elif status == "worse":
            op_a_wins += 1

    if op_a_wins != op_b_wins:
        winner = model_a_name if op_a_wins > op_b_wins else model_b_name
        return {
            "winner": winner,
            "basis": "operational efficiency",
            "reason": (
                f"Quality is tied; {winner} is more efficient on "
                f"{max(op_a_wins, op_b_wins)} of {len(VERDICT_OPERATIONAL_METRICS)} key operational metrics."
            ),
        }

    return {
        "winner": "Tie",
        "basis": "no material difference",
        "reason": "The models are tied on measured quality and key operational metrics.",
    }


def build_markdown_report(comparison, evaluated_a, evaluated_b, model_a_name, model_b_name):
    verdict = build_verdict(comparison, model_a_name, model_b_name)
    lines = [
        "# Back-to-Back Model Comparison",
        "",
        f"**Baseline:** `{model_a_name}`  ",
        f"**Candidate:** `{model_b_name}`",
        "",
        "## Verdict",
        "",
        f"**Winner: {verdict['winner']}**  ",
        f"**Basis:** {verdict['basis']}  ",
        verdict["reason"],
        "",
        "## Quality",
        "",
        *_markdown_metric_table(comparison.get("quality_comparison", {}), QUALITY_METRICS, model_a_name, model_b_name),
        "",
        "## Operational efficiency",
        "",
        *_markdown_metric_table(comparison.get("operational_comparison", {}), OPERATIONAL_METRICS, model_a_name, model_b_name),
        "",
        "## Case outcomes",
        "",
    ]

    outcomes = comparison.get("case_outcomes", {})
    lines.append(
        f"Improved: **{outcomes.get('improved', 0)}** · "
        f"Regressed: **{outcomes.get('regressed', 0)}** · "
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
        "## Release signal",
        "",
        f"Critical regressions: **{', '.join(critical) if critical else 'None'}**",
    ])
    return "\n".join(lines) + "\n"


def _console_section(title, rows, model_a_name, model_b_name):
    print(f"\n{title}")
    print("-" * len(title))
    print(f"{'Metric':<24} {model_a_name:<22} {model_b_name:<22} Better")
    print(f"{'-' * 24} {'-' * 22} {'-' * 22} {'-' * 24}")
    for row in rows:
        print(f"{row['label']:<24} {row['a']:<22} {row['b']:<22} {row['signal']}")


def print_console_report(comparison, evaluated_a, evaluated_b, model_a_name, model_b_name):
    verdict = build_verdict(comparison, model_a_name, model_b_name)
    print("\nBACK-TO-BACK MODEL COMPARISON")
    print("=" * 29)
    print(f"Baseline : {model_a_name}")
    print(f"Candidate: {model_b_name}")

    _console_section(
        "QUALITY",
        _metric_rows(comparison.get("quality_comparison", {}), QUALITY_METRICS, model_a_name, model_b_name),
        model_a_name,
        model_b_name,
    )
    _console_section(
        "OPERATIONAL EFFICIENCY",
        _metric_rows(comparison.get("operational_comparison", {}), OPERATIONAL_METRICS, model_a_name, model_b_name),
        model_a_name,
        model_b_name,
    )

    outcomes = comparison.get("case_outcomes", {})
    print("\nCASE OUTCOMES")
    print("-------------")
    print(
        f"Improved: {outcomes.get('improved', 0)} | "
        f"Regressed: {outcomes.get('regressed', 0)} | "
        f"Unchanged: {outcomes.get('unchanged', 0)}"
    )

    for model_name, report in ((model_a_name, evaluated_a), (model_b_name, evaluated_b)):
        failed = _failed_cases(report)
        if failed:
            print(f"Failed cases for {model_name}:")
            for case_id, reason in failed:
                print(f"  - {case_id}: {reason}")
        else:
            print(f"Failed cases for {model_name}: none")

    print("\nVERDICT")
    print("-------")
    print(f"Winner: {verdict['winner']}")
    print(f"Basis : {verdict['basis']}")
    print(f"Reason: {verdict['reason']}")


def main():
    parser = argparse.ArgumentParser(description="Render a readable back-to-back AI model report.")
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--model-a-report", required=True)
    parser.add_argument("--model-b-report", required=True)
    parser.add_argument("--model-a-name", required=True)
    parser.add_argument("--model-b-name", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    comparison = _load(args.comparison)
    evaluated_a = _load(args.model_a_report)
    evaluated_b = _load(args.model_b_report)

    report = build_markdown_report(
        comparison,
        evaluated_a,
        evaluated_b,
        args.model_a_name,
        args.model_b_name,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")

    print_console_report(
        comparison,
        evaluated_a,
        evaluated_b,
        args.model_a_name,
        args.model_b_name,
    )


if __name__ == "__main__":
    main()
