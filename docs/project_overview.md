# AI QE Lab — Current Project Overview

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. Its current System Under Test is a Shopping RAG Assistant. The surrounding framework demonstrates governed datasets, deterministic and semantic test oracles, observability, AI-risk coverage, CI/CD quality gates, operational telemetry and failure localization.

## Oracle routing

Evaluation cases declare how expected behavior should be evaluated through `Oracle = deterministic` or `Oracle = semantic_llm`. Explicit Oracle metadata is primary. If it is missing/null/empty, `judge_routing.py` uses the manually reviewed case-ID mapping, accepting `case_id`, `id`, and `ID` as field-name variants. If the ID is unknown too, routing safely defaults to `semantic_llm` and the LLM Judge evaluates PASS/FAIL.

The Judge does not decide whether an unknown case is deterministic or semantic. The routing layer makes that conservative fallback decision.

## Current reviewed inventory

- PR Critical: 6 deterministic / 4 semantic.
- Regression: 7 deterministic / 8 semantic.
- Nightly: 48 deterministic / 32 semantic.
- Total: 61 deterministic / 44 semantic across 105 reviewed cases.

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

## Next hardening layer

Complete deterministic atomic assertion coverage and stricter Oracle metadata validation across Critical, Regression and Nightly. Routing a case to deterministic evaluation is not sufficient by itself; Python must prove the expected facts/business rules with explicit assertions.
