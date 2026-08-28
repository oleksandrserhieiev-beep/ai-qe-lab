import argparse
import json
from pathlib import Path


def load(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def metric(report, *keys, default=0):
    value = report
    for key in keys:
        value = value.get(key, {})
    return value if value != {} else default


def change(before, after):
    if before == 0:
        return None
    return round((after - before) / before * 100, 2)


def main():
    parser = argparse.ArgumentParser(description="Compare AI evaluation cost before and after optimization.")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--output", default="reports/cost_comparison.json")
    args = parser.parse_args()

    before = load(args.before)
    after = load(args.after)

    rows = {}
    for layer in ("sut", "judge", "total"):
        b = metric(before, "summary", "operational_metrics", "token_cost", layer, default={})
        a = metric(after, "summary", "operational_metrics", "token_cost", layer, default={})
        rows[layer] = {
            "before": b,
            "after": a,
            "token_change_pct": change(b.get("total_tokens", 0), a.get("total_tokens", 0)),
            "cost_change_pct": change(b.get("cost_usd", 0), a.get("cost_usd", 0)),
        }

    quality_keys = [
        "overall_pass_rate",
        "retrieval_hit_rate",
        "correctness_rate",
        "groundedness_rate",
        "constraint_adherence_rate",
        "hallucination_rate",
        "average_context_coverage",
        "context_sufficiency_rate",
    ]
    quality = {
        key: {
            "before": before.get("summary", {}).get(key),
            "after": after.get("summary", {}).get(key),
        }
        for key in quality_keys
    }

    report = {"usage": rows, "quality": quality}
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("AI Evaluation Cost Comparison")
    print("-----------------------------")
    print("Layer | Before tokens | After tokens | Change | Before $ | After $ | Change")
    for layer in ("sut", "judge", "total"):
        row = rows[layer]
        bt = row["before"].get("total_tokens", 0)
        at = row["after"].get("total_tokens", 0)
        bc = row["before"].get("cost_usd", 0)
        ac = row["after"].get("cost_usd", 0)
        tc = row["token_change_pct"]
        cc = row["cost_change_pct"]
        print(f"{layer.upper():5} | {bt:13} | {at:12} | {tc if tc is not None else 'n/a'}% | ${bc:.6f} | ${ac:.6f} | {cc if cc is not None else 'n/a'}%")

    print("\nQuality comparison")
    print("------------------")
    for key, values in quality.items():
        print(f"{key}: {values['before']} -> {values['after']}")
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
