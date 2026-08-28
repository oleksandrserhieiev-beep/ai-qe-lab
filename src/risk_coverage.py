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

NIGHTLY_RISK_METADATA = (
    BASE_DIR / "datasets" / "evaluation_risk_metadata.json"
)

# Compatibility aliases for EXPLICIT Risk metadata only.
# Segment is a test-design dimension and must not be silently treated as AI Risk.
CANONICAL_RISK_MAP = {
    "retrieval_quality": ["retrieval_quality"],
    "constraint_adherence": ["constraint_adherence"],
    "policy_grounding": ["policy_grounding"],
    "sensitive_data_handling": ["sensitive_data_handling"],
    "out_of_domain_abstention": ["out_of_domain_abstention"],
    "robustness": ["robustness"],
    "negative_behavior": ["negative_behavior"],
    "hallucination": ["hallucination"],
    "prompt_injection": ["prompt_injection"],
    "groundedness": ["groundedness"],
    "conflicting_data": ["conflicting_data"],
    "missing_information": ["missing_information"],
    "ambiguity": ["ambiguity"],
    # Historical aliases used by existing datasets.
    "retrieval_and_constraints": ["retrieval_quality", "constraint_adherence"],
    "privacy_and_safety": ["sensitive_data_handling"],
    "out_of_domain": ["out_of_domain_abstention"],
    "policy_constraint": ["policy_grounding", "constraint_adherence"],
    "hallucination_and_policy": ["hallucination", "policy_grounding"],
    "multi_constraint": ["retrieval_quality", "constraint_adherence"],
    "long_query_and_multi_constraint": [
        "robustness",
        "retrieval_quality",
        "constraint_adherence",
    ],
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


def canonicalize_risks(value):
    canonical = []

    for risk in normalize_list(value):
        mapped = CANONICAL_RISK_MAP.get(risk, [risk])
        for item in mapped:
            if item not in canonical:
                canonical.append(item)

    return canonical


def canonicalize_case_risks(case):
    """Return canonical risks from explicit Risk metadata only.

    Segment is intentionally ignored. A segment describes test design/behavioral
    shape (for example long_query or paraphrase) and is not automatically an
    AI risk. Missing Risk metadata is reported as unclassified instead of being
    inferred heuristically.
    """
    return canonicalize_risks(case.get("Risk"))


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_nightly_risk_metadata():
    return load_dataset(NIGHTLY_RISK_METADATA)


def build_coverage_matrix(suites=None):
    suites = suites or SUITES
    matrix = defaultdict(lambda: defaultdict(list))
    unclassified = defaultdict(list)
    suite_totals = {}
    nightly_risk_metadata = load_nightly_risk_metadata()

    for suite_name, dataset_path in suites.items():
        cases = load_dataset(dataset_path)
        suite_totals[suite_name] = len(cases)

        for case in cases:
            case_id = case.get("ID", "UNKNOWN")

            if suite_name == "nightly":
                risks = canonicalize_risks(
                    nightly_risk_metadata.get(case_id)
                )
            else:
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
        total_memberships = sum(counts.values())
        covered_suites = sum(1 for count in counts.values() if count > 0)

        if covered_suites == len(all_suites):
            status = "full"
        elif covered_suites == 2:
            status = "partial"
        else:
            status = "single_suite"

        rows.append(
            {
                "risk": risk,
                "coverage": counts,
                "total_case_memberships": total_memberships,
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
            "full": [row["risk"] for row in rows if row["status"] == "full"],
            "partial": [row["risk"] for row in rows if row["status"] == "partial"],
            "single_suite": [
                row["risk"] for row in rows if row["status"] == "single_suite"
            ],
        },
    }


def print_matrix(report):
    print("AI Risk Coverage Matrix")
    print("-----------------------")

    risk_width = max(
        len("Risk"),
        *(len(row["risk"]) for row in report["matrix"]),
    )

    header = (
        f"{'Risk':<{risk_width}} | "
        f"{'Critical':>8} | "
        f"{'Regression':>10} | "
        f"{'Nightly':>7} | "
        f"{'Case memberships':>16} | "
        f"{'Status':<12}"
    )
    print(header)
    print("-" * len(header))

    for row in report["matrix"]:
        coverage = row["coverage"]
        print(
            f"{row['risk']:<{risk_width}} | "
            f"{coverage.get('critical', 0):>8} | "
            f"{coverage.get('regression', 0):>10} | "
            f"{coverage.get('nightly', 0):>7} | "
            f"{row['total_case_memberships']:>16} | "
            f"{row['status'].upper():<12}"
        )

    print("\nRisk Coverage Gaps")
    print("------------------")
    print(f"Full (3 suites): {', '.join(report['gap_summary']['full']) or 'none'}")
    print(f"Partial (2 suites): {', '.join(report['gap_summary']['partial']) or 'none'}")
    print(
        "Single-suite only: "
        f"{', '.join(report['gap_summary']['single_suite']) or 'none'}"
    )
    print(f"Unclassified cases: {report['unclassified_count']}")

    for suite, case_ids in sorted(report.get("unclassified", {}).items()):
        if case_ids:
            print(f"  {suite}: {len(case_ids)}")


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
