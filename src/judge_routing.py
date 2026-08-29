"""Risk-based routing for deterministic checks and semantic LLM judging."""

SEMANTIC_RISKS = {
    "hallucination",
    "groundedness",
    "policy_grounding",
    "prompt_injection",
    "sensitive_data_handling",
    "conflicting_data",
    "negative_behavior",
    "out_of_domain_abstention",
    "missing_information",
    "ambiguity",
    "robustness",
}

DETERMINISTIC_RISKS = {
    "retrieval_quality",
    "constraint_adherence",
}


def normalize_risks(risk):
    if risk is None:
        return []
    if isinstance(risk, str):
        return [risk]
    return [item for item in risk if item]


def choose_judge_route(risk, retrieval_pass, constraint_retrieval=None):
    """Return whether semantic Judge evaluation is required for this case.

    A case may skip the LLM Judge only when all declared risks are covered by
    deterministic retrieval/constraint checks and those checks are applicable.
    Unknown/unclassified risks remain conservative and use the semantic Judge.
    """
    risks = set(normalize_risks(risk))
    constraint_retrieval = constraint_retrieval or {}

    if not risks:
        return {
            "route": "semantic_judge",
            "reason": "unclassified risk: preserve semantic evaluation",
        }

    if risks & SEMANTIC_RISKS:
        return {
            "route": "semantic_judge",
            "reason": "semantic risk requires model judgment",
        }

    if risks <= DETERMINISTIC_RISKS:
        constraint_required = "constraint_adherence" in risks
        constraint_applicable = bool(constraint_retrieval.get("applicable"))

        if constraint_required and not constraint_applicable:
            return {
                "route": "semantic_judge",
                "reason": "constraint risk is not deterministically measurable for this case",
            }

        return {
            "route": "deterministic_only",
            "reason": "declared risks are fully covered by deterministic checks",
        }

    return {
        "route": "semantic_judge",
        "reason": "risk is not proven deterministic: preserve semantic evaluation",
    }


def deterministic_evaluation(retrieval_pass, constraint_retrieval=None):
    constraint_retrieval = constraint_retrieval or {}
    constraint_applicable = bool(constraint_retrieval.get("applicable"))
    constraint_score = constraint_retrieval.get("constraint_match_score")
    constraint_pass = (
        constraint_score == 100.0 if constraint_applicable else True
    )

    return {
        "retrieval_pass": bool(retrieval_pass),
        "constraint_adherence": bool(constraint_pass),
        "overall_pass": bool(retrieval_pass and constraint_pass),
    }
