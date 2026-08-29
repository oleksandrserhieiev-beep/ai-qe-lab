"""Deterministic atomic assertions for AI/RAG evaluation.

The engine evaluates formal expectations without an LLM Judge and reports the
first pipeline layer at which an expected fact is lost: retrieval, context, or
generation.
"""

import re


SUPPORTED_STAGES = {"retrieval", "context", "generation"}


def _text_for_stage(case, stage):
    if stage == "context":
        return str(case.get("retrieved_context") or case.get("final_context") or "")
    if stage == "generation":
        return str(case.get("actual_answer") or "")
    return ""


def _retrieved_ids(case):
    return [str(item.get("id", "")) for item in case.get("retrieval", [])]


def _evaluate_assertion(case, assertion, stage):
    assertion_type = str(assertion.get("type", "")).strip().lower()
    assertion_id = assertion.get("id") or f"{stage}:{assertion_type}"

    if stage not in SUPPORTED_STAGES:
        return {
            "id": assertion_id,
            "stage": stage,
            "type": assertion_type,
            "passed": False,
            "expected": assertion,
            "actual": None,
            "reason": f"unsupported assertion stage: {stage}",
        }

    if assertion_type == "retrieved_id":
        expected = str(assertion.get("value", ""))
        actual = _retrieved_ids(case)
        passed = expected in actual
        return {
            "id": assertion_id,
            "stage": stage,
            "type": assertion_type,
            "passed": passed,
            "expected": expected,
            "actual": actual,
            "reason": "expected ID retrieved" if passed else "expected ID not retrieved",
        }

    text = _text_for_stage(case, stage)

    if assertion_type == "contains":
        expected = str(assertion.get("value", ""))
        case_sensitive = bool(assertion.get("case_sensitive", False))
        haystack = text if case_sensitive else text.lower()
        needle = expected if case_sensitive else expected.lower()
        passed = bool(needle) and needle in haystack
        return {
            "id": assertion_id,
            "stage": stage,
            "type": assertion_type,
            "passed": passed,
            "expected": expected,
            "actual": text,
            "reason": "expected value present" if passed else "expected value missing",
        }

    if assertion_type == "regex":
        pattern = str(assertion.get("pattern", ""))
        flags = 0 if assertion.get("case_sensitive") else re.IGNORECASE
        match = re.search(pattern, text, flags) if pattern else None
        return {
            "id": assertion_id,
            "stage": stage,
            "type": assertion_type,
            "passed": bool(match),
            "expected": pattern,
            "actual": match.group(0) if match else None,
            "reason": "expected pattern matched" if match else "expected pattern not matched",
        }

    if assertion_type == "not_regex":
        pattern = str(assertion.get("pattern", ""))
        flags = 0 if assertion.get("case_sensitive") else re.IGNORECASE
        match = re.search(pattern, text, flags) if pattern else None
        return {
            "id": assertion_id,
            "stage": stage,
            "type": assertion_type,
            "passed": not bool(match),
            "expected": f"must not match: {pattern}",
            "actual": match.group(0) if match else None,
            "reason": "forbidden pattern absent" if not match else "forbidden pattern present",
        }

    return {
        "id": assertion_id,
        "stage": stage,
        "type": assertion_type,
        "passed": False,
        "expected": assertion,
        "actual": None,
        "reason": f"unsupported assertion type: {assertion_type}",
    }


def evaluate_deterministic_assertions(case, retrieval_pass, constraint_retrieval=None):
    """Evaluate structured assertions and return layer-level evidence.

    Existing retrieval and constraint metrics remain part of the deterministic
    result. Explicit atomic assertions extend coverage into context and final
    generation. Cases without structured assertions retain legacy behavior so
    older datasets can be migrated incrementally.
    """
    constraint_retrieval = constraint_retrieval or {}
    constraint_applicable = bool(constraint_retrieval.get("applicable"))
    constraint_score = constraint_retrieval.get("constraint_match_score")
    constraint_pass = constraint_score == 100.0 if constraint_applicable else True

    configured = case.get("deterministic_assertions") or case.get("Deterministic Assertions") or []
    results = []
    for assertion in configured:
        stages = assertion.get("stages") or [assertion.get("stage", "generation")]
        for stage in stages:
            results.append(_evaluate_assertion(case, assertion, str(stage).strip().lower()))

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
        stage_results[stage] = {
            "passed": passed,
            "assertions": stage_assertions,
        }

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
