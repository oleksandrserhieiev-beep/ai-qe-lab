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
| Proposed test/evaluation assets | Support | Design/review |
| Human test-asset approval | Support business truth | Govern promotion |
| Governed evaluation datasets | Support business truth | Own/govern |
| Dataset/Oracle validation | Support | Build/own |
| Oracle/assertions/Judge | Support expectations | Design/build/govern |
| Judge calibration | Support runtime/model access | Design/own evaluator-quality control |
| Golden canonical truth | Support business sources | Govern executable representation |
| Metrics/quality gates | Provide telemetry | Define/own |
| CI test/governance levels | DevOps support | Design quality execution model |
| Release evidence/recommendation | Fix/support | Quality governance |

## Framework control model

The framework separates **asset creation/governance**, **product quality execution**, **evaluator quality**, and **canonical-truth governance**.

```text
TARGET AGENTIC QE / TEST-ASSET GOVERNANCE
Requirement
-> Requirements Review
-> Risk Analysis
-> Test Analysis & Design
-> Proposed Test / Evaluation Assets
-> Human Review / Approval
-> Governed Test Assets

PRODUCT QUALITY / CI/CD EXECUTION
Selected Governed Suite
-> Dataset / Oracle Validation
-> Real SUT Execution
-> Evidence
-> Oracle Resolution
-> Deterministic Assertions or Semantic Judge
-> Metrics / Risk Aggregation
-> Product Quality Gate
-> PASS / FAIL + Evidence
-> Lifecycle Decision

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

These answer different questions:

```text
Should this proposed test/evaluation asset become governed?
Is the selected governed suite technically executable?
Is the product behavior acceptable?
Is the evaluator still trustworthy?
Is canonical expected truth being changed legitimately?
```

`Governed Test Assets` are approved artifacts, not an agent. Human Governance / Approval is the promotion boundary. Dataset/Oracle Validation is the later execution-precondition boundary.

## What the completed framework does

```text
Requirement
 -> Requirements Review
 -> Risk Analysis
 -> Test Analysis & Design
      -> Functional / API / Integration / E2E tests
      -> AI Evaluation cases
 -> Proposed Test / Evaluation Assets
 -> Human Governance / Approval
 -> Governed executable datasets / Test Management
 -> Dataset / Oracle Validation
 -> SUT execution against the existing application
 -> SUT evidence collection
 -> Oracle Resolution
      -> Deterministic Python assertions
      -> Calibrated Semantic LLM Judge
 -> Metric aggregation / AI-risk reporting
 -> Product Quality Gate
 -> Failure localization
 -> Defect / Jira traceability
 -> confirmed product fix -> Regression coverage
 -> release-readiness evidence

Parallel controls:
 -> Judge changes -> OLD vs NEW Judge Calibration
 -> Golden changes -> Golden Governance Check
```

## Test/evaluation execution

An Evaluation Case is a machine-readable test case. CI/CD quality execution begins by validating the selected governed dataset, then sends valid inputs through the **real SUT**, captures actual behavior and evaluates the evidence.

```text
Selected Governed Dataset
 -> Dataset / Oracle Validation
 -> Test/Evaluation Executor
 -> Existing SUT
 -> Actual answer + application evidence/telemetry
 -> Oracle Resolution / Evaluation
 -> Metrics / Risk
 -> Quality Gate
```

The executor is automation of what a tester would otherwise do manually; it is not a separate product architecture.

## Evaluation engine

```text
Formal, objective rule -> Deterministic Python Assertion Engine
Meaning / behavior judgment -> Calibrated Semantic LLM Judge
```

Deterministic assertions validate IDs, numbers, enums, booleans, ranges, hard constraints and other formal properties. Semantic evaluation handles correctness, groundedness, hallucination and other behavior requiring interpretation.

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

`datasets/judge_calibration_dataset.json` contains human-reviewed known good/bad evaluator examples. On relevant Judge PRs:

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

The cheaper or newer evaluator is not accepted merely because it runs; it must remain acceptably aligned with human truth and must not introduce dangerous false PASS behavior.

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
 -> deterministic catalogue routing where applicable
 -> Embedding + FAISS Semantic Ranking where applicable
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

PR Critical, Regression and Nightly are governed execution assets. They are not all canonical truth. Golden has the stronger canonical-truth role and separate governance.

A confirmed product defect normally becomes Regression coverage. Promotion to Golden is a separate canonical-governance decision.

## Dataset / Oracle Validation

Current implementation validates the executable contract before expensive model calls:

```text
dataset root -> JSON array
case ID -> required + unique
explicit Oracle -> deterministic | semantic_llm
deterministic Oracle -> non-empty deterministic assertions
missing Oracle -> warning + reviewed runtime fallback
invalid Oracle -> ERROR
```

Future schema/required-field hardening can extend this pipeline, but should be distinguished from what the current validator already enforces.

## CI/CD and release governance

CI/CD is the execution envelope from validation through the quality decision:

```text
Selected Governed Suite
-> Dataset / Oracle Validation
-> SUT Execution
-> Evaluation
-> Metrics / Risk Aggregation
-> Quality Gate
-> PASS / FAIL + Evidence
```

Lifecycle controls:

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

The target agents create/analyze proposed quality assets upstream of the existing framework:

```text
Jira / Confluence
-> Requirements Review
-> Risk Analysis
-> targeted project evidence where required
-> Test Analysis & Design
-> Proposed Test / Evaluation Assets
-> Human Governance / Approval
-> Governed Test Assets
-> Dataset / Oracle Validation
-> SUT Execution
-> Evaluation
-> Metrics / Risk Aggregation
-> Quality Gate
-> Failure Analysis / Defect / Regression / Release Evidence
```

Agents do not bypass the evaluator or governance controls. In particular they may propose a Golden/calibration change but must not silently rewrite governed truth.

## Traceability

Product traceability:

```text
Requirement
 -> Risk
 -> Proposed Test / Evaluation Case
 -> Human Governance / Approval
 -> Governed Dataset / Test Management asset
 -> Dataset / Oracle Validation
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
