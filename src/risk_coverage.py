import argparse
import json
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SUITES = {
    "critical": BASE_DIR / "datasets" / "pr_critical_dataset.json",
    "regression": BASE_DIR / "datasets" / "regression_dataset.json",
    "nightly": BASE_DIR / "datasets" / "evaluation_dataset.json",
}

CANONICAL_RISK_MAP = {
    "retrieval_quality": ["retrieval_quality"],
    "constraint_adherence": ["constraint_adherence"],
    "policy_grounding": ["policy_grounding"],
    "sensitive_data_handling": ["sensitive_data_handling"],
    "out_of_domain_abstention": ["out_of_domain_abstention"],
    "robustness": ["robustness"],
    "negative_behavior": ["negative_behavior"],
    "retrieval_and_constraints": ["retrieval_quality", "constraint_adherence"],
    "privacy_and_safety": ["sensitive_data_handling"],
    "out_of_domain": ["out_of_domain_abstention"],
    "hallucination": ["hallucination"],
    "policy_constraint": ["policy_grounding", "constraint_adherence"],
    "hallucination_and_policy": ["hallucination", "policy_grounding"],
    "multi_constraint": ["retrieval_quality", "constraint_adherence"],
    "prompt_injection": ["prompt_injection"],
    "groundedness": ["groundedness"],
    "conflicting_data": ["conflicting_data"],
    "long_query_and_multi_constraint": [
        "robustness",
        "retrieval_quality",
        "constraint_adherence",
    ],
}

SEGMENT_RISK_MAP = {
    "normal": ["baseline_behavior"],
    "ambiguous": ["ambiguity"],
    "negative": ["negative_behavior", "hallucination"],
    "multi_constraint": ["retrieval_quality", "constraint_adherence"],
    "out_of_domain": ["out_of_domain_abstention"],
    "missing_info": ["missing_information", "hallucination"],
    "conflict": ["conflicting_data", "policy_grounding"],
    "adversarial": ["prompt_injection"],
    "paraphrase": ["robustness", "policy_grounding"],
    "long_query": ["robustness", "retrieval_quality", "constraint_adherence"],
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build AI risk coverage matrix across evaluation suites."
    )
    parser.add_argument(
        "--output",
        default="reports/risk_coverage.json",
        help="Output JSON path.",
    )
    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def canonicalize_case_risks(case):
    explicit_risks = normalize_list(case.get("Risk"))
    canonical = []

    for risk in explicit_risks:
        mapped = CANONICAL_RISK_MAP.get(risk, [risk])
        for item in mapped:
            if item not in canonical:
                canonical.append(item)

    if canonical:
        return canonical

    segment = case.get("Segment")
    for item in SEGMENT_RISK_MAP.get(segment, []):
        if item not in canonical:
            canonical.append(item)

    return canonical


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_coverage_matrix(suites=None):
    suites = suites or SUITES
    matrix = defaultdict(lambda: defaultdict(list))
    unclassified = defaultdict(list)
    suite_totals = {}

    for suite_name, dataset_path in suites.items():
        cases = load_dataset(dataset_path)
        suite_totals[suite_name] = len(cases)

        for case in cases:
            case_id = case.get("ID", "UNKNOWN")
            risks = canonicalize_case_risks(case)

            if not risks:
                unclassified[suite_name].append(case_id)
                continue

            for risk in risks:
                matrix[risk][suite_name].append(case_id)

    all_suites = list(suites.keys())
    rows = []

    for risk in sorted(matrix):
        counts = {
            suite: len(matrix[risk].get(suite, []))
            for suite in all_suites
        }
        total = sum(counts.values())
        covered_suites = sum(1 for count in counts.values() if count > 0)

        status = "covered"
        if covered_suites == 1 or total <= 2:
            status = "low"

        rows.append(
            {
                "risk": risk,
                "coverage": counts,
                "total_case_memberships": total,
                "covered_suites": covered_suites,
                "status": status,
                "case_ids": {
                    suite: matrix[risk].get(suite, [])
                    for suite in all_suites
                },
            }
        )

    return {
        "suite_totals": suite_totals,
        "risk_count": len(rows),
        "matrix": rows,
        "unclassified": dict(unclassified),
        "unclassified_count": sum(len(ids) for ids in unclassified.values()),
        "gap_summary": {
            "low": [row["risk"] for row in rows if row["status"] == "low"],
            "covered": [row["risk"] for row in rows if row["status"] == "covered"],
        },
    }


def print_matrix(report):
    print("AI Risk Coverage Matrix")
    print("-----------------------")
    print("Risk | Critical | Regression | Nightly | Total | Status")

    for row in report["matrix"]:
        coverage = row["coverage"]
        print(
            f"{row['risk']} | "
            f"{coverage.get('critical', 0)} | "
            f"{coverage.get('regression', 0)} | "
            f"{coverage.get('nightly', 0)} | "
            f"{row['total_case_memberships']} | "
            f"{row['status'].upper()}"
        )

    print("\nRisk Gap Summary")
    print("----------------")
    print(f"Low coverage: {', '.join(report['gap_summary']['low']) or 'none'}")
    print(f"Unclassified cases: {report['unclassified_count']}")


def main():
    args = parse_args()
    output_path = resolve_path(args.output)
    report = build_coverage_matrix()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print_matrix(report)
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
