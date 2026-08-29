# AI QE Lab — Current Project Overview

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. Its current System Under Test is a Shopping RAG Assistant. The current RAG path uses structured product filtering, embedding/FAISS ranking, Top-K retrieval candidates, adaptive similarity-based context selection, deterministic context construction and Claude generation.

The surrounding QE framework provides governed datasets, Dataset/Oracle Validation, deterministic and semantic test oracles, observability, AI-risk coverage, CI/CD quality gates, operational telemetry and failure localization.

## Current evaluation inventory

- PR Critical: 6 deterministic / 4 semantic.
- Regression: 7 deterministic / 8 semantic.
- Nightly: 48 deterministic / 32 semantic.
- Total: 61 deterministic / 44 semantic across 105 reviewed cases.

All 61 deterministic cases have structured atomic assertions. All three active CI workflows validate their dataset before evaluation.

## Current lifecycle

```text
Controlled dataset
 -> Dataset Validation
 -> Constraint Extraction / Structured Filtering
 -> Embedding + FAISS Top-K candidates
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

Explicit Oracle metadata is primary. Missing/null/empty Oracle uses the reviewed fallback mapping in `judge_routing.py`; unknown IDs safely fall back to `semantic_llm`. Invalid non-empty Oracle metadata fails Dataset Validation.

## Next hardening layer

Automatically generate/refresh the fallback Oracle mapper from validated approved datasets, then extend the governed lifecycle toward Jira-driven requirements and Defect -> Regression automation.
