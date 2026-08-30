# Current Evaluation Status

## Implemented on `main`

- Shopping RAG Assistant reference SUT with deterministic constraint extraction for supported product fields.
- Constraint Validation / Classification for unresolved subjective-price input; deterministic clarification is returned before retrieval and Claude is skipped.
- Structured product filtering before semantic ranking when hard constraints are present.
- Deterministic no-product-match handling when valid hard constraints match zero catalogue products.
- `all-MiniLM-L6-v2` embeddings and FAISS Top-K retrieval.
- Adaptive Context Selection with `0.30` minimum similarity threshold and separate Retrieval-K / Context-K evidence.
- Deterministic no-context abstention: `Context-K=0` skips Claude and records zero SUT tokens/latency.
- Governed Golden, PR Critical, Regression and Nightly datasets.
- Dataset/Oracle Validation before active evaluation model calls, including Golden inside Release Validation.
- Reviewed Oracle routing with deterministic Python assertions or semantic LLM Judge evaluation.
- AI-risk/metric aggregation, quality gates, operational telemetry and failure-localization evidence.
- PR Critical merge-gate workflow.
- Regression workflow available via manual `workflow_dispatch`.
- Nightly workflow available via manual `workflow_dispatch`.
- Release Validation workflow available via manual `workflow_dispatch`, executing Golden + broad Nightly validation before the final Release Quality Gate.

## Deterministic early-response terminology

- **Clarification** — input is unresolved and the user must provide a governed value, for example a maximum price for `cheap`.
- **No-Product-Match** — resolved hard constraints match no catalogue products.
- **Abstention** — input is understood, but no governed evidence survives context selection (`Context-K=0`).

These paths are intentionally separate from normal Claude generation.

## Current CI execution state

```text
PR Critical        = automatic merge gate for meaningful PR changes
Regression         = manual-only
Nightly            = manual-only
Release Validation = manual-only: Golden + broad Nightly + Release Quality Gate
```

Documentation-only changes do not trigger the PR AI evaluation workflow.

The execution capability and the trigger policy are separate. Regression/Nightly schedules are intentionally paused while the POC baseline is stable and before Jira/Confluence-driven governance changes dataset lifecycle and release scope.

## Next phase

The next implementation phase is the upstream Agentic QE/Governance layer:

```text
Jira + Confluence
-> Requirements Review / Entry Gate
-> AI Risk Analysis
-> Test Design
-> Governance / HITL
-> Governed Dataset Update
-> existing Dataset Validation + SUT Execution + Evaluation + CI
-> Defect / Regression / Release Evidence
```

Agents create and govern quality inputs; they do not replace the independent evaluator or human release accountability.
