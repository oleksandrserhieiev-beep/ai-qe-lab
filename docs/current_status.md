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
- Metamorphic Critical evaluation integrated into the PR path using deterministic relation checks over base/transformed invocations.
- Manual Back-to-Back model comparison using the same PR Critical suite for Model A and Model B, with evaluated quality deltas, case regressions, latency and token telemetry.
- Regression, broad Nightly and Release Validation manual workflows.
- Dedicated Adversarial workflow merged via PR #80 with a governed 10-case attack dataset, manual + nightly schedule, Attack Success Rate, category breakdown and critical adversarial gate.

## Current downstream execution model

```text
PR
├─ Standard Critical Evaluation
└─ Metamorphic Critical Evaluation

Manual comparison
└─ Back-to-Back Model A vs Model B

Nightly / scheduled
└─ Adversarial Evaluation

Other lifecycle suites
├─ Regression           = manual
├─ Broad Nightly        = manual
└─ Release Validation   = manual
```

Core governed suite execution remains:

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

Metamorphic, Back-to-Back and Adversarial are specialized AI-testing workflows around this core execution model rather than replacements for it.

## AI-specific test techniques

### Metamorphic Testing — implemented

Current PR Critical dataset contains two explicit metamorphic cases. Each runs a base and transformed query and checks a governed invariant using a deterministic relation Oracle. Current relations cover paraphrase invariance and irrelevant-noise invariance for critical policy facts.

### Back-to-Back Testing — implemented

The `Back-to-Back Model Comparison` workflow is manual. It runs the same non-metamorphic PR Critical cases against two selected generation models, evaluates both outputs through the existing evaluator and produces:

- overall pass-rate delta;
- correctness, groundedness, retrieval-hit, constraint-adherence and hallucination deltas;
- improved / regressed / unchanged case counts;
- critical regressions;
- average and p95 latency;
- input/output/total token usage.

### Adversarial Testing — implemented

The dedicated adversarial flow is based on `docs/adversarial_testing_contract.md` and uses 10 governed cases across:

- business-policy override;
- instruction override;
- unsupported-claim forcing;
- prompt/system leakage;
- malicious/conflicting retrieved content;
- hard-constraint bypass.

The flow reuses the standard SUT runner and evaluator, then adds adversarial-specific aggregation:

```text
Adversarial Dataset
→ Dataset Validation
→ SUT Execution
→ Existing Evaluator
→ Adversarial Summary
   ├─ Adversarial Pass Rate
   ├─ Attack Success Rate
   ├─ Category Breakdown
   └─ Critical Failure Count
→ Adversarial Gate
→ Artifact / Step Summary
```

Drift testing is intentionally excluded from the current roadmap.

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
PR Critical          = automatic merge gate
Metamorphic Critical = automatic PR validation
Back-to-Back         = manual Model A vs Model B comparison
Adversarial          = manual + nightly scheduled hostile-input evaluation
Regression           = manual-only
Broad Nightly        = manual-only
Release Validation   = manual-only: Golden + broad Nightly + Release Quality Gate
Judge Calibration    = automatic for Judge/calibration behavior changes + manual
Golden Governance    = automatic for Golden dataset/check/workflow changes
Requirements Review  = manual batch execution
```

The broad Regression/Nightly product-evaluation schedules remain intentionally paused while the POC baseline is stable. The dedicated Adversarial suite is intentionally scheduled separately because it has its own attack taxonomy, metrics and gate.

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

The target Agentic QE continuation remains:

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
