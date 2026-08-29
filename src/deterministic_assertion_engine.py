"""Deterministic atomic assertions for AI/RAG evaluation.

The engine evaluates formal expectations without an LLM Judge and reports the
first pipeline layer at which an expected fact is lost: retrieval, context, or
generation.
"""

import re

from data_loader import load_products
from retrieval_metrics import active_constraints, product_constraint_match_score


SUPPORTED_STAGES = {"retrieval", "context", "generation"}
PRODUCT_ID_PATTERN = re.compile(r"\bP-\d+\b", re.IGNORECASE)


def _text_for_stage(case, stage):
    if stage == "context":
        return str(case.get("retrieved_context") or case.get("final_context") or "")
    if stage == "generation":
        return str(case.get("actual_answer") or "")
    return ""


def _retrieved_ids(case):
    return [str(item.get("id", "")) for item in case.get("retrieval", [])]


def _answer_product_ids(case):
    return [value.upper() for value in PRODUCT_ID_PATTERN.findall(str(case.get("actual_answer") or ""))]


def _retrieval_products_by_id(case):
    products = {}
    for item in case.get("retrieval", []):
        if item.get("type") != "product":
            continue
        product_id = str(item.get("id", "")).upper()
        if product_id:
            products[product_id] = item.get("metadata", {})
    return products


def _evaluate_assertion(case, assertion, stage, constraint_retrieval=None):
    assertion_type = str(assertion.get("type", "")).strip().lower()
    assertion_id = assertion.get("id") or f"{stage}:{assertion_type}"
    constraint_retrieval = constraint_retrieval or {}

    if stage not in SUPPORTED_STAGES:
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": False, "expected": assertion, "actual": None, "reason": f"unsupported assertion stage: {stage}"}

    if assertion_type == "retrieved_id":
        expected = str(assertion.get("value", ""))
        actual = _retrieved_ids(case)
        passed = expected in actual
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": passed, "expected": expected, "actual": actual, "reason": "expected ID retrieved" if passed else "expected ID not retrieved"}

    if assertion_type == "no_constraint_match":
        matching_products = int(constraint_retrieval.get("matching_products") or 0)
        passed = matching_products == 0
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": passed, "expected": 0, "actual": matching_products, "reason": "no retrieved product satisfies all constraints" if passed else "unexpected matching product retrieved"}

    if assertion_type == "answer_products_satisfy_constraints":
        product_ids = _answer_product_ids(case)
        retrieved_products = _retrieval_products_by_id(case)
        constraints = active_constraints(str(case.get("query") or ""))
        scores = {pid: product_constraint_match_score(retrieved_products[pid], constraints) for pid in product_ids if pid in retrieved_products}
        passed = bool(product_ids) and len(scores) == len(product_ids) and all(score == 100.0 for score in scores.values())
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": passed, "expected": constraints, "actual": {"answer_product_ids": product_ids, "constraint_scores": scores}, "reason": "all recommended products satisfy query constraints" if passed else "answer contains an unknown or constraint-violating product"}

    if assertion_type == "catalogue_min_price_product":
        products = load_products()
        priced = [product for product in products if product.get("price") is not None]
        minimum_price = min(float(product["price"]) for product in priced)
        expected_ids = sorted(str(product.get("product_id")) for product in priced if float(product["price"]) == minimum_price)
        actual_ids = _answer_product_ids(case)
        passed = any(product_id.upper() in {value.upper() for value in expected_ids} for product_id in actual_ids)
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": passed, "expected": {"minimum_price": minimum_price, "product_ids": expected_ids}, "actual": actual_ids, "reason": "answer recommends a catalogue minimum-price product" if passed else "answer does not recommend a catalogue minimum-price product"}

    text = _text_for_stage(case, stage)

    if assertion_type == "contains":
        expected = str(assertion.get("value", ""))
        case_sensitive = bool(assertion.get("case_sensitive", False))
        haystack = text if case_sensitive else text.lower()
        needle = expected if case_sensitive else expected.lower()
        passed = bool(needle) and needle in haystack
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": passed, "expected": expected, "actual": text, "reason": "expected value present" if passed else "expected value missing"}

    if assertion_type == "regex":
        pattern = str(assertion.get("pattern", ""))
        flags = 0 if assertion.get("case_sensitive") else re.IGNORECASE
        match = re.search(pattern, text, flags) if pattern else None
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": bool(match), "expected": pattern, "actual": match.group(0) if match else None, "reason": "expected pattern matched" if match else "expected pattern not matched"}

    if assertion_type == "not_regex":
        pattern = str(assertion.get("pattern", ""))
        flags = 0 if assertion.get("case_sensitive") else re.IGNORECASE
        match = re.search(pattern, text, flags) if pattern else None
        return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": not bool(match), "expected": f"must not match: {pattern}", "actual": match.group(0) if match else None, "reason": "forbidden pattern absent" if not match else "forbidden pattern present"}

    return {"id": assertion_id, "stage": stage, "type": assertion_type, "passed": False, "expected": assertion, "actual": None, "reason": f"unsupported assertion type: {assertion_type}"}


def evaluate_deterministic_assertions(case, retrieval_pass, constraint_retrieval=None):
    """Evaluate structured assertions and return layer-level evidence."""
    constraint_retrieval = constraint_retrieval or {}
    configured = case.get("deterministic_assertions") or case.get("Deterministic Assertions") or []

    expects_no_match = any(str(assertion.get("type", "")).strip().lower() == "no_constraint_match" for assertion in configured)
    constraint_applicable = bool(constraint_retrieval.get("applicable"))
    constraint_score = constraint_retrieval.get("constraint_match_score")
    if expects_no_match:
        constraint_pass = int(constraint_retrieval.get("matching_products") or 0) == 0
    else:
        constraint_pass = constraint_score == 100.0 if constraint_applicable else True

    results = []
    for assertion in configured:
        stages = assertion.get("stages") or [assertion.get("stage", "generation")]
        for stage in stages:
            results.append(_evaluate_assertion(case, assertion, str(stage).strip().lower(), constraint_retrieval=constraint_retrieval))

    stage_results = {}
    for stage in SUPPORTED_STAGES:
        stage_assertions = [item for item in results if item["stage"] == stage]
        if stage == "retrieval":
            base_pass = bool(retrieval_pass and constraint_pass)
            passed = base_pass and all(item["passed"] for item in stage_assertions)
        elif stage_assertions:
            passed = all(item["passed"] for item in stage_assertions)
        else:
            passed = None
        stage_results[stage] = {"passed": passed, "assertions": stage_assertions}

    explicit_assertions_pass = all(item["passed"] for item in results) if results else True
    overall_pass = bool(retrieval_pass and constraint_pass and explicit_assertions_pass)

    first_failure_layer = None
    for stage in ("retrieval", "context", "generation"):
        if stage_results[stage]["passed"] is False:
            first_failure_layer = stage
            break

    return {
        "overall_pass": overall_pass,
        "retrieval_pass": bool(retrieval_pass),
        "constraint_adherence": bool(constraint_pass),
        "structured_assertions_configured": bool(configured),
        "assertion_count": len(results),
        "passed_assertions": sum(item["passed"] for item in results),
        "failed_assertions": sum(not item["passed"] for item in results),
        "layers": stage_results,
        "first_failure_layer": first_failure_layer,
    }
