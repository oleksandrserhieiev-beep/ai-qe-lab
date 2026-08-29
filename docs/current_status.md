# Current Evaluation Status

Current implementation includes: structured constraint filtering, FAISS Top-K retrieval, adaptive similarity-based context selection, Dataset/Oracle Validation in PR Critical/Regression/Nightly, reviewed Oracle routing with safe fallback, and structured deterministic assertions for all 61 deterministic cases (6 Critical, 7 Regression, 48 Nightly). The 44 semantic cases continue through the LLM Judge.

Next governance hardening is automatic fallback-mapper generation from validated approved datasets, followed by Jira-driven dataset lifecycle and Defect -> Regression automation.
