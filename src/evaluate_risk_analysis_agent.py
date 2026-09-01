import json
from pathlib import Path

from risk_analysis_agent import analyze_risks


DATASET = Path("datasets/risk_analysis_evaluation_dataset.json")


def _contains_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def evaluate_case(case: dict, result: dict) -> dict:
    risks = result.get("risks", [])
    categories = {risk.get("category") for risk in risks}
    combined = json.dumps(risks, ensure_ascii=False).lower()
    expected = set(case.get("expected_categories", []))
    category_recall = len(expected & categories) / len(expected) if expected else 1.0
    required_terms = case.get("required_focus_terms", [])
    required_hits = sum(term.lower() in combined for term in required_terms)
    required_coverage = required_hits / len(required_terms) if required_terms else 1.0
    forbidden_hits = [term for term in case.get("forbidden_claim_terms", []) if term.lower() in combined]
    count_ok = case.get("min_risks", 1) <= len(risks) <= case.get("max_risks", 20)
    passed = category_recall >= 0.5 and required_coverage >= 0.5 and not forbidden_hits and count_ok
    return {
        "case_id": case["case_id"],
        "passed": passed,
        "risk_count": len(risks),
        "expected_category_recall": round(category_recall, 3),
        "required_focus_coverage": round(required_coverage, 3),
        "forbidden_claim_hits": forbidden_hits,
        "count_within_bounds": count_ok,
    }


def main():
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    results = []
    total_tokens = 0
    total_cost = 0.0
    for case in cases:
        output, telemetry = analyze_risks(case["input"])
        evaluation = evaluate_case(case, output)
        evaluation["telemetry"] = telemetry
        evaluation["agent_output"] = output
        total_tokens += telemetry["total_tokens"]
        total_cost += telemetry["estimated_cost_usd"]
        results.append(evaluation)

    passed = sum(item["passed"] for item in results)
    summary = {
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate_pct": round(100 * passed / len(results), 1) if results else 0.0,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(total_cost, 6),
        "results": results,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/risk_analysis_agent_evaluation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
