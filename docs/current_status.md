# Current Evaluation and Agentic QE Status

_Last synchronized with repository: 2026-09-01._

## Downstream QE framework — implemented

The Shopping RAG Assistant remains the executable reference SUT. The implemented QE framework includes deterministic constraint handling, FAISS retrieval, adaptive context selection, Claude generation, Dataset/Oracle Validation, deterministic Python assertions, semantic LLM Judge evaluation, metrics/risk aggregation, failure localization, telemetry, quality gates, Judge Calibration, Golden Governance, Metamorphic, Back-to-Back and Adversarial testing.

Current execution inventory:

```text
PR Critical standard = 10 (6 deterministic / 4 semantic)
Metamorphic Critical = 2 META records
Regression           = 15 (manual)
Broad Nightly        = 80 (manual)
Golden               = 35 canonical cases
Adversarial          = 10 (manual + nightly schedule)
Judge Calibration    = 8
Back-to-Back         = reuses 10 standard PR Critical cases
```

Broad Regression and Broad Nightly product schedules remain intentionally paused. Release Validation is manual.

## Upstream Agentic QE — implemented state

The upstream flow is no longer Requirements-Review-only.

```text
Jira Requirement
→ Requirements Review Agent
→ human readiness boundary / review-completed
→ Risk Analysis Agent
→ Prioritized Risk Register
→ human approval
→ approved Risk Register appended to Jira Description
→ risk-analysis-completed
→ Test Analysis & Design Agent
→ Dataset Health + Existing Coverage / Similarity
→ Proposed Test / Evaluation Assets
→ Human Decision workflow
→ APPROVE / REJECT / EDIT / EXTEND_EXISTING
→ explicit confirmation
→ decision evidence
```

### Requirements Review

Implemented: Jira batch input, deterministic eligibility before LLM, minimal semantic payload, structured READY / NEEDS_CLARIFICATION contract, content-aware cache, force-review bypass, prompt/model-sensitive invalidation, malformed-output handling, batch quality/cost telemetry and GitHub Step Summary evidence.

The current downstream Risk Analysis eligibility expects the `review-completed` Jira label. Automatic Requirements Review approval → Jira label write-back is not yet implemented and remains a future integration choice.

### Risk Analysis

Implemented: Jira batch input, deterministic eligibility requiring `review-completed` + Acceptance Criteria, content-aware per-ticket cache, force-analysis bypass, Claude semantic risk identification, Python Likelihood × Impact scoring and priority, mitigation, recommended test focus, prioritized Risk Register, token/cost telemetry and per-ticket error isolation.

Human approval is a hard mutation boundary. Risk Analysis itself does not modify Jira. The separate approval workflow writes the approved Risk Register to Jira Description and adds `risk-analysis-completed` only after explicit confirmation.

### Test Analysis & Design

Implemented: Jira/AC/reviewed-risk input, governed dataset snapshots (PR Critical, Regression, Nightly, Golden), deterministic dataset-health checks, existing coverage/similarity analysis, missing/extendable coverage proposals, traceability, Oracle assignment, target-suite recommendation and decision-package generation.

Output resilience includes a strict Pydantic contract, exact prompt schema, normalization of known LLM aliases, larger output budget, malformed/truncated JSON retry from original input and per-ticket failure isolation.

Proposal actions are agent recommendations:

- `ADD` — genuinely new coverage;
- `EXTEND_EXISTING` — modify an existing similar case instead of creating a duplicate;
- `SKIP` — existing coverage is sufficient.

### Human Decision workflow

Implemented as a separate `workflow_dispatch` continuation because a GitHub Actions Step Summary is not an interactive form. GitHub supports typed manual inputs including `choice` and `boolean`.

The workflow accepts Proposal ID, human decision (`APPROVE`, `REJECT`, `EDIT`, `EXTEND_EXISTING`), optional edited proposal JSON and an explicit confirmation boolean. It validates the decision and records decision evidence. Analysis alone never mutates a governed dataset.

## Current governance boundaries

```text
Requirements Review output
→ human readiness boundary
→ Risk Analysis eligibility

Risk Analysis proposal
→ explicit human approval
→ Jira Description write-back + risk-analysis-completed

Test Analysis proposal
→ explicit Human Decision workflow
→ decision evidence

Governed Dataset mutation
→ NOT YET IMPLEMENTED after Human Decision
```

Golden remains canonical truth under separate governance. Judge changes remain protected by Judge Calibration. Dataset/Oracle Validation remains a runtime technical contract check and does not replace human promotion governance.

## Remaining implementation work

Only work not yet implemented is listed here:

1. **Dataset promotion after Human Decision** — apply approved ADD, validated EDIT, or reviewed BEFORE → AFTER EXTEND_EXISTING; REJECT is a no-op.
2. **Post-mutation deterministic validation** — schema, IDs, references, Oracle contract and dataset integrity before promotion.
3. **Source-control promotion** — produce the governed dataset diff/commit/PR only after successful validation.
4. **Requirements Review Jira approval write-back** — optional automation for applying `review-completed`; currently external/manual.
5. **Targeted Risk evidence retrieval/RAG** — architecture/rules/policies/related specs/defects only when relevant; not a broad context dump.
6. **Agent Evaluation Dataset** — expected/prohibited actions, permissions, tool use and HITL behavior.
7. **State-driven multi-agent orchestration** — introduce after manual human gates are proven stable; do not force unconditional Agent 1 → Agent 2 → Agent 3 execution.
8. **Optional later integrations** — Confluence evidence, test-management system write-back and release/residual-risk automation where a real project requires them.

Drift testing remains intentionally outside the current roadmap.
