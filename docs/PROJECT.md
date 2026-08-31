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

The upstream Agentic QE phase has now started with the **Requirements Review Agent** as the first controlled slice:

```text
Manual Jira batch
→ Python deterministic eligibility gate
→ minimal semantic requirement payload
→ content fingerprint / cache decision
→ Claude Requirements Review when needed
→ READY / NEEDS_CLARIFICATION
→ batch quality + cache + token + cost evidence
```

Unchanged eligible requirements can reuse their structured review with zero LLM calls. Changes to Summary, Description, Acceptance Criteria or Components invalidate the fingerprint; `force_review=true` is an explicit manual bypass for a controlled fresh review.

The next architectural progression is:

```text
Jira Requirement
→ Requirements Review / Entry Gate
→ Risk Analysis
→ targeted cross-document retrieval/RAG where needed
→ Test Generation
→ Governance / Human Approval
→ Governed Dataset Update
→ existing Dataset Validation + Evaluation + CI framework
→ Defect / Regression / Release Evidence
```

Requirements Review intentionally evaluates the Jira requirement itself; external retrieval should not hide missing requirement content. Risk Analysis is the first planned stage where architecture, business rules, policies, related specifications and historical defects can become evidence through bounded retrieval.

Automatic generation/refresh of derived Oracle fallback mappings remains a useful governance hardening item, but the governed dataset remains the authoritative source. The primary roadmap milestone is requirements-driven Agentic QE integration connected to the already implemented evaluation/governance framework.

See `docs/agentic_qe_orchestration.md` for current/future orchestration diagrams and `docs/manual_requirements_review_poc.md` for the operating and validation instructions.
