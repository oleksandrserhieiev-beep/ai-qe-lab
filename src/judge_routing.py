"""Manually reviewed deterministic/semantic oracle routing for AI evaluation suites."""

from deterministic_assertion_engine import evaluate_deterministic_assertions


CRITICAL_DETERMINISTIC = {
    "G-001", "G-002", "G-003", "G-032", "G-033", "G-034",
}
CRITICAL_SEMANTIC = {
    "G-004", "G-005", "G-031", "G-035",
}

REGRESSION_DETERMINISTIC = {
    "R-001", "R-007", "R-008", "R-010", "R-011", "R-013", "R-015",
}
REGRESSION_SEMANTIC = {
    "R-002", "R-003", "R-004", "R-005", "R-006", "R-009", "R-012", "R-014",
}

NIGHTLY_DETERMINISTIC_SEGMENTS = {
    "normal", "negative", "multi_constraint", "conflict", "paraphrase", "long_query",
}
NIGHTLY_SEMANTIC_SEGMENTS = {
    "ambiguous", "out_of_domain", "missing_info", "adversarial",
}


def _case_id(case):
    return str(case.get("case_id") or case.get("id") or case.get("ID") or "").strip().upper()


def _segment(case):
    return str(case.get("segment") or case.get("Segment") or "").strip().lower()


def _explicit_oracle(case):
    value = str(case.get("oracle") or case.get("Oracle") or "").strip().lower()
    if value == "deterministic":
        return {"route": "deterministic_only", "reason": "explicit dataset oracle classification"}
    if value in {"semantic_llm", "semantic", "llm"}:
        return {"route": "semantic_judge", "reason": "explicit dataset oracle classification"}
    return None


def choose_oracle_route(case):
    """Return explicit reviewed route; use ID/segment mappings as compatibility fallback."""
    explicit = _explicit_oracle(case)
    if explicit:
        return explicit

    case_id = _case_id(case)
    if case_id.startswith("G-"):
        if case_id in CRITICAL_DETERMINISTIC:
            return {"route": "deterministic_only", "reason": "manual Critical oracle classification"}
        if case_id in CRITICAL_SEMANTIC:
            return {"route": "semantic_judge", "reason": "manual Critical oracle classification"}

    if case_id.startswith("R-"):
        if case_id in REGRESSION_DETERMINISTIC:
            return {"route": "deterministic_only", "reason": "manual Regression oracle classification"}
        if case_id in REGRESSION_SEMANTIC:
            return {"route": "semantic_judge", "reason": "manual Regression oracle classification"}

    if case_id.startswith("E-"):
        segment = _segment(case)
        if segment in NIGHTLY_DETERMINISTIC_SEGMENTS:
            return {"route": "deterministic_only", "reason": f"manual Nightly segment classification: {segment}"}
        if segment in NIGHTLY_SEMANTIC_SEGMENTS:
            return {"route": "semantic_judge", "reason": f"manual Nightly segment classification: {segment}"}

    return {"route": "semantic_judge", "reason": "unclassified route defaults safely to semantic Judge"}


def build_evaluation_plan(case, retrieval_pass, constraint_retrieval=None):
    route = choose_oracle_route(case)
    constraint_retrieval = constraint_retrieval or {}
    constraint_applicable = bool(constraint_retrieval.get("applicable"))
    constraint_score = constraint_retrieval.get("constraint_match_score")
    constraint_pass = constraint_score == 100.0 if constraint_applicable else True

    atomic_result = None
    if route["route"] == "deterministic_only":
        atomic_result = evaluate_deterministic_assertions(
            case=case,
            retrieval_pass=retrieval_pass,
            constraint_retrieval=constraint_retrieval,
        )

    return {
        **route,
        "constraint_assertion": {
            "applicable": constraint_applicable,
            "passed": constraint_pass if constraint_applicable else None,
        },
        "deterministic_pass": atomic_result["overall_pass"] if atomic_result else bool(retrieval_pass and constraint_pass),
        "deterministic_signals": ["atomic_assertion_engine"] if atomic_result and atomic_result["structured_assertions_configured"] else (["legacy_deterministic_route"] if route["route"] == "deterministic_only" else []),
        "atomic_assertion_result": atomic_result,
        "factual_assertion": atomic_result,
    }


def deterministic_evaluation(retrieval_pass, constraint_retrieval=None, plan=None, case=None):
    """Evaluate deterministic route, using atomic assertions when configured."""
    constraint_retrieval = constraint_retrieval or {}
    plan = plan or {}
    case = case or {}

    engine_result = plan.get("atomic_assertion_result")
    if engine_result is None:
        engine_result = evaluate_deterministic_assertions(
            case=case,
            retrieval_pass=retrieval_pass,
            constraint_retrieval=constraint_retrieval,
        )

    overall = bool(engine_result["overall_pass"] and plan.get("deterministic_pass", True))
    return {
        **engine_result,
        "overall_pass": overall,
    }
