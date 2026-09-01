# AI QE Lab — Test Strategy

_Last synchronized with repository: 2026-09-01._

## 1. Purpose and scope

The AI QE Lab demonstrates a reusable Quality Engineering framework around an AI-enabled SUT. The Shopping RAG Assistant is the executable reference SUT. The reusable outcome is governed requirements/risk/test design, datasets, deterministic and semantic Oracles, AI-specific test techniques, evaluator governance, CI/CD quality gates, observability, human approval and release evidence.

The strategy covers conventional testing, AI/RAG evaluation, Requirements Review, Risk Analysis, Test Analysis & Design, Human-in-the-Loop governance, Dataset/Oracle Validation, Metamorphic, Back-to-Back, Adversarial, Judge Calibration and Golden Governance.

## 2. Quality architecture

```text
UPSTREAM QE / STLC
Jira Requirement
→ Requirements Review
→ human readiness boundary
→ Risk Analysis
→ human Risk approval + Jira write-back
→ Test Analysis & Design
→ Human Decision
→ [next: governed dataset promotion]

DOWNSTREAM QUALITY EXECUTION
Governed Dataset
→ Dataset / Oracle Validation
→ SUT Execution
→ deterministic Python OR semantic LLM Judge
→ Metrics / Risk Aggregation
→ Quality Gate
→ Evidence / Lifecycle Decision
```

Agents produce decision support and proposals. Human approval remains the mutation boundary where specified. Dataset/Oracle Validation is a technical execution-precondition check and does not replace human governance.

## 3. Quality objectives

Testing must provide confidence that requirements are explicit enough for downstream design; material conventional and AI risks are identified; risks map to executable coverage; hard constraints and business rules are respected; retrieval/context/generation failures can be localized; hallucination and unsupported claims are detected; semantic outputs are grounded; hostile instructions cannot override governed truth; evaluator behavior remains calibrated; Golden truth cannot be silently moved; cost/latency/tokens remain observable; and merge/release decisions are supported by auditable evidence.

## 4. Risk-based test design

Conventional risks include functional, API/contract, integration, E2E, data integrity, resilience, security/privacy and performance/capacity failures.

AI/RAG risks include retrieval miss/noise, hard-constraint violation, context loss/insufficiency, semantic incorrectness, hallucination, poor groundedness, stale/conflicting evidence, out-of-domain behavior, prompt injection, malicious retrieved content, prompt leakage, non-deterministic instability, model/config regression and excessive latency/token/cost growth.

Evaluator risks include false PASS/FAIL, Judge model/prompt/rubric regression, malformed output, missing rationale and runtime configuration drift from the reviewed Judge contract.

## 5. Upstream Agentic QE strategy

### Requirements Review

Deterministic eligibility runs before paid semantic review. The agent evaluates requirement quality only; it must not use external evidence to conceal missing business behavior. Outputs are READY or NEEDS_CLARIFICATION with blocking gaps/questions. Content-aware caching avoids repeat LLM calls for unchanged semantic input.

### Risk Analysis

Risk Analysis is downstream of the readiness boundary. Eligibility requires `review-completed` and Acceptance Criteria. The LLM identifies risks; Python validates the contract and computes Likelihood × Impact score/priority. Output includes Risk, Mitigation and Recommended Test Focus. Risk Analysis itself is read-only; approved Risk Registers are written to Jira Description only through the explicit human-approval workflow, which adds `risk-analysis-completed`.

### Test Analysis & Design

The agent consumes AC + reviewed Risk Register + governed dataset snapshots. Dataset health is checked deterministically before semantic analysis. Existing coverage is analyzed for exact duplicate, similar coverage, already-covered behavior and gaps. Similarity is evidence for human review, not an automatic duplicate threshold.

Only missing or meaningfully extendable coverage is proposed. Every proposal carries Requirement/AC/Risk traceability, Oracle, target suite and rationale.

### Human Decision

Agent recommendation and human decision are separate concepts. Agent proposal actions are ADD / EXTEND_EXISTING / SKIP. Human decisions are APPROVE / REJECT / EDIT / EXTEND_EXISTING.

The actionable gate is a separate manual GitHub workflow with Proposal ID, decision choice, optional edited proposal JSON and explicit confirmation. The current implementation records validated decision evidence but does not yet mutate governed datasets.

## 6. Dataset strategy

| Asset | Current scope | Purpose |
|---|---:|---|
| PR Critical standard | 10 | fast merge-blocking high-risk evaluation |
| Metamorphic Critical | 2 | PR-level invariant checks |
| Regression | 15 | stable behavior + confirmed fixed defects |
| Broad Nightly | 80 | broad AI-risk / edge coverage |
| Golden | 35 | canonical trusted baseline |
| Adversarial | 10 | hostile-input robustness |
| Judge Calibration | 8 | evaluator regression truth |
| Agent Evaluation | planned | agent tools/permissions/HITL behavior |

Back-to-Back has no separate dataset; it reuses the 10 standard PR Critical cases.

Dataset size is not a quality objective. Coverage is justified by risk, criticality, defect history, execution time and cost.

## 7. Dataset / Oracle Validation

Before active SUT/Judge execution, selected governed cases must satisfy schema, unique identity, required fields, references, Oracle route and deterministic assertion requirements. Invalid technical contracts block execution. Runtime fallback is resilience, not a competing source of truth.

After Human Decision dataset promotion is implemented, the same deterministic validation principles must run after mutation and before the source-control change is promoted.

## 8. Oracle strategy

**Formal assertion → deterministic Python. Meaning/behavior judgment → calibrated semantic LLM Judge.**

Deterministic evaluation covers IDs, exact values, regex/patterns, hard constraints, catalogue/policy facts and Metamorphic invariants. Semantic evaluation covers Correctness, Groundedness, Hallucination, Context Coverage/Sufficiency and meaning-level adherence when deterministic proof is insufficient.

The Judge does not choose the Oracle. Semantic PASS/FAIL requires a short non-empty rationale.

## 9. Metrics and gates

Semantic metrics use only semantic/Judge cases in their denominator. Suite-wide/hybrid metrics include Overall Pass Rate, Retrieval Hit and Constraint Adherence where applicable. Current POC product thresholds remain provisional:

```text
Correctness >= 95%
Groundedness >= 95%
Retrieval Hit >= 95%
Constraint Adherence >= 95%
Hallucination <= 2%
```

Quality-gate decisions remain deterministic even when source evidence includes semantic Judge outputs.

## 10. AI-specific test techniques

- **Metamorphic:** controlled transformations with governed invariant relations; current PR subset has 2 META cases.
- **Back-to-Back:** same 10 standard PR cases against Model A and Model B; reports quality, regression, latency and token deltas.
- **Adversarial:** 10 governed hostile-input cases with Adversarial Pass Rate, Attack Success Rate, category outcomes and critical failures.
- **Judge Calibration:** OLD vs NEW evaluator against the same 8 human-reviewed truth cases.
- **Golden Governance:** protects canonical expected behavior from being changed merely to hide product failures.

Drift testing is intentionally outside the current roadmap.

## 11. CI/CD execution model

| Workflow | Trigger | Scope / decision |
|---|---|---|
| PR Critical Standard | PR | 10 cases; merge-blocking product gate |
| Metamorphic Critical | PR | 2 META cases; invariant gate |
| Back-to-Back | manual | model/config comparison |
| Adversarial | manual + nightly | hostile-input gate |
| Regression | manual currently | 15-case regression health |
| Broad Nightly | manual currently | 80-case broad AI-risk signal |
| Release Validation | manual / RC | Golden + broad evidence |
| Judge Calibration | Judge changes + manual | evaluator regression gate |
| Golden Governance | Golden changes | canonical truth change control |
| Requirements Review | manual batch | requirement-quality evidence |
| Risk Analysis | manual batch | prioritized risk evidence |
| Risk Jira Approval | manual explicit approval | approved Risk Register write-back |
| Test Analysis & Design | manual batch | coverage/test proposals |
| Human Decision | manual explicit choice | validated proposal decision evidence |

## 12. Entry / exit criteria

Lifecycle entry requires governed scope, valid dataset/Oracle contract, source data/environment, required model/secrets, telemetry and no blocking infrastructure defect. Exit requires planned scope execution, classified blocking failures, applicable gate outcome, retained evidence and acceptable residual risk.

Ticket/agent readiness is separate from release entry/exit criteria. Requirements Review and Risk Analysis have their own deterministic eligibility contracts.

## 13. Failure localization and defect policy

Investigate the first failing layer:

```text
Requirement / Agent eligibility
→ Human Governance
→ Risk/Test proposal contract
→ Dataset / Oracle Validation
→ Constraint handling
→ Retrieval
→ Context selection/building
→ Generation
→ Specialized relation/attack/comparison
→ Oracle / Judge
→ Metrics / Gate / Reporting
→ Governance control
```

A rerun is evidence about reproducibility, not permission to retry until green. Confirmed product defects should add permanent Regression coverage after the fix is verified.

## 14. Traceability

Target chain:

```text
Requirement
→ Acceptance Criterion
→ Risk
→ Proposed Test
→ Human Decision
→ Governed Test Asset
→ Oracle
→ Execution Evidence
→ Metric / Gate
→ Defect / Regression
→ Residual Risk
→ Release Decision
```

## 15. Remaining roadmap

Implemented orchestration items are intentionally excluded. Remaining work is:

1. confirmed Human Decision → governed dataset ADD/EDIT/EXTEND_EXISTING mutation;
2. deterministic post-mutation schema/integrity validation;
3. governed source-control diff/commit/PR promotion;
4. optional Requirements Review approval → `review-completed` Jira write-back;
5. targeted cross-document Risk Analysis retrieval where justified;
6. Agent Evaluation Dataset + agent-behavior evaluation;
7. state-driven orchestration after manual gates are proven stable;
8. optional Confluence/test-management/release integrations for real-project adoption.
