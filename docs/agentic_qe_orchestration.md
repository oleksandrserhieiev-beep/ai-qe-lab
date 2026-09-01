# Agentic QE Orchestration

_Last synchronized with repository: 2026-09-01._

## Purpose

This document is the repository source of truth for upstream Agentic QE/STLC orchestration. The SUT/evaluation pipelines remain independent downstream quality controls. Agents create decision-support evidence and proposed quality assets; humans retain mutation/approval boundaries where explicitly defined.

## Implemented orchestration

```text
Jira Requirement
        ↓
Requirements Review Agent
        ↓
READY / NEEDS_CLARIFICATION
        ↓ human readiness boundary
review-completed
        ↓
Risk Analysis Agent
        ↓
Prioritized Risk Register
Risk + Mitigation + Recommended Test Focus
        ↓ explicit human approval
Jira Description append
+ risk-analysis-completed
        ↓
Test Analysis & Design Agent
        ↓
Dataset Health
+ Existing Coverage / Similarity
+ Missing/Extendable Coverage
        ↓
Proposal / Traceability / Decision Package
        ↓
Human Decision workflow
APPROVE / REJECT / EDIT / EXTEND_EXISTING
        ↓ explicit confirmation
Decision Evidence
```

The next unimplemented boundary is **confirmed decision → governed dataset mutation/promotion**.

## Architectural rules

### Minimal context
Each agent receives only evidence required for its responsibility. Requirements Review evaluates the requirement itself. Risk Analysis may later use targeted external evidence, but broad Jira/Confluence/document dumps are prohibited. Test Analysis receives AC, approved/reviewed risks and governed dataset snapshots needed for coverage analysis.

### Deterministic before semantic
Use Python for input parsing, eligibility, schema/contract checks, risk scoring, dataset health, cache fingerprints, validation and mutation controls. Use the LLM where semantic reasoning adds value: requirement quality, risk identification and coverage/test-design reasoning.

### Human mutation boundaries
Semantic output is a proposal until the relevant human gate is passed.

```text
Risk proposal
→ human approval
→ Jira write-back

Test proposal
→ Human Decision
→ decision evidence
→ future dataset promotion
```

No analysis workflow is allowed to mutate governed datasets merely because an agent produced a proposal.

### Understand → Identify Risks → Design Tests
Responsibilities remain separated:

- Requirements Review: **Is the requirement sufficiently explicit?**
- Risk Analysis: **What can go wrong?**
- Test Analysis & Design: **What coverage should address the AC and reviewed risks?**
- Human Governance: **What is accepted, rejected, edited or used to extend existing coverage?**
- Dataset promotion: **What exact governed JSON change is applied?**

## Requirements Review — implemented

Manual GitHub Actions batch → parse/de-duplicate IDs → Jira retrieval → deterministic eligibility → minimal payload → content fingerprint/cache → Claude only on cache miss/force review → READY or NEEDS_CLARIFICATION → report/telemetry.

Cache invalidates when semantic Jira content, prompt, model or cache version changes. Ineligible tickets and matching cache hits spend zero LLM tokens.

Risk Analysis currently expects `review-completed`. Applying that label automatically after Requirements Review approval is not yet implemented.

## Risk Analysis — implemented

Eligibility requires Jira access, `review-completed` and non-empty Acceptance Criteria. Eligible tickets use per-ticket content-aware caching. Claude identifies conventional/AI risks; Python validates the contract and calculates Likelihood × Impact score/priority. Output includes mitigation and recommended test focus.

```text
Risk score = Likelihood (1..5) × Impact (1..5)
20–25 = CRITICAL
12–19 = HIGH
6–11  = MEDIUM
1–5   = LOW
```

Risk Analysis itself is read-only. A separate manual approval workflow performs Jira write-back only after explicit human approval: preserve existing Description → append `Reviewed Risk Register` → add `risk-analysis-completed`.

## Test Analysis & Design — implemented

Eligibility requires usable Jira content, Acceptance Criteria and reviewed Risk Register in Jira Description. The runtime loads governed PR Critical, Regression, Nightly and Golden snapshots and performs deterministic dataset-health checks before semantic analysis.

The agent compares AC + reviewed risks with existing coverage and returns exact/similar/already-covered/gap evidence. Similarity is decision support, never an automatic duplicate threshold. It proposes only missing or meaningfully extendable coverage and assigns traceability, Oracle and target suite with rationale.

Agent proposal actions:

- `ADD` — new coverage;
- `EXTEND_EXISTING` — existing similar case should be extended rather than duplicated;
- `SKIP` — coverage is already sufficient.

Runtime resilience includes strict Pydantic validation, exact output-schema instructions, deterministic normalization of known LLM aliases, larger output budget, malformed/truncated JSON retry from the original input and per-ticket failure isolation.

## Actionable Human Decision — implemented

GitHub Step Summary is evidence, not an interactive form. Therefore the human gate is a separate manually dispatched workflow using GitHub typed inputs.

Inputs:

```text
Issue key
Proposal ID
Decision: APPROVE | REJECT | EDIT | EXTEND_EXISTING
Optional edited proposal JSON
Confirm decision: true/false
```

`Run workflow` is the explicit confirmation action. The workflow validates the decision against the decision package and records decision evidence.

Decision semantics:

- APPROVE = accept proposed new case;
- REJECT = no change;
- EDIT = human modifies the proposal before addition;
- EXTEND_EXISTING = modify/merge the existing case using a reviewed BEFORE → AFTER change.

The current workflow **does not yet mutate the governed dataset**.

## Downstream handoff

After dataset promotion is implemented, the handoff remains:

```text
Approved governed dataset change
→ Dataset / Oracle Validation
→ SUT Execution
→ deterministic or semantic Oracle
→ Metrics / Risk Aggregation
→ Quality Gate
→ Evidence / lifecycle decision
```

Golden canonical truth and Judge Calibration remain separate governance systems.

## Remaining orchestration roadmap

Implemented items have been removed from this roadmap. Remaining work only:

1. Apply confirmed Human Decisions to governed JSON datasets.
2. For `EXTEND_EXISTING`, generate and validate the exact BEFORE → AFTER change; never concatenate blindly.
3. Validate schema, IDs, references, Oracle contract and integrity after mutation.
4. Produce a source-control diff/commit/PR for the validated dataset change.
5. Optionally implement Requirements Review approval → `review-completed` Jira write-back.
6. Add targeted Risk Analysis retrieval from architecture/rules/policies/related specs/historical defects where useful.
7. Add Agent Evaluation Dataset and evaluation of tool use, permissions, prohibited actions and HITL behavior.
8. Move from manually chained workflows to state-driven orchestration only after these human gates are stable and measurable.
9. Add Confluence/test-management/release integrations only when required by the target project.

Drift testing remains outside the current roadmap.
