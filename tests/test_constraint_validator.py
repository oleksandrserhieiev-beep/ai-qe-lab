import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from constraint_filter import extract_constraints  # noqa: E402
from constraint_validator import clarification_answer, validate_constraints  # noqa: E402


def test_subjective_price_requires_clarification_without_max_price():
    query = "Find me a cheap black waterproof jacket"
    validation = validate_constraints(query, extract_constraints(query))

    assert validation["is_resolved"] is False
    assert validation["unresolved_constraints"][0]["requested_field"] == "max_price"
    assert clarification_answer(validation) == "Please specify the maximum price you consider acceptable."


def test_explicit_max_price_resolves_subjective_price():
    query = "Find me a cheap black waterproof jacket under $80"
    validation = validate_constraints(query, extract_constraints(query))

    assert validation["is_resolved"] is True
    assert validation["unresolved_constraints"] == []
