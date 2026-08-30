# AI QE Lab — Project Overview

AI QE Lab is an end-to-end Quality Engineering framework for AI-enabled systems. The Shopping RAG Assistant is a **reference System Under Test (SUT)** that we built only because the lab needed a real AI application to execute tests against. The reusable product of the lab is the QE framework around that SUT, not the Shopping Assistant itself.

> This document describes the target operating model in present tense by design. It explains what the completed framework does, while implementation status is tracked separately in `current_status.md`.

## Reference SUT vs reusable QE framework

In this lab we owned both sides:

```text
Reference application / SUT
        +
AI QE framework around it
```

That was necessary for the POC because there was no existing application available to test. Building the Shopping RAG Assistant gave us a controlled application pipeline with known data, retrieval behavior, context construction and model generation so the QE layers could be implemented and verified against something real.

On a real project, Development / AI Engineering will usually already own the application pipeline. A Quality Architect or QE team should **not start by rebuilding the SUT**. The first task is to understand it well enough to test it.

Before designing the framework, QE should ask:

1. What is the System Under Test and what business behavior does it provide?
2. What is the end-to-end application/request pipeline?
3. Where is AI used and which model(s) are involved?
4. Is retrieval/RAG used? If yes, how are retrieval and context selection implemented?
5. What are the inputs, outputs, APIs/contracts and deterministic business rules?
6. Which decisions are deterministic and which are semantic/model-driven?
7. Which tools, external services or data sources are dependencies?
8. What telemetry/evidence is available at each layer?
9. Which architecture-specific failure modes must the QE framework detect?

QE can identify gaps in testability or observability and recommend changes, but application implementation remains owned by the product/development/AI engineering team.

The practical ownership model is:

| Area | Development / AI Engineering | QE / Quality Architecture |
|---|---|---|
| SUT/application pipeline | Build and own | Understand and test |
| Retrieval/context/tooling | Build and own | Validate behavior and evidence |
| Prompt/model integration | Build and own | Test semantic and operational quality |
| Observability hooks | Implement/support | Define evidence required for testing |
| Requirement/risk/test governance | Support | Own/design |
| Evaluation datasets | Support business truth | Own/govern |
| Dataset validation | Support | Build/own |
| Oracle/assertions/Judge | Support expected behavior | Design/build |
| Metrics and quality gates | Provide telemetry | Define/own |
| CI test levels | DevOps support | Design quality execution model |
| Failure localization | Instrumentation support | Design/use |
| Release evidence and recommendation | Fix/support | Quality governance |

## What the framework does

After the SUT architecture is understood, the reusable QE lifecycle starts here:

```text
Requirement
 -> Requirements Review / Entry Gate
 -> AI Risk Analysis
 -> Test Design
      -> Functional / API / Integration / E2E tests
      -> AI Evaluation cases
 -> Test & Dataset Governance Review
 -> Human approval where required
 -> Governed executable datasets / Test Management
 -> Dataset Validation
 -> Test execution against the existing SUT
 -> SUT evidence collection
 -> Oracle Resolution
      -> Deterministic Python assertions
      -> Semantic LLM Judge
 -> Metric aggregation
 -> AI-risk reporting
 -> Quality Gate
 -> Failure localization
 -> Defect / Jira traceability
 -> confirmed fix -> Regression Dataset
 -> release-readiness evidence
```

The framework therefore answers a different question from the SUT:

```text
SUT:      How does the AI-enabled product process a request and produce an output?
QE:       How do we prove that behavior is acceptable, diagnose failures and make lifecycle quality decisions?
```

## Test/evaluation execution

An Evaluation Case is simply a machine-readable test case. The execution layer reads a governed case, sends its input through the **real SUT**, captures the result and records the evidence required by the evaluator.

Conceptually:

```text
Governed Dataset Case
 -> Test/Evaluation Executor
 -> Existing SUT
 -> Actual answer + application evidence/telemetry
 -> Evaluation
```

The executor is not a separate product architecture. It is the automation mechanism that performs the same action a tester would perform manually: provide an input to the SUT and capture actual behavior.

## Requirements and agent orchestration

The Requirements Review Agent checks story quality before downstream automation starts. It validates acceptance criteria, expected behavior, failure behavior, data/source dependencies, constraints and missing information.

The AI Risk Analysis Agent maps only risks that are applicable to the architecture and feature under test. It does not assume that every AI feature is RAG-based or automatically assign hallucination, retrieval or prompt-injection risks when they do not apply.

The Test Design Agent creates both conventional test coverage and AI evaluation cases. Functional, API, integration and E2E tests are routed to Test Management; AI evaluation cases are routed into governed executable datasets.

The Governance/Review Agent checks generated test assets for duplicates, risk coverage, criticality, Oracle choice, suite placement, traceability and consistency with approved requirements. Human approval remains available as a risk-based control before changes become executable.

The Dataset Update Agent applies approved changes to the governed JSON datasets and derived Oracle metadata. The dataset package is the authoritative runtime source; generated helper mappings are derived from validated approved data rather than manually maintained as a second source of truth.

## Evaluation engine

The framework evaluates AI behavior through two automated Oracle routes:

```text
Formal, objective rule -> Deterministic Python Assertion Engine
Meaning / behavior judgment -> Semantic LLM Judge
```

Deterministic assertions validate IDs, numbers, enums, booleans, ranges, schemas, structured constraints and other formal properties across application layers when the necessary evidence is exposed.

Semantic evaluation handles correctness, groundedness, hallucination, ambiguity, safety and other behavior that requires interpretation rather than exact comparison.

Metrics always report the population actually measured. Suite-wide, semantic-only, hybrid and applicability-scoped metrics therefore have explicit denominators instead of implying that every metric covers every case.

## Reference RAG SUT used by this lab

The Shopping RAG Assistant currently executes:

```text
User / Evaluation Case
 -> Constraint Extraction
 -> Constraint Validation / Classification
      -> unresolved -> Deterministic Clarification
      -> resolved -> continue
 -> Structured Product Filtering
      -> zero matching products -> Deterministic No-Product-Match
 -> Embedding + FAISS Semantic Ranking
 -> Retrieval-K / Top-K Candidates
 -> Adaptive Context Selection
 -> Context-K
      -> 0 -> Deterministic Abstention
      -> >0 -> Context Builder -> Claude Generation
 -> SUT Output
```

This application pipeline is useful to QE because each layer creates a different possible failure point. A real project may have a different architecture: it may omit retrieval entirely, use tools/agents, use a reranker, have no adaptive selector, or contain different deterministic controls. QE must map the **actual** SUT rather than copy this RAG pipeline mechanically.

Retrieval-K and Context-K are separate in the reference SUT. Adaptive Context Selection removes low-value evidence before generation while retaining telemetry that shows which candidates were selected or dropped and why.

The framework then uses that telemetry to localize defects to the earliest failing layer: input/constraint handling, retrieval/filtering/ranking, context selection, context construction, generation, Oracle/evaluation, or operational execution.

## Dataset model

Datasets are separated by purpose rather than inheritance:

- **Golden** — trusted canonical baseline and release reference;
- **PR Critical** — fast merge-blocking risk-based coverage;
- **Regression** — stable behavior plus confirmed defect coverage;
- **Nightly Evaluation** — broad AI-risk, adversarial and edge-case coverage.

A confirmed defect becomes a candidate for Regression coverage so production or test-discovered failures are converted into permanent executable evidence.

## CI/CD and release governance

The framework supports multiple execution levels. The exact trigger policy can be enabled or paused independently from the test/evaluation capability:

```text
PR Critical       -> fast merge quality gate
Regression        -> main health gate
Nightly Evaluation-> broad AI-risk signal
Release Validation-> Golden + valid broad Nightly evidence for the release scope/SHA
```

The same evaluation engine can therefore be invoked from PR, merge/main, schedule, manual execution or release workflows. The workflow decides **when and which dataset to execute**; the evaluator decides **whether the observed behavior passes its Oracle and quality gates**.

Release Validation treats Golden and Nightly as different evidence types. Golden proves trusted canonical business-critical behavior. Nightly provides broader AI-risk, adversarial and edge coverage. A release candidate requires Golden plus valid broad evidence for the same release candidate/scope; when reusable Nightly evidence is not valid for that SHA/scope, the broad suite is re-executed.

Quality gates combine deterministic outcomes, semantic metrics, risk-level evidence, critical-case failures and operational telemetry. The resulting evidence supports release-readiness and residual-risk decisions rather than only producing a generic PASS/FAIL score.

## Traceability

The lifecycle preserves traceability across:

```text
Requirement
 -> AI Risk
 -> Test / Evaluation Case
 -> Governed Dataset or Test Management asset
 -> Dataset Validation
 -> SUT execution
 -> Evidence
 -> Oracle / Metric
 -> Quality Gate
 -> Defect / Regression coverage
 -> Residual Risk / Release Decision
```

This separation is what makes the lab a reusable **AI Quality Engineering Framework** rather than only a RAG demo or an LLM evaluation script.