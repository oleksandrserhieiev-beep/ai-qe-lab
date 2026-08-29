import argparse
import json
import sys
from pathlib import Path

ALLOWED_ORACLES = {"deterministic", "semantic_llm"}
SEGMENT_ORACLE = {
    "normal": "deterministic",
    "ambiguous": "semantic_llm",
    "negative": "deterministic",
    "multi_constraint": "deterministic",
    "out_of_domain": "semantic_llm",
    "missing_info": "semantic_llm",
    "conflict": "deterministic",
    "adversarial": "semantic_llm",
    "paraphrase": "deterministic",
    "long_query": "deterministic",
}


def load_cases(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("dataset root must be a JSON array")
    return data


def _nightly_assertions(path: Path):
    if path.name != "evaluation_dataset.json":
        return {}
    assertion_file = path.parent / "evaluation_assertion_metadata.json"
    if not assertion_file.exists():
        return {}
    with assertion_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolved_oracle(case):
    oracle = case.get("Oracle")
    if isinstance(oracle, str) and oracle.strip():
        return oracle.strip()
    segment = str(case.get("Segment") or "").strip().lower()
    return SEGMENT_ORACLE.get(segment)


def validate_dataset(path: Path):
    errors = []
    warnings = []
    seen_ids = set()

    try:
        cases = load_cases(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"{path}: {exc}"], warnings, 0

    assertion_metadata = _nightly_assertions(path)

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"case #{index}: case must be a JSON object")
            continue

        case_id = str(case.get("ID") or case.get("id") or case.get("case_id") or "").strip()
        label = case_id or f"case #{index}"

        if not case_id:
            errors.append(f"{label}: missing ID")
        elif case_id in seen_ids:
            errors.append(f"{label}: duplicate ID")
        else:
            seen_ids.add(case_id)

        oracle = _resolved_oracle(case)
        if oracle is None:
            warnings.append(f"{label}: Oracle missing and Segment has no governed routing rule")
            continue

        if oracle not in ALLOWED_ORACLES:
            errors.append(
                f"{label}: invalid Oracle {oracle!r}; allowed values: deterministic, semantic_llm"
            )
            continue

        if oracle == "deterministic":
            assertions = case.get("Deterministic Assertions")
            if not isinstance(assertions, list) or not assertions:
                assertions = assertion_metadata.get(case_id, [])
            if not isinstance(assertions, list) or not assertions:
                errors.append(
                    f"{label}: deterministic Oracle requires non-empty Deterministic Assertions"
                )

    return errors, warnings, len(cases)


def main():
    parser = argparse.ArgumentParser(description="Validate AI QE dataset Oracle metadata")
    parser.add_argument("datasets", nargs="+", help="Dataset JSON files to validate")
    args = parser.parse_args()

    total_errors = 0
    for dataset in args.datasets:
        path = Path(dataset)
        errors, warnings, count = validate_dataset(path)
        print(f"\nDataset: {path} ({count} cases)")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        if errors:
            print(f"Validation: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        else:
            print(f"Validation: PASS ({len(warnings)} warning(s))")
        total_errors += len(errors)

    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
