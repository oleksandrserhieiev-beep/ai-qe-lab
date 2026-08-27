import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"

K5_FILE = REPORTS_DIR / "baseline_topk5.json"
K10_FILE = REPORTS_DIR / "baseline_topk10.json"


def load_summary(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["summary"]


def get_metric(summary, metric):
    return summary.get(metric, 0)


def get_operational_metric(summary, metric):
    operational = summary.get("operational_metrics", {})
    return operational.get(metric, 0)


def calculate_change(k5, k10):
    if k5 == 0:
        return 0

    return round(((k10 - k5) / k5) * 100, 2)


def print_row(name, k5, k10, suffix=""):
    difference = round(k10 - k5, 2)

    print(
        f"{name:<32}"
        f"{str(k5) + suffix:<16}"
        f"{str(k10) + suffix:<16}"
        f"{str(difference) + suffix}"
    )


def compare():
    k5 = load_summary(K5_FILE)
    k10 = load_summary(K10_FILE)

    print("\nTOP-K BASELINE COMPARISON")
    print("=" * 78)

    print(
        f"{'Metric':<32}"
        f"{'K=5':<16}"
        f"{'K=10':<16}"
        f"{'Difference'}"
    )

    print("-" * 78)

    print_row(
        "Overall Pass Rate",
        get_metric(k5, "overall_pass_rate"),
        get_metric(k10, "overall_pass_rate"),
        "%",
    )

    print_row(
        "Retrieval Hit Rate",
        get_metric(k5, "retrieval_hit_rate"),
        get_metric(k10, "retrieval_hit_rate"),
        "%",
    )

    print_row(
        "Correctness Rate",
        get_metric(k5, "correctness_rate"),
        get_metric(k10, "correctness_rate"),
        "%",
    )

    print_row(
        "Groundedness Rate",
        get_metric(k5, "groundedness_rate"),
        get_metric(k10, "groundedness_rate"),
        "%",
    )

    print_row(
        "Constraint Adherence",
        get_metric(k5, "constraint_adherence_rate"),
        get_metric(k10, "constraint_adherence_rate"),
        "%",
    )

    print_row(
        "Hallucination Rate",
        get_metric(k5, "hallucination_rate"),
        get_metric(k10, "hallucination_rate"),
        "%",
    )

    print("-" * 78)

    k5_avg_latency = get_operational_metric(
        k5,
        "average_latency_ms",
    )
    k10_avg_latency = get_operational_metric(
        k10,
        "average_latency_ms",
    )

    k5_p95 = get_operational_metric(
        k5,
        "p95_latency_ms",
    )
    k10_p95 = get_operational_metric(
        k10,
        "p95_latency_ms",
    )

    k5_input = get_operational_metric(
        k5,
        "total_input_tokens",
    )
    k10_input = get_operational_metric(
        k10,
        "total_input_tokens",
    )

    k5_output = get_operational_metric(
        k5,
        "total_output_tokens",
    )
    k10_output = get_operational_metric(
        k10,
        "total_output_tokens",
    )

    print_row(
        "Average Latency",
        k5_avg_latency,
        k10_avg_latency,
        " ms",
    )

    print_row(
        "P95 Latency",
        k5_p95,
        k10_p95,
        " ms",
    )

    print_row(
        "Total Input Tokens",
        k5_input,
        k10_input,
    )

    print_row(
        "Total Output Tokens",
        k5_output,
        k10_output,
    )

    print("\nRELATIVE COST / PERFORMANCE CHANGE")
    print("=" * 78)

    print(
        "Average latency change: "
        f"{calculate_change(k5_avg_latency, k10_avg_latency)}%"
    )

    print(
        "P95 latency change: "
        f"{calculate_change(k5_p95, k10_p95)}%"
    )

    print(
        "Input token change: "
        f"{calculate_change(k5_input, k10_input)}%"
    )

    print(
        "Output token change: "
        f"{calculate_change(k5_output, k10_output)}%"
    )


if __name__ == "__main__":
    compare()