# AI QE Lab

Practical AI Quality Engineering lab for building, testing, evaluating, observing and governing AI-enabled systems.

## Quick start

New to the lab? Follow [`QUICKSTART.md`](QUICKSTART.md) to clone the repository, configure the local environment and run the project on Windows.

## What this lab is

The executable System Under Test (SUT) is a Shopping RAG Assistant. The main purpose of the repository is the QE framework around that SUT: governed datasets, dataset validation, deterministic and semantic evaluation, AI-risk evidence, evaluator calibration, dataset governance, CI quality gates, telemetry, failure localization and Agentic QE/STLC orchestration.

Engineering owns the SUT implementation. QE defines risks and expected behavior, builds evaluation assets, executes the real SUT, evaluates evidence, validates the evaluator itself, governs canonical test truth, gates quality and localizes failures.

## Master architecture

The README intentionally keeps the master view compact. It shows how the major pipelines/control planes connect. The detailed steps live in focused Markdown documents linked in **Architecture navigation** below.

```mermaid
flowchart TB
    ORCH["Agentic QE / STLC Orchestration\nRequirements -> Risks -> Tests -> Dataset Proposals"]
    GOVDATA["Governed Datasets\nHuman-approved evaluation truth"]
    VALID["Dataset / Oracle Validation\nSchema + contract + eligibility + routing"]
    APP["Application / SUT Pipeline\nShopping RAG execution"]
    EVAL["Evaluation Pipeline\nOracle -> Python / LLM Judge -> Metrics"]
    QG["CI/CD Quality Pipeline\nSuite execution -> Quality Gate -> Decision"]

    ORCH --> GOVDATA
    GOVDATA --> VALID
    VALID --> APP
    APP --> EVAL
    EVAL --> QG

    EGOV["Evaluator Governance\nJudge Calibration"] -. controls .-> EVAL
    GGOV["Canonical Truth Governance\nGolden change control"] -. controls .-> GOVDATA
    QG --> DEC["PR / Regression / Nightly / Release Decision"]
```

**Boundary:** the SUT is the reference application built for the lab. On a real project, Development / AI Engineering normally owns that application pipeline. Agentic QE is upstream and prepares reviewed quality assets; Dataset/Oracle Validation proves those assets are executable; Evaluation judges observed SUT behavior; CI/CD applies the quality decision.

For the expanded map and responsibility boundaries, see [`docs/master_architecture.md`](docs/master_architecture.md).

## Architecture navigation

Use the master diagram for orientation, then open the pipeline that owns the question you are investigating.

| Pipeline / control plane | Responsibility | Detailed view |
|---|---|---|
| **Agentic QE / STLC Orchestration** | Requirement review -> risk analysis -> test analysis/design -> governed dataset proposal | [`docs/agentic_qe_orchestration.md`](docs/agentic_qe_orchestration.md) |
| **Dataset / Oracle Validation Pipeline** | Validate schema, case identity, required fields, Oracle metadata/routing and execution eligibility before model calls | [`docs/dataset_oracle_validation_pipeline.md`](docs/dataset_oracle_validation_pipeline.md) |
| **Application / SUT Pipeline** | Execute the Shopping RAG flow: constraints -> filtering -> retrieval -> adaptive context -> generation/deterministic exits | [`docs/architecture.md`](docs/architecture.md#3-reference-sut-pipeline) |
| **Evaluation Pipeline** | Resolve the validated Oracle against SUT evidence, route to deterministic Python or semantic LLM Judge, aggregate metrics | [`docs/automated_ai_evaluation.md`](docs/automated_ai_evaluation.md) |
| **CI/CD Quality Pipeline** | Select execution suite, validate, execute SUT/evaluation, apply quality gates and retain PASS/FAIL evidence | [`docs/master_architecture.md`](docs/master_architecture.md#4-cicd-quality-pipeline) |
| **Dataset Design / Oracle Contract** | Define PR Critical, Regression, Nightly, Golden and Judge Calibration roles plus Oracle/assertion metadata | [`docs/dataset_design.md`](docs/dataset_design.md) |
| **Golden / Canonical Truth Governance** | Prevent canonical expected behavior from being rewritten without approved reason/source of truth | [`docs/golden_dataset_governance.md`](docs/golden_dataset_governance.md) |
| **Evaluator Governance** | Calibrate OLD vs NEW Judge against human-reviewed truth before trusting evaluator changes | [`docs/judge_calibration_workflow.md`](docs/judge_calibration_workflow.md) |
| **Master Architecture** | Expanded end-to-end map, boundaries and cross-cutting rules | [`docs/master_architecture.md`](docs/master_architecture.md) |

### Agent-level navigation

| Agent | Contract / implementation context |
|---|---|
| Requirements Review Agent | [`docs/requirements_review_agent.md`](docs/requirements_review_agent.md) |
| Risk Analysis Agent | [`docs/risk_analysis_agent.md`](docs/risk_analysis_agent.md) |

## Current QE control planes

| Concern | Purpose |
|---|---|
| SUT | Real Shopping RAG behavior under test |
| Dataset Validation | Reject invalid test/oracle contracts before model calls |
| Product Evaluation | Resolve Oracle, evaluate deterministic/semantic behavior, aggregate metrics and risks |
| Judge Calibration | Regression-test the semantic evaluator itself against human-reviewed truth |
| Golden Governance | Prevent canonical expected behavior from being silently rewritten to make CI green |
| CI/CD Execution | Select suite/control, run it, apply gates and retain evidence |
| Agentic QE / STLC Orchestration | Requirement review -> risk analysis -> test analysis/design -> governed dataset proposal |

## Dataset and CI model

SUT evaluation datasets are organized by execution purpose, not inheritance:

- **PR Critical — 10 cases:** fast merge-blocking risk subset;
- **Regression — 15 cases:** stable behavior and fixed-defect health on main;
- **Nightly Evaluation — 80 cases:** broad AI-risk, edge and adversarial signal;
- **Golden — 35 cases:** trusted canonical baseline / release validation.

Golden is not merely a fourth execution suite. It represents canonical expected behavior and has separate governance.

A separate **Judge Calibration Dataset — 8 human-reviewed cases** tests the evaluator rather than the SUT.

Current CI operating state:

```text
PR Critical        = automatic merge gate
Regression         = manual-only
Nightly            = manual-only
Release Validation = manual-only: Golden + broad Nightly + Release Quality Gate
```

## Core governing rules

```text
Formal assertion -> deterministic Python.
Meaning / behavior judgment -> semantic LLM Judge.
Validate dataset/oracle contracts before expensive model calls.
Retrieve broadly -> select relevant evidence -> send narrowly to an agent.
Agent-generated dataset changes remain proposals until human-approved promotion.
```

Golden is canonical truth under separate governance. PR Critical, Regression and Nightly are execution-purpose suites. Automated generation of Playwright/Cypress/API test code remains deferred from the current Agentic QE scope.

## Traceability target

```text
Requirement -> Risk -> Test -> Dataset -> Validation -> SUT Execution
-> Metric / Evidence -> Quality Gate -> Defect / Regression
-> Residual Risk -> Release Decision
```

Cross-cutting evidence should retain, where applicable: requirement/trace ID, model and prompt version, token usage, estimated cost, latency, retrieval/cache evidence, human approval history and quality-gate result.

## Documentation

- [`QUICKSTART.md`](QUICKSTART.md) — clone, configure and run locally;
- [`docs/master_architecture.md`](docs/master_architecture.md) — expanded master architecture and responsibility boundaries;
- [`docs/dataset_oracle_validation_pipeline.md`](docs/dataset_oracle_validation_pipeline.md) — dataset/oracle execution-precondition pipeline;
- [`docs/architecture.md`](docs/architecture.md) — detailed reference SUT/application architecture;
- [`docs/agentic_qe_orchestration.md`](docs/agentic_qe_orchestration.md) — focused Agentic QE orchestration;
- [`docs/automated_ai_evaluation.md`](docs/automated_ai_evaluation.md) — Oracle/evaluation details;
- [`docs/dataset_design.md`](docs/dataset_design.md) — dataset purposes and Oracle contract;
- [`docs/metric_contract.md`](docs/metric_contract.md) — canonical metric definitions and denominators;
- [`docs/test_strategy.md`](docs/test_strategy.md) — reusable test strategy including evaluator and dataset governance;
- [`docs/judge_calibration_workflow.md`](docs/judge_calibration_workflow.md) — OLD vs NEW Judge calibration contract and implementation;
- [`docs/golden_dataset_governance.md`](docs/golden_dataset_governance.md) — Golden truth governance and automated PR enforcement;
- [`docs/current_status.md`](docs/current_status.md) — concise implementation status;
- [`docs/documentation_index.md`](docs/documentation_index.md) — full documentation map.
