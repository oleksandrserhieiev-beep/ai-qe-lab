import json
import os
from pathlib import Path


def main():
    issue_key = os.environ["ISSUE_KEY"]
    report_path = Path("reports") / f"requirements_review_{issue_key}.json"
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if not report_path.exists():
        print(f"Requirements review report not found: {report_path}")
        return

    data = json.loads(report_path.read_text(encoding="utf-8"))
    review = data["review"]
    telemetry = data["telemetry"]

    cost = telemetry.get("estimated_cost_usd")
    cost_text = f"${cost:.6f}" if cost is not None else "N/A"
    latency_seconds = telemetry.get("latency_ms", 0) / 1000

    lines = [
        "## Requirements Review Agent",
        "",
        f"**Story:** `{issue_key}`  ",
        f"**Decision:** `{review['decision']}`  ",
        f"**Readiness score:** `{review['readiness_score']}/100`  ",
        f"**Model:** `{telemetry['model']}`",
        "",
        "### AI usage",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Input tokens | {telemetry['input_tokens']:,} |",
        f"| Output tokens | {telemetry['output_tokens']:,} |",
        f"| **Total tokens** | **{telemetry['total_tokens']:,}** |",
        f"| **Estimated cost** | **{cost_text}** |",
        f"| Latency | {latency_seconds:.2f}s |",
        "",
        f"**Gaps found:** {len(review['gaps'])}  ",
        f"**Recommended next action:** {review['recommended_next_action']}",
    ]

    summary = "\n".join(lines) + "\n"
    print(summary)

    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)


if __name__ == "__main__":
    main()
