# AI QE Lab — Project Description

AI QE Lab demonstrates practical Quality Engineering for AI-enabled systems using a Shopping RAG Assistant as the current SUT. The current RAG flow includes structured filtering, FAISS Top-K retrieval candidates, adaptive similarity-based Context-K selection, deterministic context construction and Claude generation.

Evaluation combines governed datasets, Dataset/Oracle Validation, deterministic Python oracles, semantic LLM-as-a-Judge evaluation, AI-risk metadata, observability, CI/CD gates, telemetry and failure localization.

The implemented reviewed inventory is 6/4 deterministic/semantic for PR Critical, 7/8 for Regression, and 48/32 for Nightly: 61 deterministic and 44 semantic routes across 105 cases. All 61 deterministic cases have structured atomic assertions.

Explicit Oracle metadata is primary; missing/null/empty metadata uses the reviewed fallback in `judge_routing.py`; unknown IDs safely default to `semantic_llm`; invalid non-empty Oracle metadata fails Dataset Validation.

Next governance hardening: derive the fallback Oracle mapper automatically from validated approved datasets, then extend the lifecycle toward Jira and Defect -> Regression automation.
