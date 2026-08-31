# Current Evaluation and Agentic QE Status

## Implemented downstream QE framework

- Shopping RAG Assistant reference SUT with deterministic constraint extraction/validation, structured filtering, FAISS retrieval, adaptive context selection and Claude generation.
- Deterministic clarification, no-product-match, deterministic catalogue routing and no-context abstention paths that can skip Claude where applicable.
- Governed Golden, PR Critical, Regression and Nightly datasets.
- Dataset/Oracle Validation as the first technical stage before active SUT/Judge model execution.
- Deterministic Python assertions plus semantic LLM Judge evaluation.
- Version-controlled Judge model/prompt/rubric configuration.
- Human-reviewed Judge Calibration Dataset and OLD-vs-NEW calibration gate.
- Golden Dataset Governance check requiring Change Reason + Source of Truth.
- AI-risk/metric aggregation, quality gates, telemetry and failure localization.
- PR Critical automatic merge gate.
- Regression, Nightly and Release Validation manual workflows.

## Current downstream execution model

```text
Selected Governed Suite
→ Dataset / Oracle Validation
→ SUT Execution
→ Evaluation
   ├─ deterministic Python
   └─ semantic LLM Judge
→ Metrics / Risk Aggregation
→ Quality Gate
→ PASS / FAIL + Evidence
→ Lifecycle Decision
```

This is the CI/CD execution path. CI/CD does not start after Evaluation; it orchestrates the sequence from Dataset/Oracle Validation through the Quality Gate.

## Implemented upstream Agentic QE slice — Requirements Review

The first complete agentic component is the read-only Requirements Review Agent.

Current implemented flow:

```text
Manual GitHub Actions batch
→ Jira retrieval
→ deterministic Python eligibility pre-check
   ├─ reject → 0 LLM tokens
   └─ eligible
       ↓
minimal semantic payload
       ↓
content fingerprint
       ↓
cache / force-review decision
   ├─ matching cache → reuse → 0 LLM tokens
   └─ fresh review → Claude
       ↓
READY / NEEDS_CLARIFICATION
       ↓
blocking gaps / clarification questions
       ↓
batch quality + cache + token + cost metrics
```

Implemented controls include:

- issue/project/status/Description/Acceptance Criteria pre-checks before Claude;
- minimal semantic payload: issue key, summary, description, acceptance criteria and components;
- structured READY / NEEDS_CLARIFICATION contract;
- blocking-gap clarification evidence;
- compact prompt/output budgets and malformed-JSON retry;
- persistent content-hash cache;
- invalidation when Summary / Description / Acceptance Criteria / Components, model or prompt changes;
- manual `force_review=true` cache bypass;
- serialized GitHub cache persistence;
- batch quality/efficiency/cost metrics: requested, eligible, rejected, READY, NEEDS_CLARIFICATION, cache hits, LLM attempts, cache hit rate, LLM execution rate, avoided LLM calls, tokens and actual estimated cost.

Detailed orchestration and sequence diagrams: `docs/agentic_qe_orchestration.md`.  
Manual operating/validation instructions: `docs/manual_requirements_review_poc.md`.

## Target Agentic QE architecture

The master architecture intentionally keeps the full target flow even though implementation is incremental:

```text
Jira / Confluence
→ Requirements Review
→ Risk Analysis
→ targeted evidence retrieval where needed
→ Human Governance
→ Test Analysis & Design
→ Proposed Test / Evaluation Assets
→ Human Review / Approval
→ Governed Test Assets
→ downstream CI/CD Quality Execution
```

`Governed Test Assets` are approved artifacts, not an agent. Human Governance / Approval is the promotion boundary. Dataset/Oracle Validation is a later runtime/execution-precondition check.

## Current CI execution state

```text
PR Critical          = automatic merge gate for meaningful PR changes
Regression           = manual-only
Nightly              = manual-only
Release Validation   = manual-only: Golden + broad Nightly + Release Quality Gate
Judge Calibration    = automatic for Judge/calibration behavior changes + manual
Golden Governance    = automatic for Golden dataset/check/workflow changes
Requirements Review  = manual batch execution
```

Regression/Nightly schedules remain intentionally paused while the POC baseline is stable and the upstream Jira-driven Agentic QE lifecycle is being introduced.

## Governance boundaries

```text
Proposed test/evaluation asset
→ Human Review / Approval
→ Governed Test Asset

Selected governed suite
→ Dataset / Oracle Validation
→ SUT Execution
→ Evaluation
→ Metrics / Risk Aggregation
→ Product Quality Gate

Judge behavior change
→ OLD vs NEW Judge
→ Human Calibration Truth
→ Judge Calibration Gate

Golden truth change
→ Change Reason + Source of Truth
→ Golden Governance Check

Jira requirement
→ deterministic eligibility
→ Requirements Review Agent
→ READY / NEEDS_CLARIFICATION
→ cache / cost / batch evidence
```

These are separate controls. Human test-asset approval governs promotion. Dataset/Oracle Validation governs execution eligibility under the implemented contract. Requirements Review creates upstream quality evidence; it does not replace independent product evaluation, Judge calibration, Golden governance or release accountability.

## Current implementation maturity

Requirements Review is implemented and runnable. Risk Analysis currently has its contract/skeleton and validation tests, while LLM execution/retrieval orchestration remains a later implementation slice. Test Analysis & Design, governed dataset promotion and full multi-agent state orchestration remain target architecture.

## Next phase

The target continuation is:

```text
Jira Requirement
→ Requirements Review
   ├─ NEEDS_CLARIFICATION → requirement clarification → re-review
   └─ READY
        ↓
Risk Analysis Agent
        ↓
Targeted retrieval/RAG where cross-document evidence is needed
        ↓
Test Analysis & Design Agent
        ↓
Proposed Test / Evaluation Assets
        ↓
Human Governance / Approval
        ↓
Governed Test Assets
        ↓
Dataset / Oracle Validation
        ↓
SUT Execution
        ↓
Evaluation
        ↓
Metrics / Risk Aggregation
        ↓
Quality Gate
        ↓
Regression / Release Evidence
```

Risk Analysis is intentionally downstream of the readiness gate. Requirements Review asks whether the story itself is sufficient; Risk Analysis asks what can go wrong and may retrieve architecture, business rules, policies, related specifications and historical defects as supporting evidence.
