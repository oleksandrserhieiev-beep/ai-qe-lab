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
- Version-controlled Judge configuration: model, Judge prompt and rubric are approved Git assets rather than silent runtime-only behavior.
- Human-reviewed Judge Calibration Dataset with 8 known good/bad cases covering correctness, groundedness, hallucination and constraint adherence.
- Automated OLD vs NEW Judge Calibration workflow for Judge model/config/prompt/rubric/calibration changes, plus manual `workflow_dispatch`.
- Initial approved Judge baseline: `claude-opus-5` + prompt `v1` + rubric `v1`, with 100% agreement across 32 expected field judgments, 0 false PASS and 0 false FAIL in the bootstrap calibration run.
- Judge calibration response hardening: invalid/empty JSON handling, bounded retries, raw-response diagnostics and response-attempt telemetry.
- Deterministic Golden Dataset Governance check requiring explicit `Golden Change Reason` and `Source of Truth` for governed Golden changes.
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
Judge Calibration  = automatic for Judge/calibration behavior changes + manual dispatch
Golden Governance  = automatic only for Golden dataset/check/workflow changes
```

### Judge Calibration automatic paths

```text
config/judge_config.json
config/judge_prompt.txt
config/judge_rubric.txt
datasets/judge_calibration_dataset.json
src/judge_calibration_runner.py
.github/workflows/judge-calibration.yml
```

On normal post-bootstrap Judge changes, the approved Judge from the PR base (`OLD`) and proposed Judge from the PR head (`NEW`) are evaluated against the same human-reviewed calibration truth. The current gate requires NEW agreement >= 90%, no agreement drop greater than 5 percentage points, and no increase in false PASS verdicts.

### Golden Governance automatic paths

```text
datasets/golden_dataset.json
src/golden_governance_check.py
.github/workflows/golden-governance.yml
```

A Golden-related PR must contain non-placeholder values for:

```text
Golden Change Reason: ...
Source of Truth: ...
```

A failing product evaluation is not a valid reason by itself to change canonical Golden expectations.

Documentation-only changes do not trigger PR AI evaluation, Judge Calibration or Golden Governance unless an executable workflow path itself is changed. The execution capability and trigger policy are separate. Regression/Nightly schedules are intentionally paused while the POC baseline is stable and before Jira/Confluence-driven governance changes dataset lifecycle and release scope.

## Governance boundary now implemented

```text
Product behavior
-> Dataset Validation
-> SUT Execution
-> Oracle / Judge
-> Product Quality Gate

Judge behavior change
-> OLD vs NEW Judge
-> Human Calibration Truth
-> Judge Calibration Gate

Golden truth change
-> Change Reason + Source of Truth
-> Golden Governance Check
```

This separates three questions that must not be conflated: **Is the product correct? Is the evaluator still trustworthy? Is the canonical expected truth being changed legitimately?**

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
-> existing Judge Calibration + Golden Governance controls
-> Defect / Regression / Release Evidence
```

Agents create and govern quality inputs; they do not replace the independent evaluator, evaluator calibration, deterministic governance checks or human release accountability.
