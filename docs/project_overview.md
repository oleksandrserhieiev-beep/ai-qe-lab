# AI QE Lab — Project Overview

AI QE Lab is an end-to-end Quality Engineering framework for AI-enabled systems. The Shopping RAG Assistant is a **reference System Under Test (SUT)** built because the lab needed a real AI application to execute tests against. The reusable product is the QE framework around that SUT, not the Shopping Assistant itself.

> This document describes the target operating model in present tense by design. Actual implementation status is tracked in `current_status.md`.

## Reference SUT vs reusable QE framework

```text
Reference application / SUT
        +
AI QE framework around it
```

On a real project, Development / AI Engineering normally owns the application pipeline. QE first understands it: business behavior, request pipeline, AI/RAG/tool usage, deterministic rules, inputs/outputs/contracts, dependencies, telemetry and architecture-specific failure modes.

Practical ownership:

| Area | Development / AI Engineering | QE / Quality Architecture |
|---|---|---|
| SUT/application pipeline | Build/own | Understand/test |
| Retrieval/context/tooling | Build/own | Validate behavior/evidence |
| SUT prompt/model integration | Build/own | Test semantic/operational quality |
| Observability hooks | Implement/support | Define required evidence |
| Requirement/risk/test governance | Support | Own/design |
| Evaluation datasets | Support business truth | Own/govern |
| Dataset validation | Support | Build/own |
| Oracle/assertions/Judge | Support expectations | Design/build/govern |
| Judge calibration | Support runtime/model access | Design/own evaluator-quality control |
| Golden canonical truth | Support business sources | Govern executable representation |
| Metrics/quality gates | Provide telemetry | Define/own |
| CI test/governance levels | DevOps support | Design quality execution model |
| Release evidence/recommendation | Fix/support | Quality governance |

## Three framework control loops

The framework does not rely on one generic “AI check”. It separates product quality, evaluator quality and canonical-truth governance.

```text
PRODUCT QUALITY
Governed SUT Case
-> Dataset Validation
-> Real SUT
-> Evidence
-> Oracle
-> Deterministic Assertions or Semantic Judge
-> Metrics / Risk
-> Product Quality Gate

EVALUATOR QUALITY
Judge Model / Prompt / Rubric Change
-> OLD Judge from main
-> NEW Judge from PR
-> Same Human Calibration Truth
-> Agreement / False PASS / False FAIL
-> Judge Calibration Gate

CANONICAL TRUTH GOVERNANCE
Golden Expected-Behavior Change
-> Golden Change Reason
-> Source of Truth
-> Deterministic Golden Governance Check
-> Human Review
-> Approved Golden Baseline
```

This answers three different questions:

```text
Is the product correct?
Is the evaluator still trustworthy?
Is the expected truth being changed legitimately?
```

## What the completed framework does

```text
Requirement
 -> Requirements Review / Entry Gate
 -> Test Analysis & Risk
 -> Test Design
      -> Functional / API / Integration / E2E tests
      -> AI Evaluation cases
 -> Coverage / Governance Review
 -> Human approval where required
 -> Governed executable datasets / Test Management
 -> Dataset Validation
 -> Test execution against the existing SUT
 -> SUT evidence collection
 -> Oracle Resolution
      -> Deterministic Python assertions
      -> Calibrated Semantic LLM Judge
 -> Metric aggregation / AI-risk reporting
 -> Product Quality Gate
 -> Failure localization
 -> Defect / Jira traceability
 -> confirmed product fix -> Regression Dataset
 -> release-readiness evidence

Parallel controls:
 -> Judge changes -> OLD vs NEW Judge Calibration
 -> Golden changes -> Golden Governance Check
```

## Test/evaluation execution

An Evaluation Case is a machine-readable test case. The executor sends its input through the **real SUT**, captures actual behavior and collects evidence required by the Oracle/evaluator.

```text
Governed Dataset Case
 -> Test/Evaluation Executor
 -> Existing SUT
 -> Actual answer + application evidence/telemetry
 -> Evaluation
```

The executor is automation of what a tester would otherwise do manually; it is not a separate product architecture.

## Evaluation engine

```text
Formal, objective rule -> Deterministic Python Assertion Engine
Meaning / behavior judgment -> Calibrated Semantic LLM Judge
```

Deterministic assertions validate IDs, numbers, enums, booleans, ranges, schemas, hard constraints and other formal properties. Semantic evaluation handles correctness, groundedness, hallucination and other behavior requiring interpretation.

Metrics report the population actually measured. Semantic-only metrics therefore use only semantic/Judge cases as denominator.

The production Judge uses version-controlled assets:

```text
config/judge_config.json
config/judge_prompt.txt
config/judge_rubric.txt
```

so semantic evidence can be tied to the exact Judge model, prompt and rubric version.

## Judge Calibration

The framework treats the LLM Judge as a test object of its own.

`datasets/judge_calibration_dataset.json` contains 8 human-reviewed known good/bad evaluator examples. The first approved baseline — `claude-opus-5` + prompt `v1` + rubric `v1` — matched all 32 human-approved semantic field expectations with 100% agreement, 0 false PASS and 0 false FAIL.

On future relevant Judge PRs:

```text
OLD = approved Judge configuration from main
NEW = proposed Judge configuration from PR

OLD -> same human calibration set
NEW -> same human calibration set
        ↓
compare human agreement and false PASS/FAIL
        ↓
Judge Calibration Gate
```

Current POC gate requires NEW agreement >= 90%, no drop greater than 5 percentage points and no increase in false PASS.

This allows changes such as Opus -> Sonnet, prompt revisions or rubric revisions to be evaluated before the new evaluator is trusted for product quality decisions.

## Golden Dataset governance

Golden is a canonical business/reference baseline, not a convenient expected-results file.

```text
Evaluation FAIL
!=
Rewrite Golden until PASS
```

A Golden change must carry:

```text
Golden Change Reason: ...
Source of Truth: ...
```

The deterministic governance action is path-scoped to the Golden dataset and its checker/workflow. Documentation and unrelated SUT changes do not trigger it.

This prevents goalpost movement while keeping ordinary PR cost low.

## Reference RAG SUT

```text
User / Evaluation Case
 -> Constraint Extraction
 -> Constraint Validation / Classification
      -> unresolved -> Deterministic Clarification
 -> Structured Product Filtering
      -> zero matches -> Deterministic No-Product-Match
 -> Embedding + FAISS Semantic Ranking
 -> Retrieval-K / Top-K Candidates
 -> Adaptive Context Selection
 -> Context-K
      -> 0 -> Deterministic Abstention
      -> >0 -> Context Builder -> Claude Generation
 -> SUT Output
```

Retrieval-K and Context-K are separate. Adaptive Context Selection removes low-value evidence before generation while preserving diagnostics about selected/dropped evidence.

A real project may omit retrieval, use agents/tools/rerankers or expose different deterministic controls. QE maps the actual SUT rather than copying this pipeline mechanically.

## Dataset model

SUT datasets are separated by lifecycle purpose:

- **Golden** — trusted canonical baseline/release reference;
- **PR Critical** — fast merge-blocking risk coverage;
- **Regression** — stable behavior plus confirmed defect coverage;
- **Nightly Evaluation** — broad AI-risk/adversarial/edge coverage.

Separate evaluator dataset:

- **Judge Calibration** — human-reviewed truth for testing the Judge, not the SUT.

A confirmed product defect normally becomes Regression coverage. Promotion to Golden is a separate canonical-governance decision.

## CI/CD and release governance

```text
PR Critical        -> automatic fast product merge gate
Regression         -> stable product health (manual currently)
Nightly Evaluation -> broad product AI-risk signal (manual currently)
Release Validation -> Golden + valid broad evidence
Judge Calibration  -> automatic on Judge/calibration behavior changes
Golden Governance  -> automatic on Golden/check/workflow changes
```

Workflow trigger policy and evaluation capability are separate. Documentation-only changes should not spend LLM evaluation cost unnecessarily.

Release Validation requires canonical Golden evidence plus valid broad-risk evidence for the relevant release candidate/scope/SHA. If the release includes a Judge change, valid calibration evidence is also part of evaluator confidence. If the release includes a Golden change, the canonical baseline movement must be visible and governed.

## Requirements and agent orchestration

The target agents create/analyze/govern quality inputs around the existing framework:

```text
Jira / Confluence
-> Requirements Review
-> Test Analysis & Risk
-> Test Design
-> Coverage & Gap Analysis
-> Human Approval
-> Governed Tests / JSON Datasets
-> existing Dataset Validation
-> existing SUT Evaluation
-> existing Judge Calibration / Golden Governance controls
-> Failure Analysis / Defect / Regression / Release Evidence
```

Agents do not bypass the evaluator or governance controls. In particular they may propose a Golden/calibration change but must not silently rewrite governed truth.

## Traceability

Product traceability:

```text
Requirement
 -> Risk
 -> Test / Evaluation Case
 -> Governed Dataset / Test Management asset
 -> Dataset Validation
 -> SUT execution
 -> Evidence
 -> Oracle / Metric
 -> Product Quality Gate
 -> Defect / Regression
 -> Residual Risk / Release Decision
```

Evaluator traceability:

```text
Judge Change
 -> Model / Prompt / Rubric Version
 -> Human Calibration Case
 -> OLD / NEW Result
 -> Agreement / False PASS / False FAIL
 -> Judge Calibration Gate
 -> Approved Judge Baseline
```

Canonical-truth traceability:

```text
Golden Change
 -> Previous / Proposed Expected Behavior
 -> Change Reason
 -> Source of Truth
 -> Human Review
 -> Golden Governance Check
 -> Approved Golden Baseline
```

This separation is what makes the lab a reusable **AI Quality Engineering Framework** rather than only a RAG demo or an LLM evaluation script.
