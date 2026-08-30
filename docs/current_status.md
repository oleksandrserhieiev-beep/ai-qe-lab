# Current Evaluation Status

## Implemented on `main`

- Shopping RAG Assistant SUT with deterministic constraint extraction for supported product fields.
- Constraint Validation / Classification for unresolved subjective price input; deterministic clarification is returned before retrieval and the Claude SUT call is skipped.
- Structured product filtering before semantic ranking when hard constraints are present.
- `all-MiniLM-L6-v2` embeddings and FAISS Top-K retrieval.
- Adaptive Context Selection with `0.30` minimum similarity threshold and separate Retrieval-K / Context-K evidence.
- Deterministic zero-match handling for structured constraints.
- Deterministic no-context abstention: `Context-K=0` skips the Claude SUT call and records zero SUT tokens/latency.
- Dataset/Oracle Validation for PR Critical, Regression and Nightly execution.
- Reviewed Oracle routing with deterministic Python assertions or semantic LLM Judge evaluation.
- AI-risk/metric aggregation, quality gates, operational telemetry and failure-localization evidence.
- Pull-request evaluation uses the PR Critical merge gate.

## Deterministic early-response terminology

- **Clarification** — input is unresolved and the user must provide a governed value, for example a maximum price for `cheap`.
- **No-product-match response** — resolved hard constraints match no catalogue products.
- **Abstention** — input is understood, but no governed evidence survives context selection (`Context-K=0`).

These paths are intentionally separate from normal Claude generation.

## CI execution policy

```text
PR Critical = fast merge gate
Regression  = main health gate
Nightly     = broad AI-risk signal
Golden      = trusted baseline / release validation
```

Documentation-only changes do not need SUT/Judge evaluation and are excluded from the PR evaluation workflow trigger.

## Next phase

Continue toward Jira integration and the Requirements Review -> AI Risk Analysis -> Test Design -> Governance workflow. Approved agent-generated cases will feed the existing dataset validation, evaluation and CI framework rather than replacing it.
