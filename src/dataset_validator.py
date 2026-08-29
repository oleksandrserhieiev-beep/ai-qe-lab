import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED_ORACLES = {"deterministic", "semantic_llm"}
PRODUCT_ID_RE = re.compile(r"^P-\d+$", re.IGNORECASE)


def load_cases(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("dataset root must be a JSON array")
    return data


def validate_dataset(path: Path):
    errors = []
    warnings = []
    seen_ids = set()

    try:
        cases = load_cases(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"{path}: {exc}"], warnings, 0

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

        expected_source = case.get("Expected Source")
        if expected_source is not None:
            source_value = str(expected_source).strip()
            if PRODUCT_ID_RE.fullmatch(source_value):
                errors.append(
                    f"{label}: Expected Source must identify a source document/dataset, not product ID {source_value!r}; "
                    "use Expected Product / Expected Retrieved Product for product identity"
                )

        oracle = case.get("Oracle")
        if oracle is None or (isinstance(oracle, str) and not oracle.strip()):
            warnings.append(
                f"{label}: Oracle missing; runtime routing will use the fallback mapper"
            )
            continue

        if not isinstance(oracle, str) or oracle.strip() not in ALLOWED_ORACLES:
            errors.append(
                f"{label}: invalid Oracle {oracle!r}; allowed values: deterministic, semantic_llm"
            )
            continue

        oracle = oracle.strip()
        if oracle == "deterministic":
            assertions = case.get("Deterministic Assertions")
            if not isinstance(assertions, list) or not assertions:
                errors.append(
                    f"{label}: deterministic Oracle requires non-empty Deterministic Assertions"
                )

    return errors, warnings, len(cases)


def main():
    parser = argparse.ArgumentParser(description="Validate AI QE dataset metadata contracts")
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
