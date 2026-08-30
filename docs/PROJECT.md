# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. The Shopping RAG Assistant is the reference System Under Test (SUT) used to prove the reusable QE framework; on a real project, the application pipeline would normally already exist and be owned by Development / AI Engineering.

The reference SUT includes deterministic constraint handling, structured filtering, FAISS Top-K retrieval, adaptive context selection, deterministic context construction and Claude generation. The QE framework around it combines governed datasets, Dataset/Oracle Validation, deterministic Python assertions, semantic LLM-as-a-Judge evaluation, AI-risk metadata, CI/CD quality gates, operational telemetry, failure localization and release validation.

Across the implemented reviewed PR Critical, Regression and Nightly suites there are 61 deterministic and 44 semantic cases: PR Critical 6/4, Regression 7/8 and Nightly 48/32. Explicit Oracle metadata in the governed datasets is primary. Missing metadata can use the reviewed fallback registry; invalid non-empty Oracle metadata fails validation before evaluation.

Current CI operating state:

```text
PR Critical        = automatic merge gate
Regression         = manual-only
Nightly            = manual-only
Release Validation = manual-only: Golden + broad Nightly + Release Quality Gate
```

The next major implementation phase is not more RAG/evaluator hardening. It is the upstream Agentic QE/Governance flow:

```text
Jira + Confluence
-> Requirements Review / Entry Gate
-> AI Risk Analysis
-> Test Design
-> Governance / Human Approval
-> Governed Dataset Update
-> existing Dataset Validation + Evaluation + CI framework
-> Defect / Regression / Release Evidence
```

Automatic generation/refresh of derived Oracle fallback mappings remains a useful governance hardening item, but the governed dataset remains the authoritative source and the primary roadmap milestone is requirements-driven Agentic QE integration.
