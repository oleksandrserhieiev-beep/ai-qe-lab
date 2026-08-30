# Current Evaluation Status

## Implemented on `main`

- Shopping RAG Assistant SUT with deterministic constraint extraction for supported product fields.
- Structured product filtering before semantic ranking when hard constraints are present.
- `all-MiniLM-L6-v2` embeddings and FAISS Top-K retrieval.
- Adaptive Context Selection with retained `0.30` minimum similarity threshold and separate Retrieval-K / Context-K evidence.
- Deterministic zero-match handling for structured constraints.
- Deterministic no-context abstention: `Context-K=0` skips the Claude SUT call and records zero SUT tokens/latency.
- Dataset/Oracle Validation for PR Critical, Regression and Nightly execution.
- Reviewed Oracle routing with safe fallback.
- Structured deterministic assertions for 61 cases (6 PR Critical, 7 Regression, 48 Nightly) and semantic LLM Judge routing for 44 cases.
- AI-risk/metric aggregation, quality gates, operational telemetry and failure-localization evidence.
- Case-scoped conflicting-policy fixture for Regression `R-014`; the production corpus remains unchanged.
- Pull-request evaluation is intentionally the 10-case PR Critical merge gate.

## Constraint Validation hardening

Constraint Validation / Classification and deterministic clarification are implemented in PR #37 and become part of `main` when that PR is merged.

The behavioral distinction is explicit:

- clarification = user input is unresolved and needs a governed value;
- abstention = input is understood but governed evidence is insufficient.

## CI execution policy

```text
PR Critical = fast merge gate
Regression  = main health gate
Nightly     = broad AI-risk signal
Golden      = trusted baseline / release validation
```

Documentation-only changes do not need to spend SUT/Judge tokens; the PR evaluation workflow is scoped to runtime code, data, datasets, policies, tests, workflow changes and dependency changes.

## Next phase

After the current RAG/evaluation architecture is stable, continue with Jira integration and the Requirements Review -> AI Risk Analysis -> Test Design -> Governance workflow. Agent-generated approved cases feed the existing dataset validation, evaluation and CI framework rather than replacing it.
