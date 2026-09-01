# AI QE Lab — Test Strategy

_Last synchronized with repository: 2026-09-01._

## 1. Purpose and scope

The AI QE Lab demonstrates a reusable Quality Engineering framework around an AI-enabled SUT. The Shopping RAG Assistant is the executable reference SUT. The strategy covers conventional testing, AI/RAG evaluation, upstream Agentic QE, HITL governance, governed datasets, deterministic and semantic Oracles, specialized AI testing, evaluator governance, CI/CD gates, observability and release evidence.

## 2. Quality architecture

```text
UPSTREAM QE / STLC
Requirement → Requirements Review → Human readiness
→ Risk Analysis → Human risk approval / Jira write-back
→ Test Analysis & Design → Human Decision → Decision Evidence
→ [NEXT: governed dataset promotion]

DOWNSTREAM QUALITY EXECUTION
Governed Dataset → Dataset / Oracle Validation → SUT
→ Python Assertions OR calibrated LLM Judge
→ Metrics / Risk → Quality Gate → Evidence / Lifecycle Decision
```

Agent output is decision support until the applicable human/governance boundary is passed. Dataset/Oracle Validation is a technical execution precondition, not a substitute for human promotion governance.

## 3. Quality objectives

Testing must provide evidence that:

- requirements are explicit enough for downstream design;
- material conventional and AI risks are identified and traceable;
- risks map to executable coverage;
- hard constraints/business rules are respected;
- retrieval/context/generation failures are localizable;
- hallucination/unsupported claims and hostile behavior are detected;
- semantic behavior is grounded and evaluator behavior remains calibrated;
- canonical Golden truth cannot move silently;
- latency/tokens/cost/errors are observable;
- merge/release decisions are auditable.

## 4. Risk model

Conventional: functional, API/contract, integration, E2E, data integrity, resilience, security/privacy, performance/capacity.

AI/RAG: retrieval miss/noise, hard-constraint violation, context loss/insufficiency, semantic incorrectness, hallucination, groundedness failure, stale/conflicting evidence, OOD behavior, prompt injection, malicious retrieved content, prompt leakage, non-determinism, model/config regression, latency/token/cost growth.

Evaluator: false PASS/FAIL, Judge model/prompt/rubric regression, malformed output, missing rationale, configuration drift.

## 5. Upstream Agentic QE strategy

### Requirements Review
Deterministic eligibility precedes paid semantic review. The agent evaluates the requirement itself and returns READY or NEEDS_CLARIFICATION. Cache hits and ineligible tickets use zero LLM calls. Human readiness remains the downstream boundary; automatic `review-completed` Jira write-back is not implemented.

### Risk Analysis
Requires `review-completed` + Acceptance Criteria. LLM identifies risks; Python validates and calculates Likelihood × Impact priority. Output contains Risk, Mitigation and Recommended Test Focus. Analysis is read-only; separate explicit approval writes the approved Risk Register to Jira and adds `risk-analysis-completed`.

### Test Analysis & Design
Consumes AC + reviewed Risk Register + governed PR/Regression/Nightly/Golden snapshots. Deterministic dataset health runs before semantic coverage reasoning. Existing coverage is classified as already covered, similar/extendable or gap. Similarity is evidence, never an automatic duplicate verdict. Proposals carry traceability, Oracle, target suite and rationale.

### Human Decision
Agent actions: `ADD / EXTEND_EXISTING / SKIP`. Human actions: `APPROVE / REJECT / EDIT / EXTEND_EXISTING`. The separate GitHub workflow requires Proposal ID + explicit confirmation and records decision evidence. Governed dataset mutation is the next implementation slice.

## 6. Dataset strategy

| Asset | Scope | Purpose / current execution |
|---|---:|---|
| PR Critical standard | 10 | automatic fast merge gate |
| Metamorphic Critical | 2 | automatic PR invariant gate |
| Regression | 15 | manual regression health |
| Broad Nightly | 80 | manual broad AI-risk evaluation |
| Golden | 35 | canonical release/reference truth |
| Adversarial | 10 | manual + nightly hostile-input gate |
| Judge Calibration | 8 | evaluator regression truth |
| Back-to-Back | reuses 10 PR | manual model/config comparison |
| Agent Evaluation | planned | tools/permissions/HITL behavior |

Routine product population = 105 standard cases: 10 PR + 15 Regression + 80 Broad Nightly. Golden, Adversarial, Metamorphic and Judge Calibration have separate governance/technique roles.

## 7. Dataset / Oracle Validation

Before active execution, governed cases must satisfy schema, unique identity, required fields, references, Oracle route and deterministic assertion requirements.

```text
deterministic      → assertions required
semantic_llm       → semantic route
missing Oracle     → warning + reviewed fallback
invalid Oracle     → ERROR
missing/duplicate ID → ERROR
```

After dataset promotion is implemented, the same deterministic validation must run **after mutation and before source-control promotion**.

## 8. Oracle strategy

**Formal assertion → deterministic Python. Meaning/behavior judgment → calibrated semantic LLM Judge.**

The Judge never selects the Oracle. Semantic PASS/FAIL requires a short non-empty rationale. Missing routing metadata can use the reviewed fallback registry; invalid explicit routing is an error.

## 9. Metrics and gates

Semantic metrics use only semantic/Judge cases in their denominator. Deterministic/hybrid metrics use their applicable populations. Current POC thresholds remain provisional:

```text
Correctness >= 95%
Groundedness >= 95%
Retrieval Hit >= 95%
Constraint Adherence >= 95%
Hallucination <= 2%
```

Quality-gate decisions remain deterministic even when source evidence contains semantic judgments.

## 10. AI-specific techniques

- **Metamorphic:** controlled transformations + governed invariant relations; 2 PR META cases.
- **Back-to-Back:** same 10 PR standard cases against Model A/B; quality/regression/latency/token comparison.
- **Adversarial:** 10 hostile-input cases; pass rate, attack success rate, category outcomes, critical failures.
- **Judge Calibration:** OLD vs NEW evaluator against the same 8 human-reviewed truth cases.
- **Golden Governance:** prevents canonical expected behavior from being rewritten to hide product failures.

Drift testing is outside the roadmap.

## 11. CI/CD execution model

| Workflow | Trigger | Decision |
|---|---|---|
| PR Critical Standard | PR | merge-blocking product gate |
| Metamorphic Critical | PR | invariant gate |
| Back-to-Back | manual | model/config comparison |
| Adversarial | manual + nightly | hostile-input gate |
| Regression | manual | regression health |
| Broad Nightly | manual | broad AI-risk signal |
| Release Validation | manual / RC | Golden + broad evidence |
| Judge Calibration | Judge changes + manual | evaluator regression gate |
| Golden Governance | Golden changes | canonical truth control |
| Requirements Review | manual batch | requirement-quality evidence |
| Risk Analysis | manual batch | prioritized risk evidence |
| Risk Jira Approval | manual explicit approval | Risk Register write-back |
| Test Analysis & Design | manual batch | coverage/test proposals |
| Human Decision | manual explicit choice | validated decision evidence |

Broad Regression/Nightly product schedules are intentionally paused.

## 12. Entry / exit criteria

Lifecycle entry requires governed scope, valid dataset/Oracle contract, required source/environment/model configuration, telemetry and no blocking infrastructure defect. Exit requires planned scope execution, classified blocking failures, applicable gate result, retained evidence and acceptable residual risk.

Ticket/agent eligibility is separate from release entry/exit criteria.

## 13. Failure localization and defect policy

Investigate the first failing layer:

```text
Requirement / eligibility
→ Human governance
→ Risk/Test proposal contract
→ Dataset / Oracle contract
→ Constraint handling
→ Retrieval
→ Context selection/building
→ Generation
→ Specialized relation/attack/comparison
→ Oracle / Judge
→ Metrics / Gate / Reporting
→ Governance control
```

A rerun is reproducibility evidence, not permission to retry until green. Confirmed product defects should add permanent Regression coverage after verification.

## 14. Traceability

```text
Requirement → Acceptance Criterion → Risk → Proposed Test
→ Human Decision → Governed Test Asset → Oracle
→ Execution Evidence → Metric / Gate → Defect / Regression
→ Residual Risk → Release Decision
```

## 15. Documentation / architecture ownership

- `master_architecture.md` — compact system-level map.
- `agentic_qe_orchestration.md` — detailed agent eligibility/cache/HITL decision flows.
- `architecture.md` — reference SUT/RAG + downstream evaluation decisions.
- `dataset_oracle_validation_pipeline.md` — dataset technical contract.
- `automated_ai_evaluation.md` — Oracle/evaluator mechanics and metric populations.
- `judge_calibration_workflow.md` — evaluator governance.
- `golden_dataset_governance.md` — canonical truth governance.

This ownership prevents contradictory duplicated diagrams.

## 16. Remaining roadmap

Only unimplemented work:

1. confirmed Human Decision → governed dataset ADD/EDIT/EXTEND_EXISTING mutation;
2. exact BEFORE → AFTER handling for EXTEND_EXISTING;
3. deterministic post-mutation schema/reference/Oracle/integrity validation;
4. governed source-control diff/commit/PR promotion;
5. optional Requirements Review approval → `review-completed` Jira write-back;
6. targeted Risk evidence retrieval where justified;
7. Agent Evaluation Dataset + agent behavior evaluation;
8. state-driven orchestration after manual gates are stable;
9. optional Confluence/test-management/release integrations.
