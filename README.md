# AI QE Lab

Practical AI Quality Engineering lab for building, testing, evaluating, observing and governing AI-enabled systems.

## Quick start

Follow [`QUICKSTART.md`](QUICKSTART.md) to clone, configure and run the lab.

## What this lab is

The executable reference SUT is a Shopping RAG Assistant. The primary outcome is the reusable QE framework around it: governed requirements/risks/test assets, Dataset/Oracle Validation, deterministic and semantic evaluation, AI-risk evidence, evaluator calibration, canonical-truth governance, CI quality gates, telemetry, failure localization and Agentic QE/STLC orchestration.

## Current architecture

```text
UPSTREAM AGENTIC QE
Jira Requirement
→ Requirements Review
→ human readiness boundary / review-completed
→ Risk Analysis
→ human Risk approval
→ approved Risk Register → Jira Description + risk-analysis-completed
→ Test Analysis & Design
→ proposal / traceability / decision package
→ Human Decision workflow
→ APPROVE / REJECT / EDIT / EXTEND_EXISTING
→ explicit confirmation + decision evidence
→ [next: governed dataset promotion]

DOWNSTREAM QUALITY EXECUTION
Governed Dataset
→ Dataset / Oracle Validation
→ SUT Execution
→ deterministic Python OR semantic LLM Judge
→ Metrics / Risk Aggregation
→ Quality Gate
→ Evidence / Lifecycle Decision
```

Requirements Review, Risk Analysis and Test Analysis & Design are runnable. The Risk Jira write-back is approval-gated. Test-asset Human Decision is actionable through a separate GitHub `workflow_dispatch` choice/confirmation workflow. Test Analysis itself never mutates governed datasets.

See [`docs/agentic_qe_orchestration.md`](docs/agentic_qe_orchestration.md), [`docs/master_architecture.md`](docs/master_architecture.md) and [`docs/current_status.md`](docs/current_status.md).

## Governed evaluation assets

| Asset | Scope | Execution purpose |
|---|---:|---|
| PR Critical standard | 10 | automatic merge gate |
| Metamorphic Critical | 2 | PR invariant gate |
| Regression | 15 | manual regression health |
| Broad Nightly | 80 | manual broad AI-risk evaluation |
| Golden | 35 | canonical release/reference truth |
| Adversarial | 10 | manual + nightly hostile-input gate |
| Judge Calibration | 8 | evaluator regression gate |
| Back-to-Back | reuses 10 PR cases | manual model/config comparison |
| Agent Evaluation | planned | agent tools/permissions/HITL behavior |

Broad Regression/Nightly product schedules remain intentionally paused. Drift testing is outside the current roadmap.

## Core engineering rules

- deterministic/formal checks stay in Python;
- semantic reasoning uses LLMs only where it adds value;
- deterministic eligibility runs before paid semantic agent execution;
- content-aware caches avoid unchanged repeat calls;
- human approval is required before governed/external mutations where defined;
- Golden truth and Judge behavior have independent governance;
- similar coverage is evidence, not an automatic duplicate decision;
- one failed ticket should not crash an entire agent batch;
- preserve model/prompt/token/cost/evidence traceability.

## Human Decision semantics

Agent recommendation and human decision are separate.

```text
Agent: ADD / EXTEND_EXISTING / SKIP
Human: APPROVE / REJECT / EDIT / EXTEND_EXISTING
```

APPROVE adds new coverage; REJECT changes nothing; EDIT modifies the proposal before addition; EXTEND_EXISTING applies a reviewed BEFORE → AFTER change to an existing case.

## Current remaining roadmap

Implemented work is not repeated here. Remaining slices only:

1. confirmed Human Decision → governed dataset mutation;
2. deterministic post-mutation validation;
3. governed dataset diff/commit/PR promotion;
4. optional Requirements Review approval → Jira `review-completed` write-back;
5. targeted cross-document retrieval for Risk Analysis where useful;
6. Agent Evaluation Dataset and agent-behavior evaluation;
7. state-driven multi-agent orchestration after manual gates are stable;
8. optional Confluence/test-management/release integrations.

## Documentation

- [`docs/test_strategy.md`](docs/test_strategy.md) — test strategy and quality governance.
- [`docs/master_architecture.md`](docs/master_architecture.md) — top-level architecture.
- [`docs/agentic_qe_orchestration.md`](docs/agentic_qe_orchestration.md) — agent responsibilities, human gates and remaining orchestration.
- [`docs/current_status.md`](docs/current_status.md) — executable current state.
- [`docs/architecture.md`](docs/architecture.md) — detailed Shopping RAG SUT architecture.
- [`docs/automated_ai_evaluation.md`](docs/automated_ai_evaluation.md) — evaluation/Oracle/Judge design.
- [`docs/adversarial_testing_contract.md`](docs/adversarial_testing_contract.md) — adversarial testing contract.
