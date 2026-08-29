# AI QE Lab — Project Overview

AI QE Lab is an end-to-end Quality Engineering framework for AI-enabled systems. The Shopping RAG Assistant is the reference System Under Test used to prove the framework, while the QE lifecycle itself is designed to generalize to other AI application types.

> This document describes the target operating model in present tense by design. It explains what the completed framework does, while implementation status is tracked separately in `current_status.md`.

## What the framework does

AI QE Lab takes a product requirement from Jira, reviews whether it is testable, identifies applicable AI risks, generates conventional and AI-specific tests, governs executable evaluation datasets, runs automated evaluation through deterministic and semantic oracles, applies quality gates, localizes failures and feeds confirmed defects back into regression coverage.

The complete lifecycle is:

```text
Jira Requirement
 -> Requirements Review / Entry Gate
 -> AI Risk Analysis
 -> Test Design
      -> Functional / API / Integration / E2E tests
      -> AI Evaluation cases
 -> Test & Dataset Governance Review
 -> Human approval where required
 -> Governed executable datasets / Test Management
 -> Dataset Validation
 -> SUT execution
 -> Retrieval / Context / Generation evidence
 -> Oracle Resolution
      -> Deterministic Python assertions
      -> Semantic LLM Judge
 -> Metric aggregation
 -> AI-risk reporting
 -> Quality Gate
 -> Failure localization
 -> Defect draft / Jira traceability
 -> confirmed fix -> Regression Dataset
 -> release-readiness evidence
```

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

Deterministic assertions validate IDs, numbers, enums, booleans, ranges, schemas, structured constraints and other formal properties across retrieval, context and generation layers.

Semantic evaluation handles correctness, groundedness, hallucination, ambiguity, safety and other behavior that requires interpretation rather than exact comparison.

Metrics always report the population actually measured. Suite-wide, semantic-only, hybrid and applicability-scoped metrics therefore have explicit denominators instead of implying that every metric covers every case.

## RAG reference SUT

The Shopping RAG Assistant executes:

```text
Query
 -> Constraint Extraction
 -> Structured Filtering
 -> Embedding + FAISS Ranking
 -> Top-K Retrieval Candidates
 -> Adaptive Context Selection
 -> Context Builder
 -> Claude generation
```

Retrieval-K and Context-K are separate. Adaptive Context Selection removes low-value evidence before generation while retaining telemetry that shows which candidates were selected or dropped and why.

The framework localizes defects to the earliest failing layer: retrieval, context selection, augmentation/context, generation, Oracle/evaluation, or operational execution.

## Dataset model

Datasets are separated by purpose rather than inheritance:

- **Golden** — trusted baseline and release reference;
- **PR Critical** — fast merge-blocking risk-based coverage;
- **Regression** — stable behavior plus confirmed defect coverage;
- **Nightly Evaluation** — broad AI-risk, adversarial and edge-case coverage.

A confirmed defect automatically becomes a candidate for Regression coverage so production or test-discovered failures are converted into permanent executable evidence.

## CI/CD and release governance

The framework provides multiple execution levels:

```text
PR Critical -> merge gate
Regression -> main health gate
Nightly Evaluation -> broad AI-risk surveillance
Release validation -> Golden + Regression + required critical evidence
```

Quality gates combine deterministic outcomes, semantic metrics, risk-level evidence, critical-case failures and operational telemetry. The resulting evidence supports release-readiness and residual-risk decisions rather than only producing a generic PASS/FAIL score.

## Traceability

The lifecycle preserves traceability across:

```text
Requirement
 -> AI Risk
 -> Test / Evaluation Case
 -> Dataset or Test Management asset
 -> CI execution level
 -> Metric
 -> Quality Gate
 -> Evidence
 -> Defect / Regression coverage
 -> Residual Risk / Release Decision
```

This makes the lab an AI Quality Engineering framework rather than only a RAG demo or an LLM evaluation script.