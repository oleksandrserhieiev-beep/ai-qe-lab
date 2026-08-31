# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. The Shopping RAG Assistant is the reference System Under Test (SUT) used to prove the reusable QE framework; on a real project, the application pipeline would normally already exist and be owned by Development / AI Engineering.

The reference SUT includes deterministic constraint handling, structured filtering, FAISS Top-K retrieval, adaptive context selection, deterministic context construction and Claude generation. The QE framework around it combines governed datasets, Dataset/Oracle Validation, deterministic Python assertions, semantic LLM-as-a-Judge evaluation, AI-risk metadata, CI/CD quality gates, specialized AI testing workflows, operational telemetry, failure localization and release validation.

## Current governed evaluation assets

The standard routine SUT inventory remains 105 cases:

- PR Critical standard cases: 10 total — 6 deterministic / 4 semantic;
- Regression: 15 total — 7 deterministic / 8 semantic;
- Broad Nightly Evaluation: 80 total — 48 deterministic / 32 semantic.

That standard 105-case inventory is supplemented by:

- 2 Metamorphic Critical records stored in `datasets/pr_critical_dataset.json` and executed through the dedicated metamorphic runner/gate;
- 10 governed Adversarial cases in `datasets/adversarial_dataset.json`;
- 35 Golden cases for canonical release/reference validation;
- 8 Judge Calibration cases that test the evaluator rather than the Shopping Assistant.

Back-to-Back does not introduce another dataset. It reuses the same 10 standard PR Critical cases against two selected models/configurations and compares evaluated quality plus operational telemetry.

Explicit Oracle metadata in governed datasets is primary. Missing metadata can use the reviewed fallback registry; invalid non-empty Oracle metadata fails validation before evaluation. Semantic Judge results require a short non-empty rationale; a missing `reason` is an evaluator contract violation rather than valid evidence.

## Current workflow model

```text
PR
├─ Standard Critical Evaluation     = automatic merge gate
└─ Metamorphic Critical             = automatic relation gate

Manual
└─ Back-to-Back                     = Model A vs Model B on the same 10 standard Critical cases

Scheduled / manual
└─ Adversarial                      = dedicated 10-case hostile-input suite

Other lifecycle workflows
├─ Regression                       = manual-only
├─ Broad Nightly                    = manual-only
└─ Release Validation               = manual-only: Golden + broad Nightly + Release Quality Gate
```

Drift testing is intentionally outside the current roadmap.

The upstream Agentic QE phase has started with the **Requirements Review Agent** as the first controlled slice:

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
→ Test Analysis & Design
→ Governance / Human Approval
→ Governed Dataset Update
→ existing Dataset Validation + Evaluation + CI framework
→ Defect / Regression / Release Evidence
```

Requirements Review intentionally evaluates the Jira requirement itself; external retrieval should not hide missing requirement content. Risk Analysis is the first planned stage where architecture, business rules, policies, related specifications and historical defects can become evidence through bounded retrieval.

See `README.md`, `docs/current_status.md`, `docs/test_strategy.md`, `docs/master_architecture.md` and `docs/future_ai_testing_workflows.md` for the current canonical architecture and execution model.
