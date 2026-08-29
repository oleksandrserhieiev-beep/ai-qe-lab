# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. Its current System Under Test is a Shopping RAG Assistant, while the surrounding framework demonstrates how AI behavior can be evaluated with governed datasets, deterministic and semantic test oracles, observability, AI-risk coverage, CI/CD quality gates, operational telemetry and failure localization.

## Evaluation model

Evaluation cases carry an expected behavior and an Oracle classification. The Oracle determines **how** the expected behavior is evaluated:

- `deterministic` — objective Python assertions for formal facts, IDs, numbers, booleans, thresholds, ranges, schemas, catalogue relations and structured constraints;
- `semantic_llm` — LLM-as-a-Judge evaluation where PASS/FAIL requires semantic interpretation of meaning or behavior.

Critical, Regression and Nightly have been manually reviewed with a target classification of 61 deterministic and 44 semantic cases across 105 cases.

## Oracle routing safety

Explicit Oracle metadata is the primary routing source. If Oracle is missing/null/empty, `judge_routing.py` falls back to the manually reviewed case-ID mapping, accepting `case_id`, `id`, and `ID` as field-name variants for the same identifier. If the ID is also unknown, routing safely defaults to `semantic_llm`.

The LLM Judge does not classify an unknown case as deterministic or semantic. It is invoked only after routing has selected the semantic path and then evaluates PASS/FAIL.

This conservative fallback prevents unknown cases from being incorrectly treated as deterministic without a formal assertion. The long-term governance target is to make Oracle explicit and validated for every newly authored case, leaving fallback only as compatibility/safety behavior.

## Current lifecycle

```text
Controlled dataset
 -> SUT execution
 -> retrieval/context evidence
 -> Oracle resolution
 -> deterministic Python assertions or semantic LLM Judge
 -> metric aggregation
 -> AI-risk reporting
 -> quality gate
 -> CI evidence / defect localization
```

The next evaluation hardening layer is complete deterministic atomic assertion coverage and strict Oracle metadata validation across Critical, Regression and Nightly.
