import os


# Current Claude API list prices in USD per 1M tokens.
# Override through environment variables if pricing changes.
DEFAULT_PRICING = {
    "claude-sonnet-5": {"input": 2.0, "output": 10.0},
    "claude-opus-5": {"input": 5.0, "output": 25.0},
}


def _price(model, direction):
    env_name = f"PRICE_{model.upper().replace('-', '_')}_{direction.upper()}_PER_M"
    if os.getenv(env_name):
        return float(os.getenv(env_name))
    return DEFAULT_PRICING.get(model, {}).get(direction)


def estimate_cost(model, input_tokens=0, output_tokens=0):
    input_price = _price(model, "input")
    output_price = _price(model, "output")
    if input_price is None or output_price is None:
        return None
    return round(
        (input_tokens / 1_000_000) * input_price
        + (output_tokens / 1_000_000) * output_price,
        6,
    )


def summarize_usage(cases):
    summary = {
        "sut": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
        "judge": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
    }

    for case in cases:
        sut = case.get("telemetry", {}) or {}
        judge = case.get("evaluation", {}).get("judge_telemetry", {}) or {}

        for bucket_name, telemetry in (("sut", sut), ("judge", judge)):
            bucket = summary[bucket_name]
            input_tokens = int(telemetry.get("input_tokens") or 0)
            output_tokens = int(telemetry.get("output_tokens") or 0)
            model = telemetry.get("model")
            bucket["input_tokens"] += input_tokens
            bucket["output_tokens"] += output_tokens
            cost = estimate_cost(model, input_tokens, output_tokens) if model else None
            if cost is not None:
                bucket["cost_usd"] += cost

    for bucket in summary.values():
        bucket["cost_usd"] = round(bucket["cost_usd"], 6)
        bucket["total_tokens"] = bucket["input_tokens"] + bucket["output_tokens"]

    total_input = summary["sut"]["input_tokens"] + summary["judge"]["input_tokens"]
    total_output = summary["sut"]["output_tokens"] + summary["judge"]["output_tokens"]
    total_cost = summary["sut"]["cost_usd"] + summary["judge"]["cost_usd"]
    case_count = len(cases)

    summary["total"] = {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "cost_usd": round(total_cost, 6),
        "cost_per_case_usd": round(total_cost / case_count, 6) if case_count else 0.0,
    }
    return summary


def print_usage_summary(summary):
    print("\nToken / Cost Metrics")
    print("--------------------")
    print("Layer | Input | Output | Total | Estimated cost (USD)")
    for name in ("sut", "judge"):
        item = summary[name]
        print(
            f"{name.upper():5} | {item['input_tokens']:5} | {item['output_tokens']:6} | "
            f"{item['total_tokens']:5} | ${item['cost_usd']:.6f}"
        )
    total = summary["total"]
    print(
        f"TOTAL | {total['input_tokens']:5} | {total['output_tokens']:6} | "
        f"{total['total_tokens']:5} | ${total['cost_usd']:.6f}"
    )
    print(f"Cost / case: ${total['cost_per_case_usd']:.6f}")
