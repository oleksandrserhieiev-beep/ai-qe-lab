# Oracle Routing Fallback

## Purpose

This document defines how the evaluator resolves the Oracle for an evaluation case when explicit Oracle metadata is present or absent.

## Resolution order

```text
Case
 -> explicit Oracle?
    -> deterministic -> deterministic route
    -> semantic_llm  -> semantic Judge
 -> missing/null/empty Oracle
    -> judge_routing.py fallback
    -> normalize identifier from case_id / id / ID
    -> known reviewed ID?
       -> yes: use mapped deterministic or semantic_llm route
       -> no: safe default semantic_llm
 -> execute selected oracle
 -> PASS / FAIL
```

## Key rules

1. Dataset/runtime `Oracle` is the primary source of truth.
2. `judge_routing.py` is a fallback registry, not a semantic classifier.
3. `case_id`, `id`, and `ID` are field-name variants for the same case identifier.
4. The LLM Judge never decides whether an unknown case is deterministic or semantic. If classification cannot be resolved, the routing layer selects `semantic_llm`; the Judge then decides semantic PASS/FAIL.
5. Unknown cases must not default to deterministic because deterministic evaluation requires a known formal assertion.
6. New governed cases should explicitly declare `Oracle = deterministic` or `Oracle = semantic_llm`.
7. Missing Oracle metadata may temporarily use fallback for backward compatibility.
8. Unsupported non-empty Oracle values should fail dataset validation rather than silently fall back.

## Why semantic is the safe final fallback

A semantic Judge can evaluate Query, Expected Behavior, Actual Answer and supplied evidence/context without a case-specific Python rule. A deterministic oracle requires a formal rule such as an expected ID, number/unit, threshold, boolean, range, schema, catalogue relation or structured constraint. If no such classification/rule is known, deterministic execution could create a false PASS.

Therefore:

```text
unknown Oracle + unknown mapped ID
 -> semantic_llm
 -> LLM Judge
 -> PASS / FAIL
```

The trade-off is an additional Judge call. The benefit is safe evaluation rather than silently accepting an unclassified case.

## Separation of responsibilities

```text
Expected Behavior = what correct behavior is
Oracle            = how correct behavior should be evaluated
Fallback routing   = how Oracle is safely resolved when metadata is absent
Judge              = semantic PASS/FAIL evaluation after semantic routing
```

## Next hardening step

Routing alone is not sufficient for deterministic cases. Each deterministic route must have explicit atomic assertions that prove its expected facts or business rules. Dataset validation should also enforce the supported Oracle vocabulary and progressively make Oracle mandatory for new cases.
