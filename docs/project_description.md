# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. Its current System Under Test is a Shopping RAG Assistant. The implemented RAG path is: constraint extraction -> structured product filtering where applicable -> embedding/FAISS semantic ranking -> Top-K retrieval candidates -> adaptive similarity-based context selection -> deterministic Context Builder -> Claude SUT.

The surrounding framework demonstrates governed datasets, Dataset/Oracle Validation, deterministic and semantic test oracles, observability, AI-risk coverage, CI/CD quality gates, operational telemetry and failure localization.

## Evaluation model

Evaluation cases carry expected behavior and an Oracle classification:

- `deterministic` — Python assertions for formal facts, IDs, numbers, booleans, thresholds, catalogue relations and structured constraints;
- `semantic_llm` — LLM-as-a-Judge evaluation where PASS/FAIL requires semantic interpretation.

The implemented reviewed inventory is 61 deterministic and 44 semantic cases across 105 cases. All 61 deterministic cases have structured atomic assertions.

## Dataset and Oracle safety

Before evaluation, `dataset_validator.py` validates IDs, Oracle values and deterministic assertion presence. Explicit Oracle metadata is primary. Missing/null/empty Oracle is recoverable and uses `judge_routing.py`; an unknown ID safely defaults to `semantic_llm`. Invalid non-empty Oracle metadata is a validation error and stops evaluation before model calls.

## Current lifecycle

```text
Controlled dataset
 -> Dataset Validation
 -> RAG retrieval candidates
 -> Adaptive Context Selection
 -> Context Builder
 -> Claude SUT
 -> Oracle resolution
 -> deterministic Python assertions or semantic LLM Judge
 -> metric aggregation
 -> AI-risk reporting
 -> quality gate
 -> CI evidence / defect localization
```

The next governance hardening step is automatic fallback-mapper generation from validated approved datasets, followed by Jira-driven dataset lifecycle and Defect -> Regression automation.
