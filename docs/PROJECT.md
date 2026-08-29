# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. The current SUT is a Shopping RAG Assistant with structured constraint filtering, FAISS Top-K retrieval, adaptive similarity-based context selection, deterministic context construction and Claude generation.

The QE framework combines governed datasets, Dataset/Oracle Validation, deterministic Python assertions, semantic LLM-as-a-Judge evaluation, AI-risk metadata, CI/CD quality gates, operational telemetry and failure localization.

Across the implemented reviewed suites there are 61 deterministic and 44 semantic cases: Critical 6/4, Regression 7/8, Nightly 48/32. All 61 deterministic cases have structured atomic assertions. Explicit Oracle metadata is primary; missing metadata can use the safe fallback mapper, while invalid non-empty Oracle metadata fails validation before evaluation.

Next governance hardening is automatic mapper generation from validated approved datasets, followed by Jira-driven dataset lifecycle and Defect -> Regression automation.
