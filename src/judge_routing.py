"""Case-level routing for deterministic checks and semantic LLM judging."""

import re


BLOCKING_SEMANTIC_RISKS = {
    "hallucination",
    "groundedness",
    "prompt_injection",
    "sensitive_data_handling",
    "privacy_and_safety",
    "conflicting_data",
    "negative_behavior",
    "out_of_domain_abstention",
    "out_of_domain",
    "missing_information",
    "ambiguity",
    "hallucination_and_policy",
    "policy_constraint",
}

DETERMINISTIC_PRODUCT_RISKS = {
    "retrieval_quality",
    "constraint_adherence",
    "retrieval_and_constraints",
    "multi_constraint",
    "long_query_and_multi_constraint",
}

EXACT_FACT_COMPATIBLE_RISKS = {
    "factual_correctness",
    "policy_grounding",
    "robustness",
    "groundedness",
    "retrieval_quality",
}

BEHAVIORAL_MARKERS = {
    "must ",
    "do not ",
    "don't ",
    "ask ",
    "abstain",
    "refuse",
    "invent",
    "ignore ",
    "unsupported",
    "according to",
    "answer using",
    "recommend only",
    "surface the uncertainty",
    "clearly state",
}


def normalize_risks(risk):
    if risk is None:
        return []
    if isinstance(risk, str):
        return [risk]
    return [item for item in risk if item]


def _normalize_text(value):
    text = str(value or "").lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def _simple_fact_parts(expected_behavior):
    """Return deterministic literal facts or [] when the oracle is behavioral."""
    expected = _normalize_text(expected_behavior)
    if not expected:
        return []
    if "<=" in expected or ">=" in expected or "<" in expected or ">" in expected:
        return []
    if any(marker in expected for marker in BEHAVIORAL_MARKERS):
        return []
    if expected.startswith("yes") or expected.startswith("no;") or expected.startswith("no "):
        return []

    parts = [part.strip(" .") for part in expected.split(";") if part.strip(" .")]
    if not parts:
        return []

    factual = []
    for part in parts:
        has_number = bool(re.search(r"\d", part))
        has_product_id = bool(re.search(r"\bp-\d+\b", part))
        has_boolean_fact = bool(re.search(r"\b(true|false)\b", part))
        has_key_value = "=" in part
        if not (has_number or has_product_id or has_boolean_fact or has_key_value):
            return []
        factual.append(part)
    return factual


def _fact_part_matches(part, actual_answer):
    actual = _normalize_text(actual_answer)
    part = _normalize_text(part)
    actual_compact = actual.replace(",", "")
    part_compact = part.replace(",", "")

    if part_compact in actual_compact:
        return True

    key_value = re.fullmatch(r"([a-z_ ]+)\s*=\s*([^;]+)", part_compact)
    if key_value:
        key = key_value.group(1).strip()
        value = key_value.group(2).strip()
        return bool(
            re.search(
                rf"\b{re.escape(key)}\b\s*(?:=|:|is)?\s*{re.escape(value)}\b",
                actual_compact,
            )
        )

    expected_numbers = re.findall(r"\d+(?:\.\d+)?", part_compact)
    if expected_numbers and all(number in actual_compact for number in expected_numbers):
        units = [
            unit
            for unit in ("calendar days", "business days", "months", "usd")
            if unit in part_compact
        ]
        if all(unit in actual_compact for unit in units):
            if "$" in part_compact and "$" not in actual_compact:
                return False
            return True
    return False


def evaluate_factual_oracle(expected_behavior, actual_answer):
    parts = _simple_fact_parts(expected_behavior)
    if not parts:
        return {"applicable": False, "passed": None, "facts": []}
    passed = all(_fact_part_matches(part, actual_answer) for part in parts)
    return {"applicable": True, "passed": passed, "facts": parts}


def _expected_product_match(case):
    expected_product = case.get("expected_product") or case.get("expected_retrieved_product")
    if not expected_product:
        expected_behavior = _normalize_text(case.get("expected_facts_behavior"))
        match = re.search(r"\bp-\d+\b", expected_behavior)
        expected_product = match.group(0).upper() if match else None
    if not expected_product:
        return {"applicable": False, "passed": None}

    answer = _normalize_text(case.get("actual_answer"))
    expected = _normalize_text(expected_product)
    if expected in answer:
        return {"applicable": True, "passed": True}

    for item in case.get("retrieval", []):
        if _normalize_text(item.get("id")) != expected:
            continue
        metadata = item.get("metadata") or {}
        name = _normalize_text(metadata.get("name") or metadata.get("title"))
        if name and name in answer:
            return {"applicable": True, "passed": True}

    return {"applicable": True, "passed": False}


def build_evaluation_plan(case, retrieval_pass, constraint_retrieval=None):
    """Build a per-case plan from objective assertions, not Risk alone."""
    risks = set(normalize_risks(case.get("risk")))
    constraint_retrieval = constraint_retrieval or {}
    factual = evaluate_factual_oracle(
        case.get("expected_facts_behavior", ""),
        case.get("actual_answer", ""),
    )
    product = _expected_product_match(case)

    exact_fact_case = (
        factual["applicable"]
        and bool(risks)
        and risks <= (EXACT_FACT_COMPATIBLE_RISKS | DETERMINISTIC_PRODUCT_RISKS)
    )

    if risks & BLOCKING_SEMANTIC_RISKS and not exact_fact_case:
        return {
            "route": "semantic_judge",
            "reason": "case contains behavior/safety/semantic risk requiring model judgment",
            "factual_assertion": factual,
            "product_assertion": product,
        }

    constraint_applicable = bool(constraint_retrieval.get("applicable"))
    constraint_score = constraint_retrieval.get("constraint_match_score")
    constraint_pass = constraint_score == 100.0 if constraint_applicable else None

    deterministic_signals = []
    deterministic_passes = [bool(retrieval_pass)]

    if factual["applicable"]:
        deterministic_signals.append("factual_oracle")
        deterministic_passes.append(bool(factual["passed"]))

    if product["applicable"]:
        deterministic_signals.append("expected_product")
        deterministic_passes.append(bool(product["passed"]))

    product_or_constraint_risk = bool(risks & DETERMINISTIC_PRODUCT_RISKS)
    if constraint_applicable and product_or_constraint_risk:
        deterministic_signals.append("structured_constraints")
        deterministic_passes.append(bool(constraint_pass))

    deterministic_risk_set = EXACT_FACT_COMPATIBLE_RISKS | DETERMINISTIC_PRODUCT_RISKS
    deterministically_coverable = bool(risks) and risks <= deterministic_risk_set

    if deterministic_signals and deterministically_coverable:
        return {
            "route": "deterministic_only",
            "reason": "case oracle is fully represented by deterministic assertions",
            "factual_assertion": factual,
            "product_assertion": product,
            "constraint_assertion": {
                "applicable": constraint_applicable,
                "passed": constraint_pass,
            },
            "deterministic_signals": deterministic_signals,
            "deterministic_pass": all(deterministic_passes),
        }

    return {
        "route": "semantic_judge",
        "reason": "deterministic assertions do not fully represent expected behavior",
        "factual_assertion": factual,
        "product_assertion": product,
    }


def deterministic_evaluation(retrieval_pass, constraint_retrieval=None, plan=None):
    constraint_retrieval = constraint_retrieval or {}
    plan = plan or {}
    constraint_applicable = bool(constraint_retrieval.get("applicable"))
    constraint_score = constraint_retrieval.get("constraint_match_score")
    constraint_pass = constraint_score == 100.0 if constraint_applicable else True
    overall = bool(retrieval_pass and constraint_pass and plan.get("deterministic_pass", True))

    return {
        "retrieval_pass": bool(retrieval_pass),
        "constraint_adherence": bool(constraint_pass),
        "overall_pass": overall,
    }
