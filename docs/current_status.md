# Current Evaluation and Agentic QE Status

## Implemented downstream QE framework

- Shopping RAG Assistant reference SUT with deterministic constraint extraction/validation, structured filtering, FAISS retrieval, adaptive context selection and Claude generation.
- Deterministic clarification, no-product-match and no-context abstention paths that can skip Claude.
- Governed Golden, PR Critical, Regression and Nightly datasets.
- Dataset/Oracle Validation before active evaluation model calls.
- Deterministic Python assertions plus semantic LLM Judge evaluation.
- Version-controlled Judge model/prompt/rubric configuration.
- Human-reviewed Judge Calibration Dataset and OLD-vs-NEW calibration gate.
- Golden Dataset Governance check requiring Change Reason + Source of Truth.
- AI-risk/metric aggregation, quality gates, telemetry and failure localization.
- PR Critical automatic merge gate.
- Regression, Nightly and Release Validation manual workflows.

## Implemented upstream Agentic QE slice — Requirements Review

The first agentic component is the read-only Requirements Review Agent.

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

## Governance boundary now implemented

```text
Product behavior
→ Dataset Validation
→ SUT Execution
→ Oracle / Judge
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

These are separate controls. Requirements Review creates upstream quality evidence; it does not replace independent product evaluation, Judge calibration, Golden governance or release accountability.

## Requirements Review POC closure

The Requirements Review slice is treated as the first complete Agentic QE component when its validation tests, batch metrics, documentation and orchestration diagrams are merged.

Explicitly outside that closure:

- Risk Analysis Agent;
- cross-document retrieval/RAG for risk analysis;
- Test Generation Agent;
- Jira write-back;
- automatic/scheduled agent execution;
- HITL dataset promotion;
- full multi-agent state orchestration.

## Next phase

The next major implementation slice is Risk Analysis after the Requirements Review closure:

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
Test Generation Agent
        ↓
Governance / HITL
        ↓
Governed Dataset Update
        ↓
existing Dataset Validation + Evaluation + CI/CD
        ↓
Regression / Release Evidence
```

Risk Analysis is intentionally downstream of the readiness gate. Requirements Review asks whether the story itself is sufficient; Risk Analysis asks what can go wrong and may retrieve architecture, business rules, policies, related specifications and historical defects as supporting evidence.
