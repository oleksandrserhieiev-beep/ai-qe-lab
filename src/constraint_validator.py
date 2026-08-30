import re


# Subjective terms that require a user-provided governed value before retrieval.
# Keep this policy explicit and deterministic for the POC; do not invent hidden
# thresholds such as "cheap == under $50".
SUBJECTIVE_PRICE_PATTERN = re.compile(
    r"\b(?:cheap|affordable|budget|inexpensive)\b",
    re.IGNORECASE,
)


def validate_constraints(query, constraints):
    """Classify unresolved input that must be clarified before retrieval."""
    unresolved = []

    if SUBJECTIVE_PRICE_PATTERN.search(query or "") and constraints.get("max_price") is None:
        unresolved.append(
            {
                "term": "subjective_price",
                "type": "ambiguous",
                "reason": "No governed maximum price was supplied.",
                "requested_field": "max_price",
            }
        )

    return {
        "is_resolved": not unresolved,
        "unresolved_constraints": unresolved,
    }


def clarification_answer(validation):
    requested_fields = {
        item.get("requested_field")
        for item in validation.get("unresolved_constraints", [])
    }

    if "max_price" in requested_fields:
        return "Please specify the maximum price you consider acceptable."

    return "Please clarify the unresolved requirement before I continue."
