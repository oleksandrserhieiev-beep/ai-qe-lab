import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(description="Build adversarial testing summary from an evaluated AI QE report.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--evaluated-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dataset = load_json(resolve_path(args.dataset))
    evaluated = load_json(resolve_path(args.evaluated_report))
    metadata = {case["ID"]: case for case in dataset}

    cases = []
    category_totals = Counter()
    category_passed = Counter()
    critical_failures = []

    for case in evaluated.get("cases", []):
        case_id = case.get("case_id")
        source = metadata.get(case_id, {})
        category = source.get("Attack Category", "unclassified")
        passed = bool(case.get("evaluation", {}).get("overall_pass"))
        category_totals[category] += 1
        if passed:
            category_passed[category] += 1
        if str(source.get("Criticality", "")).lower() == "critical" and not passed:
            critical_failures.append(case_id)
        cases.append({
            "case_id": case_id,
            "attack_category": category,
            "criticality": source.get("Criticality"),
            "protected_rule_asset": source.get("Protected Rule / Asset"),
            "prohibited_behavior": source.get("Prohibited Behavior"),
            "traceability": source.get("Traceability"),
            "overall_pass": passed,
            "judge_route": case.get("evaluation", {}).get("judge_route"),
            "reason": case.get("evaluation", {}).get("reason"),
        })

    total = len(cases)
    passed = sum(case["overall_pass"] for case in cases)
    failed = total - passed
    category_breakdown = {}
    for category in sorted(category_totals):
        count = category_totals[category]
        category_pass_count = category_passed[category]
        category_breakdown[category] = {
            "total": count,
            "passed": category_pass_count,
            "failed": count - category_pass_count,
            "pass_rate": round(category_pass_count / count * 100, 2) if count else None,
        }

    output = {
        "summary": {
            "total_cases": total,
            "passed": passed,
            "failed": failed,
            "adversarial_pass_rate": round(passed / total * 100, 2) if total else None,
            "attack_success_rate": round(failed / total * 100, 2) if total else None,
            "critical_failure_count": len(critical_failures),
            "critical_failures": critical_failures,
        },
        "category_breakdown": category_breakdown,
        "cases": cases,
    }

    output_path = resolve_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
