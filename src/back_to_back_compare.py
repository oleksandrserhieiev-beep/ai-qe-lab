import argparse
import json
from pathlib import Path


def _load(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _delta(a, b):
    if a is None or b is None:
        return None
    return round(b - a, 2)


def _percentile(values, percentile_value):
    if not values:
        return None
    values = sorted(values)
    index = (percentile_value / 100) * (len(values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return round(values[lower] + (values[upper] - values[lower]) * fraction, 2)


def _telemetry(cases):
    latencies = [
        float(case.get("telemetry", {}).get("latency_ms"))
        for case in cases
        if case.get("telemetry", {}).get("latency_ms") is not None
    ]
    input_tokens = sum(
        int(case.get("telemetry", {}).get("input_tokens", 0) or 0)
        for case in cases
    )
    output_tokens = sum(
        int(case.get("telemetry", {}).get("output_tokens", 0) or 0)
        for case in cases
    )
    total_tokens = sum(
        int(case.get("telemetry", {}).get("total_tokens", 0) or 0)
        for case in cases
    )
    return {
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "p95_latency_ms": _percentile(latencies, 95),
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "avg_tokens_per_case": round(total_tokens / len(cases), 2) if cases else None,
    }


def _compare_values(model_a, model_b):
    return {
        "model_a": model_a,
        "model_b": model_b,
        "delta_b_minus_a": _delta(model_a, model_b),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare two evaluated AI QE reports.")
    parser.add_argument("--model-a-report", required=True)
    parser.add_argument("--model-b-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    a = _load(args.model_a_report)
    b = _load(args.model_b_report)
    sa, sb = a["summary"], b["summary"]

    quality_metrics = [
        "overall_pass_rate",
        "correctness_rate",
        "groundedness_rate",
        "retrieval_hit_rate",
        "constraint_adherence_rate",
        "hallucination_rate",
    ]
    quality_comparison = {
        metric: _compare_values(sa.get(metric), sb.get(metric))
        for metric in quality_metrics
    }

    ca = {case["case_id"]: case for case in a["cases"]}
    cb = {case["case_id"]: case for case in b["cases"]}
    case_comparison = []
    improved = regressed = unchanged = 0

    for case_id in sorted(set(ca) & set(cb)):
        pa = bool(ca[case_id]["evaluation"]["overall_pass"])
        pb = bool(cb[case_id]["evaluation"]["overall_pass"])
        status = "unchanged"
        if not pa and pb:
            status = "improved"
            improved += 1
        elif pa and not pb:
            status = "regressed"
            regressed += 1
        else:
            unchanged += 1

        case_comparison.append({
            "case_id": case_id,
            "model_a_pass": pa,
            "model_b_pass": pb,
            "status": status,
        })

    telemetry_a = _telemetry(a["cases"])
    telemetry_b = _telemetry(b["cases"])
    operational_comparison = {
        metric: _compare_values(telemetry_a.get(metric), telemetry_b.get(metric))
        for metric in telemetry_a
    }

    output = {
        "quality_comparison": quality_comparison,
        "operational_comparison": operational_comparison,
        "case_outcomes": {
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
        },
        "case_comparison": case_comparison,
        "decision_signals": {
            "critical_regressions": [
                case_id
                for case_id in sorted(set(ca) & set(cb))
                if ca[case_id].get("criticality") == "critical"
                and ca[case_id]["evaluation"]["overall_pass"]
                and not cb[case_id]["evaluation"]["overall_pass"]
            ],
            "model_b_has_regressions": regressed > 0,
        },
        "note": (
            "Quality metrics come from the existing evaluator contract. "
            "Operational metrics compare SUT generation telemetry only. "
            "Retrieval metrics are expected to remain equal when only the generation model changes."
        ),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
