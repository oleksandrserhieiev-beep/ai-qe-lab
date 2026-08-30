# AI QE Lab

Practical AI Quality Engineering lab for building, testing, evaluating, observing and governing AI-enabled systems.

## Quick start

New to the lab? Follow [`QUICKSTART.md`](QUICKSTART.md) to clone the repository, configure the local environment and run the project on Windows.

## What this lab is

The executable System Under Test (SUT) is a Shopping RAG Assistant. The main purpose of the repository is the QE framework around that SUT: governed datasets, dataset validation, deterministic and semantic evaluation, AI-risk evidence, CI quality gates, telemetry and failure localization.

Engineering owns the SUT implementation. QE defines risks and expected behavior, builds evaluation assets, executes the real SUT, evaluates evidence, gates quality and localizes failures.

## Master architecture

```text
User / Evaluation Case
        |
        v
+---------------------- SUT ----------------------+
| Constraint Extraction                           |
| -> Constraint Validation / Classification*      |
|    -> unresolved input -> Clarification*         |
| -> Structured Product Filtering when applicable |
| -> Embedding + FAISS Semantic Ranking            |
| -> Retrieval-K (Top-K candidates)                |
| -> Adaptive Context Selection                    |
| -> Context-K (0..K selected evidence)            |
|    -> 0 -> Deterministic Abstention               |
|    -> >0 -> Context Builder -> Claude -> Answer  |
+--------------------------------------------------+
        |
        | execution evidence
        v
Dataset Runner -> Automated Evaluation
               -> Oracle Resolution
                  -> deterministic -> Python assertions
                  -> semantic_llm  -> LLM Judge
               -> Metric / Risk Aggregation
               -> Quality Gate
               -> PASS / FAIL + reports

CI/CD selects the execution level:
PR Critical -> Regression -> Nightly -> Release Validation
```

`*` Constraint Validation / deterministic clarification is the next SUT hardening change and is tracked separately until merged. Deterministic abstention for `Context-K=0` is already implemented.

### Retrieval vs context

```text
Structured Filter = enforce exact known fields (price, color, waterproof, size, category)
Semantic Ranking  = rank eligible evidence by vector similarity
Retrieval-K       = up to 5 ranked candidates by default
Adaptive Selector = remove weak candidates below the governed threshold
Context-K         = evidence actually passed to generation
```

Defaults:

```text
RAG_TOP_K=5
RAG_MIN_CONTEXT_K=2       # target, not padding requirement
RAG_MAX_CONTEXT_K=5
RAG_MIN_SIMILARITY=0.30
```

## Four current QE execution concerns

| Concern | Purpose |
|---|---|
| SUT | Real Shopping RAG behavior under test |
| Dataset Validation | Reject invalid test/oracle contracts before model calls |
| Evaluation | Resolve Oracle, evaluate deterministic/semantic behavior, aggregate metrics and risks |
| CI/CD Execution | Select suite, run it, apply gates and retain evidence |

The future Agentic QE/Governance layer will create and govern requirements, risks, tests and datasets; it does not replace the evaluator.

## Dataset and CI model

Datasets are organized by execution purpose, not inheritance:

- **PR Critical — 10 cases:** fast merge-blocking risk subset;
- **Regression — 15 cases:** stable behavior and fixed-defect health on main;
- **Nightly Evaluation — 80 cases:** broad AI-risk, edge and adversarial signal;
- **Golden — 35 cases:** trusted baseline / release validation.

All active evaluation workflows validate the selected dataset before SUT/Judge model calls.

## Evaluation architecture

```text
Validated case
-> Oracle Resolution
   -> deterministic -> Python Deterministic Assertion Engine
   -> semantic_llm  -> LLM Judge
   -> missing       -> reviewed fallback registry
-> aggregation
-> Quality Gate
```

Current reviewed routing:

| Suite | Total | Deterministic | Semantic Judge |
|---|---:|---:|---:|
| PR Critical | 10 | 6 | 4 |
| Regression | 15 | 7 | 8 |
| Nightly | 80 | 48 | 32 |
| **Total** | **105** | **61** | **44** |

Semantic-only metrics (`Correctness`, `Groundedness`, `Hallucination`, `Context Coverage`, `Context Sufficiency`) use only the Judge population as denominator. Overall Pass Rate and Retrieval Hit are suite-wide. Constraint Adherence is hybrid across deterministic and semantic routes. Empty semantic populations are N/A, not 100%.

Quality gates currently enforce:

```text
Correctness >= 95%
Groundedness >= 95%
Retrieval Hit >= 95%
Constraint Adherence >= 95%
Hallucination <= 2%
```

## Target operating model

```text
Jira Requirement
-> Requirements Review / Entry Gate
-> AI Risk Analysis
-> Test Design
-> Governance / Human Approval
-> Governed JSON datasets / Test Management
-> Dataset Validation
-> Existing SUT + Evaluation + CI framework
-> Evidence / Defect / Regression
-> Release-readiness decision
```

Traceability target:

```text
Requirement -> Risk -> Test -> Dataset -> CI Execution
-> Metric / Evidence -> Quality Gate -> Defect / Regression
-> Residual Risk -> Release Decision
```

## Documentation

- [`QUICKSTART.md`](QUICKSTART.md) — clone, configure and run locally;
- [`docs/architecture.md`](docs/architecture.md) — canonical implemented/next architecture and separate pipelines;
- [`docs/current_status.md`](docs/current_status.md) — concise implementation status;
- [`docs/project_overview.md`](docs/project_overview.md) — end-state operating model;
- [`docs/automated_ai_evaluation.md`](docs/automated_ai_evaluation.md) — Oracle/evaluation details;
- [`docs/metric_contract.md`](docs/metric_contract.md) — canonical metric definitions and denominators;
- [`docs/test_strategy.md`](docs/test_strategy.md) — test strategy;
- [`docs/documentation_index.md`](docs/documentation_index.md) — documentation map.

## Governing rule

> **Formal assertion -> deterministic Python. Meaning/behavior judgment -> semantic LLM Judge. Always report the population actually measured.**
