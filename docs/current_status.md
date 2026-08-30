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

## Active hardening work

1. Restore the pull-request workflow to the intended 10-case PR Critical merge gate after temporary broad verification.
2. Add Constraint Validation / Classification after Constraint Extraction so unresolved subjective input (for example `cheap` without a maximum price) returns deterministic clarification before retrieval.
3. Keep deterministic clarification distinct from deterministic abstention:
   - clarification = user input is unresolved and needs a value;
   - abstention = input is understood but governed evidence is insufficient.

## Next phase

After the current RAG/evaluation architecture is stable, continue with Jira integration and the Requirements Review -> AI Risk Analysis -> Test Design -> Governance workflow. Agent-generated approved cases feed the existing dataset validation, evaluation and CI framework rather than replacing it.
