# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. The current SUT is a Shopping RAG Assistant. The framework combines governed datasets, RAG observability, deterministic Python checks, semantic LLM-as-a-Judge evaluation, AI-risk metadata, CI/CD quality gates, operational telemetry and failure localization.

The evaluation routing model uses explicit `Oracle` metadata as the primary source of truth. When Oracle is missing/null/empty, `judge_routing.py` uses the manually reviewed case-ID mapping; `case_id`, `id`, and `ID` are supported field-name variants. If the ID is unknown too, routing safely defaults to `semantic_llm`. The Judge then evaluates PASS/FAIL and does not classify the Oracle type.

Across the reviewed suites the target routing is 61 deterministic and 44 semantic cases: Critical 6/4, Regression 7/8, Nightly 48/32. The next hardening layer is complete deterministic atomic assertion coverage and strict Oracle metadata validation.
