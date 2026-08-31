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


def main():
    parser = argparse.ArgumentParser(description="Compare two evaluated AI QE reports.")
    parser.add_argument("--model-a-report", required=True)
    parser.add_argument("--model-b-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    a = _load(args.model_a_report)
    b = _load(args.model_b_report)
    sa, sb = a["summary"], b["summary"]
    metrics = [
        "correctness_rate", "groundedness_rate", "retrieval_hit_rate",
        "constraint_adherence_rate", "hallucination_rate",
    ]
    comparison = {metric: {"model_a": sa.get(metric), "model_b": sb.get(metric), "delta_b_minus_a": _delta(sa.get(metric), sb.get(metric))} for metric in metrics}

    ca = {case["case_id"]: case for case in a["cases"]}
    cb = {case["case_id"]: case for case in b["cases"]}
    case_comparison = []
    improved = regressed = unchanged = 0
    for case_id in sorted(set(ca) & set(cb)):
        pa = bool(ca[case_id]["evaluation"]["overall_pass"])
        pb = bool(cb[case_id]["evaluation"]["overall_pass"])
        status = "unchanged"
        if not pa and pb:
            status, improved = "improved", improved + 1
        elif pa and not pb:
            status, regressed = "regressed", regressed + 1
        else:
            unchanged += 1
        case_comparison.append({"case_id": case_id, "model_a_pass": pa, "model_b_pass": pb, "status": status})

    def telemetry(raw_cases):
        latencies = [float(c.get("telemetry", {}).get("latency_ms", 0) or 0) for c in raw_cases]
        tokens = [int(c.get("telemetry", {}).get("total_tokens", 0) or 0) for c in raw_cases]
        return {
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "total_tokens": sum(tokens),
            "avg_tokens_per_case": round(sum(tokens) / len(tokens), 2) if tokens else None,
        }

    raw_a = [case for case in a["cases"]]
    raw_b = [case for case in b["cases"]]
    output = {
        "metric_comparison": comparison,
        "case_outcomes": {"improved": improved, "regressed": regressed, "unchanged": unchanged},
        "case_comparison": case_comparison,
        "note": "Latency/token telemetry remains available in the raw Model A/B reports; semantic metrics use the existing calibrated evaluator contract. Retrieval metrics are expected to remain equal when only the generation model changes."
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
