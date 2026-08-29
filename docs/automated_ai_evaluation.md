# Automated AI Evaluation — Oracle Architecture

## Purpose

AI evaluation in this lab is automated test execution. Deterministic checks and LLM-as-a-Judge are two test-oracle mechanisms inside the same framework. The current SUT path includes retrieval candidates, adaptive context selection, context construction and Claude generation before Oracle evaluation.

The canonical metric definitions and denominators are maintained in `docs/metric_contract.md`.

## Pre-execution dataset validation

Before any active CI evaluation starts, the dataset is validated by `src/dataset_validator.py`.

```text
deterministic      -> valid; non-empty Deterministic Assertions required
semantic_llm       -> valid
missing/null/empty -> warning; runtime mapper fallback allowed
invalid non-empty  -> validation ERROR
missing/duplicate ID -> validation ERROR
```

PR Critical, Regression and Nightly all run this validation after dependency installation and before model calls.

## Oracle hierarchy

```mermaid
flowchart TD
    A[Validated Evaluation Case] --> O{Explicit Oracle?}
    O -->|deterministic| D[Deterministic Oracle]
    O -->|semantic_llm| S[Semantic Oracle]
    O -->|missing / null / empty| F[Fallback Registry: judge_routing.py]
    F --> ID[Normalize case_id / id / ID]
    ID --> M{Known reviewed ID?}
    M -->|deterministic| D
    M -->|semantic_llm| S
    M -->|unknown| S
    D --> P[Deterministic Assertion Engine]
    S --> J[LLM Judge]
    P --> R[Evaluation Aggregation]
    J --> R
    R --> G[Quality Gate]
```

The SUT LLM generates the application answer in both routes. The Oracle controls how that answer is evaluated, not whether the SUT runs.

> If a quality property can be represented as an objective, reproducible rule, evaluate it deterministically. Use an LLM Judge only when PASS/FAIL requires semantic interpretation of meaning or behavior.

| Oracle | Appropriate for | Examples |
|---|---|---|
| Deterministic Oracle | objective formal rules | IDs, numbers, booleans, ranges, schemas, structured constraints, exact policy facts, catalogue membership |
| Semantic Oracle | meaning and behavior | safe refusal, ambiguity handling, conflict interpretation, out-of-domain abstention, prompt-injection resistance, unsupported semantic claims |

The Judge never classifies Oracle type. An unknown mapping is conservatively routed to `semantic_llm` before the Judge is called.

## SUT evidence chain

```mermaid
flowchart LR
    Q[Query] --> R[Top-K Retrieval Candidates]
    R --> A[Adaptive Context Selection]
    A --> C[Constructed Context]
    C --> S[SUT LLM]
    S --> O[Output]
```

Retrieval candidates remain available for retrieval metrics. Only the adaptively selected subset is passed to the Context Builder and generation. This separation allows a failure to be localized to retrieval, context selection, context construction or generation.

## Deterministic Assertion Engine

Routing answers **who evaluates the case**. The engine answers **what Python must prove**.

```mermaid
flowchart LR
    R[Retrieval Assertions] --> C[Selected-Context Assertions]
    C --> G[Generation Assertions]
    R --> A[Aggregation]
    C --> A
    G --> A
    A --> L[First Failure Layer]
    L --> P[Case PASS / FAIL]
```

Supported assertion types include `retrieved_id`, `contains`, `regex`, `not_regex`, `no_constraint_match`, `answer_products_satisfy_constraints`, and `catalogue_min_price_product`.

All reviewed deterministic cases are migrated to structured atomic assertions:

| Suite | Total | Deterministic | Semantic LLM Judge |
|---|---:|---:|---:|
| PR Critical | 10 | 6 | 4 |
| Regression | 15 | 7 | 8 |
| Nightly Evaluation | 80 | 48 | 32 |
| **Total** | **105** | **61 (58.1%)** | **44 (41.9%)** |

Nightly deterministic assertions are loaded from `datasets/evaluation_assertion_metadata.json`. The 61/44 split is the currently implemented case-level routing model.

## Current metric population rules

The report intentionally uses different populations for different metrics.

| Metric | Evaluation mechanism | Population |
|---|---|---|
| Overall Pass Rate | Python aggregation across both routes | all executed cases |
| Retrieval Hit Rate | deterministic Python | all executed cases |
| Constraint Match / Precision@K | deterministic Python | applicable structured-constraint cases |
| Correctness | LLM Judge | semantic/Judge cases only |
| Groundedness | LLM Judge | semantic/Judge cases only |
| Hallucination | LLM Judge | semantic/Judge cases only |
| Context Coverage | LLM Judge | semantic/Judge cases only |
| Context Sufficiency | LLM Judge | semantic/Judge cases only |
| Constraint Adherence | deterministic Python or Judge depending on route | all executed cases |
| Judge call reduction | Python routing aggregation | all executed cases |

For PR Critical, the current split is 6 deterministic + 4 semantic. Therefore:

```text
Overall Pass 100%        = 10/10 complete routes
Retrieval Hit 100%       = 10/10 cases
Correctness 100%         = 4/4 judged, not 10/10
Groundedness 100%        = 4/4 judged, not 10/10
Hallucination 0%         = 0/4 judged cases hallucinated
Context Sufficiency 100% = 4/4 judged
Constraint Adherence 100%= 10/10 through hybrid route evaluation
```

Deterministic cases store semantic-only fields as `None` and are excluded from semantic denominators. If a run has zero semantic cases, those metrics are reported as **N/A**, not as an implicit `100%`.

## Semantic route

A semantic case can share exactly the same retrieval and context pipeline. The difference is that its expected behavior cannot be reduced to a complete objective assertion.

The Judge currently evaluates `correctness`, `groundedness`, `hallucination`, `constraint_adherence`, `context_coverage` and `context_sufficient`. Only the semantic route contributes to semantic-only metric denominators.

Example: two policies may be retrieved and preserved correctly, but the SUT must explain their interaction without unsupported assumptions. Retrieval/context evidence is still useful, while final behavioral PASS/FAIL requires the Judge.

## Quality-gate semantics

Current thresholds are:

```text
Correctness >= 95%           # semantic population when applicable
Groundedness >= 95%          # semantic population when applicable
Retrieval Hit >= 95%         # all executed cases
Constraint Adherence >= 95%  # all executed cases / hybrid route
Hallucination <= 2%           # semantic population when applicable
```

An empty semantic population is N/A and is not converted into a fabricated 100% score. Critical-case failures can additionally block the run.

## Probabilistic generation and re-runs

The SUT remains probabilistic even if retrieval and selected context are correct.

```mermaid
flowchart TD
    R[Retrieval PASS] --> C[Context PASS]
    C --> G{Generation correct?}
    G -->|yes| P[PASS evidence]
    G -->|no| RR[Controlled re-run]
    RR --> X{Reproducible?}
    X -->|intermittent| ST[Stochastic generation failure]
    X -->|repeated| SYS[Systematic generation failure]
```

A re-run measures reproducibility; it does not erase the original failure.

## Relationship to AI risk

```text
AI Risk           -> what quality failure are we protecting against?
Assertion         -> what exactly must be proven?
Oracle            -> what mechanism can prove it reliably?
Failure Layer     -> where did evidence first diverge?
Context Selection -> which retrieved evidence actually reached the SUT?
```

Risk-level semantic metrics use the same rule: the denominator is only the semantic cases carrying that risk. A deterministic-only risk group correctly reports semantic Groundedness/Hallucination as N/A.

## Engineering outcome

```text
Dataset Validation
-> RAG SUT execution
   -> Retrieval Candidates
   -> Adaptive Context Selection
   -> Context Builder
   -> SUT LLM
-> Oracle resolution
-> Deterministic Assertion Engine or Semantic Judge
-> Layer-level evidence + aggregation
-> Quality Gate
```

Benefits:

- malformed Oracle metadata fails before expensive execution;
- deterministic cases prove final expected facts without Judge calls;
- retrieval and generation context are independently observable;
- context-selection threshold mistakes are distinguishable from retrieval defects;
- semantic percentages expose their actual judged population;
- stochastic failures can be separated from systematic defects;
- the same governed structure can later be produced from Jira-driven agent workflows.

## Engineering rule

**Automate deterministically everything that can be expressed as an objective assertion. Use an LLM Judge only where the residual quality property genuinely requires semantic interpretation. Always report the population actually measured.**
