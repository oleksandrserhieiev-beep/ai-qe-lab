import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from jira_requirements import load_requirement
from requirements_review_agent import review_requirement


def main():
    parser = argparse.ArgumentParser(description="Run Requirements Review Agent for one Jira issue")
    parser.add_argument("issue_key", help="Jira issue key, for example SCRUM-1")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path. Defaults to reports/requirements_review_<ISSUE>.json",
    )
    args = parser.parse_args()

    requirement = load_requirement(args.issue_key)
    review, telemetry = review_requirement(requirement)

    result = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "issue_key": args.issue_key,
        "requirement": requirement,
        "review": review,
        "telemetry": telemetry,
    }

    output_path = Path(args.output) if args.output else Path("reports") / f"requirements_review_{args.issue_key}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Issue: {args.issue_key}")
    print(f"Decision: {review['decision']}")
    print(f"Readiness score: {review['readiness_score']}/100")
    print(f"Gaps: {len(review['gaps'])}")
    print(f"Next action: {review['recommended_next_action']}")
    print(
        "Usage: "
        f"{telemetry['input_tokens']} input + {telemetry['output_tokens']} output = "
        f"{telemetry['total_tokens']} tokens"
    )
    if telemetry.get("estimated_cost_usd") is not None:
        print(f"Estimated cost: ${telemetry['estimated_cost_usd']:.6f}")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
