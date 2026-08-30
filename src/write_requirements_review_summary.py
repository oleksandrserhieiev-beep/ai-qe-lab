import json
import os
from pathlib import Path


def _cell(value) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br>")


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
    gaps = review["gaps"]

    cost = telemetry.get("estimated_cost_usd")
    cost_text = f"${cost:.6f}" if cost is not None else "N/A"
    latency_seconds = telemetry.get("latency_ms", 0) / 1000
    blocking_count = sum(gap.get("gap_type") == "BLOCKING_GAP" for gap in gaps)
    non_blocking_count = sum(gap.get("gap_type") == "NON_BLOCKING_GAP" for gap in gaps)
    technical_count = sum(gap.get("gap_type") == "TECHNICAL_CONTEXT_NEEDED" for gap in gaps)

    lines = [
        "## Requirements Review Agent",
        "",
        f"**Story:** `{issue_key}`  ",
        f"**Decision:** `{review['decision']}`  ",
        f"**Readiness score:** `{review['readiness_score']}/100`  ",
        f"**Model:** `{telemetry['model']}`",
        "",
        "### Finding summary",
        "",
        "| Type | Count | Gate impact |",
        "| --- | ---: | --- |",
        f"| BLOCKING_GAP | {blocking_count} | Blocks readiness |",
        f"| NON_BLOCKING_GAP | {non_blocking_count} | Does not block |",
        f"| TECHNICAL_CONTEXT_NEEDED | {technical_count} | Does not block |",
        f"| **Total** | **{len(gaps)}** | |",
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
        f"### Findings ({len(gaps)})",
        "",
    ]

    if gaps:
        lines.extend(
            [
                "| # | Type | Severity | ISO/quality criterion | Category | Finding | Clarification |",
                "| ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for index, gap in enumerate(gaps, start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        _cell(gap.get("gap_type", "")),
                        _cell(gap.get("severity", "")).upper(),
                        _cell(gap.get("criterion", "")),
                        _cell(gap.get("category", "other")),
                        _cell(gap.get("finding", "")),
                        _cell(gap.get("clarification_question", "")),
                    ]
                )
                + " |"
            )
        lines.append("")
    else:
        lines.extend(["No requirement gaps identified.", ""])

    blocking_questions = [
        gap.get("clarification_question", "").strip()
        for gap in gaps
        if gap.get("gap_type") == "BLOCKING_GAP" and gap.get("clarification_question", "").strip()
    ]
    if blocking_questions:
        lines.extend(["### Blocking clarification questions", ""])
        for question in blocking_questions:
            lines.append(f"- {question}")
        lines.append("")

    lines.extend(
        [
            "### Recommendation",
            "",
            f"**Recommended next action:** `{review['recommended_next_action']}`",
        ]
    )

    summary = "\n".join(lines) + "\n"
    print(summary)

    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)


if __name__ == "__main__":
    main()
