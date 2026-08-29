# Oracle Routing Fallback

## Purpose

This document defines how the evaluator resolves the Oracle when explicit Oracle metadata is present or absent. Dataset Validation runs before active CI evaluation; runtime fallback remains a resilience mechanism.

## Resolution order

```text
Dataset Validation
 -> valid explicit Oracle?
    -> deterministic -> deterministic route
    -> semantic_llm  -> semantic Judge
 -> missing/null/empty Oracle
    -> warning
    -> judge_routing.py fallback
    -> normalize identifier from case_id / id / ID
    -> known reviewed ID?
       -> yes: use mapped deterministic or semantic_llm route
       -> no: safe default semantic_llm
 -> execute selected oracle
 -> PASS / FAIL
```

## Key rules

1. Dataset `Oracle` is the primary source of truth.
2. `judge_routing.py` is a fallback registry, not a semantic classifier.
3. `case_id`, `id`, and `ID` are field-name variants for the same case identifier.
4. The Judge never classifies an unknown case. Unknown routing safely selects `semantic_llm` before the Judge executes.
5. Unknown cases must not default to deterministic because deterministic evaluation requires a known formal rule.
6. Missing/null/empty Oracle is recoverable and emits a warning.
7. Invalid non-empty Oracle metadata fails Dataset Validation and does not silently fall back.
8. A deterministic Oracle must have non-empty deterministic assertions.

All 61 currently reviewed deterministic cases have structured atomic assertions.

## Why semantic is the safe final fallback

A semantic Judge can evaluate expected behavior against an answer/evidence without a case-specific formal rule. Deterministic execution requires an objective assertion. When neither explicit metadata nor a known mapping exists, semantic evaluation is safer than a possible deterministic false PASS.

## Separation of responsibilities

```text
Expected Behavior    = what correct behavior is
Dataset Validator    = whether the case metadata is safe to execute
Oracle               = how correct behavior is evaluated
Fallback routing     = how Oracle is recovered when metadata is absent
Assertion Engine     = formal deterministic PASS/FAIL
Judge                = semantic PASS/FAIL after semantic routing
```

## Next hardening step

The current manual fallback registry should become a **derived artifact generated/refreshed from validated approved dataset metadata**. That keeps the dataset authoritative and prevents mapper drift while preserving runtime resilience.
