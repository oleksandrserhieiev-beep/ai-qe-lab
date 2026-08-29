# AI QE Lab — Current Metric Contract

This document is the canonical repository-level definition of the metrics produced by the current AI evaluation framework. It describes what each metric measures, which pipeline layer it belongs to, who calculates it, and — critically — what denominator is used.

## Core rule

**A percentage is only meaningful together with its applicable population.**

A suite may contain deterministic and semantic cases. Semantic metrics are not silently projected across deterministic cases. If PR Critical contains 10 cases but only 4 are routed to the LLM Judge, then `Groundedness 100%` means `4/4 judged`, not `10/10`.

If a semantic metric has zero applicable cases, it is **N/A**, not `100%`.

## Current metric architecture

| Metric / evidence | Purpose | Pipeline layer | Calculated by | Type | Denominator / population |
|---|---|---|---|---|---|
| Overall Pass Rate | Whether each complete evaluation route passed | Case / suite | Python aggregation | Hybrid | All executed cases |
| Retrieval Hit Rate | Whether expected retrieval evidence/source was found | Retrieval | Python | Deterministic | All executed cases |
| Constraint Match Score | How well the best retrieved product satisfies detected structured constraints | Retrieval / filtering | Python | Deterministic | Cases with applicable structured constraints |
| Constraint Precision@K | How much of retrieved product Top-K fully satisfies all detected structured constraints | Retrieval / ranking | Python | Deterministic | Cases with applicable structured constraints |
| Retrieval candidate K | Number of retrieval candidates retained for diagnostics | Retrieval | Python telemetry | Deterministic | Per case |
| Selected Context-K | Number of retrieved candidates actually passed toward generation | Adaptive Context Selection | Python | Deterministic | Per case |
| Selected context IDs / scores | Which evidence survived adaptive selection and why | Adaptive Context Selection | Python | Deterministic | Per case |
| Context atomic assertions | Whether formal required evidence survives into selected/constructed context | Context / augmentation | Deterministic Assertion Engine | Deterministic | Deterministic cases carrying applicable assertions |
| Average Context Coverage | Whether supplied context contains the information required for expected behavior | Context / augmentation | LLM Judge | Semantic | Judged cases only |
| Context Sufficiency Rate | Whether context is sufficient to answer without inventing unsupported facts | Context / augmentation | LLM Judge | Semantic | Judged cases only |
| Generation atomic assertions | Whether formal expected facts/IDs/rules survive into the generated answer | Generation | Deterministic Assertion Engine | Deterministic | Deterministic cases carrying applicable assertions |
| Correctness Rate | Whether the generated answer is substantively correct | Generation | LLM Judge | Semantic | Judged cases only |
| Groundedness Rate | Whether generated claims are supported by supplied evidence | Generation | LLM Judge | Semantic | Judged cases only |
| Hallucination Rate | Frequency of unsupported semantic claims | Generation | LLM Judge | Semantic | Judged cases only |
| Constraint Adherence Rate | Whether user/business constraints are respected | Retrieval / generation | Python on deterministic route; LLM Judge on semantic route | Hybrid | All executed cases |
| Semantic Judge cases | How many cases require semantic evaluation | Oracle routing | Python | Deterministic aggregation | All executed cases |
| Deterministic-only cases | How many cases use Python oracle only | Oracle routing | Python | Deterministic aggregation | All executed cases |
| Judge call reduction | Fraction of cases where Judge invocation is avoided | Oracle routing / cost | Python | Deterministic aggregation | All executed cases |
| AI Risk Summary pass rate | Outcome grouped by canonical AI risk | Risk reporting | Python over route results | Hybrid | Cases carrying each risk |
| Risk Groundedness | Semantic grounding outcome for one risk | Risk reporting | Python aggregation of Judge results | Semantic | Semantic cases carrying that risk only |
| Risk Hallucination | Semantic hallucination outcome for one risk | Risk reporting | Python aggregation of Judge results | Semantic | Semantic cases carrying that risk only |
| Average latency | Mean SUT latency | Operations | Python from telemetry | Deterministic measurement | Cases with latency telemetry |
| P95 latency | 95th percentile SUT latency | Operations | Python from telemetry | Deterministic measurement | Cases with latency telemetry |
| SUT input/output/total tokens | Generation token consumption | Operations / cost | API telemetry + Python | Deterministic measurement | All SUT calls |
| Judge input/output/total tokens | Judge token consumption | Operations / cost | API telemetry + Python | Deterministic measurement | Judge calls only |
| Total tokens | Combined SUT + Judge tokens | Operations / cost | Python | Deterministic measurement | Current run |
| Estimated cost / case | Standard-price estimate based on configured models and token counts | Operations / cost | Python | Deterministic calculation | Current run |

## How to read PR Critical output

For a 10-case PR Critical suite with 6 deterministic and 4 semantic cases:

```text
Overall Pass Rate: 100% (10/10)
Retrieval Hit Rate: 100% (10/10)
Correctness Rate: 100% (4/4 judged)
Groundedness Rate: 100% (4/4 judged)
Constraint Adherence Rate: 100% (10/10)
Hallucination Rate: 0% (0/4 hallucinated; 4 judged)
Average Context Coverage: 100% (4 judged)
Context Sufficiency Rate: 100% (4/4 judged)
```

The semantic percentages describe the four cases that actually used the Judge. They do not claim semantic evaluation of the six deterministic cases.

## Evolution of the metric model

The project did not start with this complete contract.

### Initial scorecard

The first scorecard focused mainly on:

- PASS / FAIL;
- Retrieval Hit;
- Correctness;
- Groundedness;
- Hallucination;
- Constraint Adherence;
- latency and token usage.

This was useful for a first baseline but insufficient for failure localization. A good final answer could hide weak retrieval, and one overall semantic score could not explain where evidence was lost.

### Retrieval diagnostics added

After Top-K experiments and structured filtering were introduced, the framework added:

- Constraint Match Score;
- Constraint Precision@K.

These metrics diagnose exact structured-constraint quality independently from final answer quality.

### Context diagnostics added

The framework then added:

- Context Coverage;
- Context Sufficiency.

These isolated whether retrieval evidence was actually sufficient for generation.

### Oracle routing changed metric denominators

Once cases were manually classified into deterministic and semantic Oracle routes, semantic metrics stopped being suite-wide measurements. Deterministic cases now store semantic fields as `None` and are excluded from semantic denominators.

This is why the current report always exposes judged-case counts.

### Deterministic Assertion Engine added formal evidence

The deterministic route evolved from broad retrieval/constraint checks into atomic assertions across:

```text
Retrieval -> Selected/Constructed Context -> Generation
```

Formal facts, IDs, booleans, numeric values, catalogue logic and structured constraints no longer require an LLM Judge merely to obtain a PASS/FAIL result.

### Adaptive Context Selection added another observable layer

Retrieval Top-K and generation Context-K are now separate. The framework therefore also records:

- candidate K;
- selected Context-K;
- selected IDs/scores;
- similarity threshold configuration.

This allows a retrieved-but-filtered document to be diagnosed as a context-selection issue rather than a retrieval or generation defect.

### Operational and cost reporting matured

Token reporting evolved from one rough total into separate SUT and Judge consumption, combined totals and optional standard-price estimates. Judge-call reduction is now a first-class optimization metric.

## Superseded interpretations

The following interpretations are no longer valid:

- `Groundedness 100%` does **not** mean every case in a mixed suite was semantically grounded; it means every **judged** case passed Groundedness.
- `Correctness 100%` is not a 10/10 semantic score when only 4 cases were judged.
- `Hallucination 0%` is calculated over judged cases only.
- Context Coverage and Context Sufficiency are semantic Judge metrics in the current implementation, not deterministic suite-wide metrics.
- Constraint Adherence is no longer Judge-only; it is hybrid across deterministic and semantic routes.
- Retrieval Top-K is not the same as generation Context-K after Adaptive Context Selection.
- An empty semantic population is N/A, not an implicit 100% PASS.

## Quality-gate interpretation

Current blocking thresholds are:

```text
Correctness >= 95%           # semantic population when applicable
Groundedness >= 95%          # semantic population when applicable
Retrieval Hit >= 95%         # all executed cases
Constraint Adherence >= 95%  # all executed cases / hybrid route
Hallucination <= 2%           # semantic population when applicable
```

Critical-case failures can additionally block the run. If a semantic metric has no applicable cases, the metric is reported as N/A and the semantic threshold is not fabricated from an empty population.

## Governing principle

> **Formal assertion -> deterministic Python. Meaning/behavior judgment -> semantic LLM Judge. Always report the population that was actually measured.**
