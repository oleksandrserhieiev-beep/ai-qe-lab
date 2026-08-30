from src.constraint_filter import extract_constraints
from src.constraint_validator import clarification_answer, validate_constraints


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
