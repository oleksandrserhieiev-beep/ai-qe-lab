# AI QE Lab — Layered Metric Architecture

## Purpose

This document defines **where each metric belongs in the AI QE framework**. It separates product/SUT quality from evaluation-pipeline health, Judge quality and operational behavior, while preserving the existing RAG-stage diagnostic view.

The CI workflows (`PR Critical`, `Regression`, `Nightly`, `Release Validation`) are **execution levels / quality gates**. They are not metric layers. Each workflow can emit metrics from the layers below.

## Framework view

```text
                         AI QE FRAMEWORK
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
  SUT / PRODUCT         EVALUATION PIPELINE       JUDGE QUALITY
     QUALITY                  HEALTH                  HEALTH
        │                      │                      │
        │                      │                      │
        └───────────────┬──────┴───────────────┬─────┘
                        │                      │
                        ▼                      ▼
                  QUALITY GATE           OPERATIONAL
                                         METRICS

Execution levels using the same framework:
PR Critical → Regression → Nightly → Release Validation
```

## Layer 1 — SUT / Product Quality

This layer answers: **How well does the AI-enabled application behave?**

### Retrieval

- **Retrieval Hit Rate** — did retrieval return the expected product/source/evidence?
- **Constraint Match Score** — how well did retrieved candidates satisfy the structured constraints?
- **Constraint Precision@K** — what proportion of Top-K candidates satisfy the relevant constraints?
- Retrieval pass/fail evidence.

### Augmentation / Context

- **Retrieval-K → Context-K** — how many retrieved candidates survived adaptive context selection?
- Selected evidence IDs / similarity scores.
- Context atomic assertions.
- **Average Context Coverage** — how much expected evidence is represented in the supplied context?
- **Context Sufficiency Rate** — was the supplied context sufficient to answer correctly?

### Generation / Answer

- Generation atomic assertions.
- **Correctness Rate** — does the answer satisfy expected behavior?
- **Groundedness Rate** — are answer claims supported by supplied evidence?
- **Hallucination Rate** — how often does the answer introduce unsupported/fabricated claims?
- **Constraint Adherence Rate** — does the output respect explicit user/business constraints?

### End-to-end / Risk

- **Overall Pass Rate** — proportion of cases that passed all applicable checks.
- Passed / failed case counts.
- Risk count.
- Unclassified-risk cases.
- Risk-level / risk-category summary.

## Layer 2 — Evaluation Pipeline Health

This layer answers: **How are we measuring the SUT, and how much of the suite is actually measured by each mechanism?**

- Total executed cases.
- Applicable / measured case counts per semantic metric.
- Semantic metric pass counts.
- **Semantic Judge cases**.
- **Deterministic-only cases**.
- **Judge Call Reduction %**.
- Oracle route used per case (`deterministic` vs `semantic_llm`).
- Evaluation contract / parser failures where applicable.

Important denominator rule: semantic metrics such as Correctness, Groundedness, Hallucination, Context Coverage and Context Sufficiency are calculated only over cases actually judged semantically. Deterministic-only cases are excluded from those denominators.

## Layer 3 — Judge Quality / Evaluator Health

This layer answers: **Can we trust the semantic evaluator itself?**

The Judge is a probabilistic component and is evaluated against human-reviewed calibration truth.

- **Human Agreement** — proportion of expected Judge field decisions matching human-approved truth.
- **Matching Fields / Total Fields**.
- **False PASS** — Judge accepts a case that human truth says should fail.
- **False FAIL** — Judge rejects a case that human truth says should pass.
- Judge model identity.
- Prompt version.
- Rubric version.
- Calibration case count.
- Calibration response-attempt / contract-health signals.

Current implementation calculates these in `src/judge_calibration_runner.py` and stores the configuration identity alongside the calibration result.

### Calibration policy

Full calibration is required when evaluator behavior changes materially, for example:

- Judge model change;
- Judge prompt change;
- Judge rubric change;
- calibration truth / expected semantic contract change;
- evaluator parsing/contract logic change.

If none of those change, the main SUT regression suite does not need to rerun full Judge calibration on every execution. Periodic or Nightly Judge health checks can be used as a separate control if continuous evaluator-health evidence is required.

**Hallucination Rate is an SUT metric, not a Judge-health metric.** A low Hallucination Rate does not prove that the Judge is judging correctly. Judge Agreement / False PASS / False FAIL provide that evidence.

## Layer 4 — Operational Metrics

This layer answers: **How fast and expensive is the application/evaluation execution?**

- Average latency.
- P95 latency.
- Input tokens.
- Output tokens.
- Total tokens.
- Average tokens per case where reported.
- Cost / token-cost summary.
- Provider / retry telemetry where surfaced.

## RAG-stage diagnostic view

The layered taxonomy above does not replace the existing RAG diagnostic view. It explains **what kind of quality is being measured**; the RAG view explains **where in the SUT pipeline the signal originates**.

```text
RETRIEVAL
│  Retrieval Hit
│  Constraint Match
│  Constraint Precision@K
↓
AUGMENTATION / CONTEXT
│  Retrieval-K → Context-K
│  Selected IDs / scores
│  Context atomic assertions
│  Context Coverage
│  Context Sufficiency
↓
GENERATION
│  Generation atomic assertions
│  Correctness
│  Groundedness
│  Hallucination
│  Constraint Adherence
↓
END-TO-END / RISK
│  Overall Pass Rate
│  Risk outcomes
↓
OPERATIONS
   Average / P95 Latency
   Tokens
   Cost
```

## Legend

| Layer | Question answered | Typical metrics | Primary failure domain |
|---|---|---|---|
| **SUT / Product Quality** | Is the application behaving correctly? | Retrieval Hit, Constraint Match, Precision@K, Context Coverage/Sufficiency, Correctness, Groundedness, Hallucination, Constraint Adherence, Overall Pass, Risk | Retrieval, context selection/building, generation, application logic |
| **Evaluation Pipeline Health** | Are we measuring the right population with the right oracle? | measured/applicable counts, deterministic vs semantic routing, Judge cases, Judge Call Reduction, evaluation contract health | Oracle routing, aggregation, evaluator pipeline |
| **Judge Quality** | Can the semantic evaluator be trusted? | Human Agreement, Matching Fields, False PASS, False FAIL, calibration/config identity | Judge model, prompt, rubric, evaluator contract |
| **Operational** | Is execution acceptably fast and economical? | Average latency, P95, tokens, cost, retry/provider telemetry | Runtime/provider/cost behavior |

## How to read a run

Example Nightly interpretation:

```text
NIGHTLY
│
├─ SUT / PRODUCT QUALITY
│  Retrieval Hit       98%
│  Correctness         96% (32 judged)
│  Groundedness        97% (32 judged)
│  Hallucination        3% (32 judged)
│  Constraint Adherence 99%
│
├─ EVALUATION PIPELINE
│  Total                80
│  Deterministic        48
│  Semantic Judge       32
│  Judge Call Reduction 60%
│
├─ JUDGE QUALITY
│  Human Agreement      98%
│  False PASS            0
│  False FAIL            1
│
└─ OPERATIONAL
   Average latency       ...
   P95 latency           ...
   Tokens / cost         ...
```

Interpretation rules:

- Poor **Retrieval / Context / Generation** metrics indicate a SUT/application-quality problem.
- Poor **routing / measured population** signals indicate an evaluation-pipeline problem.
- Poor **Agreement / False PASS / False FAIL** indicate a Judge/evaluator-quality problem.
- Poor **latency / tokens / cost** indicate an operational problem.

This separation prevents a Judge defect from being misclassified as a product defect and prevents product hallucination metrics from being incorrectly used as evidence of Judge reliability.
