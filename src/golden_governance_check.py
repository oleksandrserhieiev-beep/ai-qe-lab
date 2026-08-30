import os
import re
import sys


REQUIRED_FIELDS = {
    "Golden Change Reason": r"(?im)^\s*Golden Change Reason\s*:\s*(.+?)\s*$",
    "Source of Truth": r"(?im)^\s*Source of Truth\s*:\s*(.+?)\s*$",
}

INVALID_VALUES = {"n/a", "na", "none", "-", "tbd", "todo"}


def _extract(body: str, pattern: str):
    match = re.search(pattern, body or "")
    if not match:
        return None
    value = match.group(1).strip()
    if not value or value.lower() in INVALID_VALUES:
        return None
    return value


def main() -> int:
    body = os.getenv("PR_BODY", "")
    missing = []
    values = {}

    for field, pattern in REQUIRED_FIELDS.items():
        value = _extract(body, pattern)
        if value is None:
            missing.append(field)
        else:
            values[field] = value

    print("Golden Dataset Governance Check")
    print("--------------------------------")

    if missing:
        print("FAIL")
        print("Golden dataset changes require explicit governance metadata in the PR body.")
        print("Missing or empty fields:")
        for field in missing:
            print(f"- {field}")
        print("\nRequired PR body format:")
        print("Golden Change Reason: <approved reason for changing canonical expected behavior>")
        print("Source of Truth: <requirement, business decision, specification, or defect/reference>")
        print("\nA failing evaluation by itself is not a valid reason to rewrite Golden expectations.")
        return 1

    print("PASS")
    for field, value in values.items():
        print(f"{field}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
