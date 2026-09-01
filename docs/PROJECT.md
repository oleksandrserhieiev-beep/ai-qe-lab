# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. The Shopping RAG Assistant is the reference SUT used to prove the reusable QE framework; on a real project, the application pipeline would normally already exist and be owned by Development / AI Engineering.

The downstream framework combines governed datasets, Dataset/Oracle Validation, deterministic Python assertions, semantic LLM-as-a-Judge evaluation, AI-risk metadata, CI/CD quality gates, Metamorphic, Back-to-Back and Adversarial testing, operational telemetry, failure localization, Judge Calibration, Golden Governance and Release Validation.

## Current governed assets

```text
PR Critical standard = 10 (6 deterministic / 4 semantic)
Metamorphic Critical = 2 META records
Regression           = 15 (7 deterministic / 8 semantic)
Broad Nightly        = 80 (48 deterministic / 32 semantic)
Golden               = 35
Adversarial          = 10
Judge Calibration    = 8
Back-to-Back         = reuses 10 standard PR cases
```

Regression and Broad Nightly product schedules are currently manual; Adversarial remains manual + nightly scheduled. Drift testing is outside the current roadmap.

## Current Agentic QE orchestration

The upstream phase now implements three semantic agents plus explicit human gates:

```text
Jira Requirement
→ Requirements Review
→ human readiness boundary / review-completed
→ Risk Analysis
→ Prioritized Risk Register
→ explicit human approval
→ approved Risk Register → Jira Description + risk-analysis-completed
→ Test Analysis & Design
→ coverage/similarity/test proposals
→ Human Decision workflow
→ APPROVE / REJECT / EDIT / EXTEND_EXISTING
→ explicit confirmation + decision evidence
```

Requirements Review, Risk Analysis and Test Analysis & Design all use deterministic validation around semantic LLM reasoning. Content-aware caches avoid unnecessary repeated model calls. Risk scoring, eligibility, dataset health, contract validation and governance controls remain deterministic Python responsibilities.

The Human Decision workflow is a real manually dispatched GitHub gate using typed choice/boolean inputs. It complements the non-interactive Step Summary and makes the test-asset decision explicit and auditable.

## Remaining work

Implemented items are no longer treated as future roadmap. Remaining slices are:

1. confirmed Human Decision → governed dataset mutation for ADD / EDIT / EXTEND_EXISTING;
2. post-mutation deterministic dataset validation;
3. governed source-control diff/commit/PR promotion;
4. optional Requirements Review approval → `review-completed` Jira write-back;
5. targeted Risk Analysis retrieval/RAG where relevant;
6. Agent Evaluation Dataset and agent-behavior evaluation;
7. state-driven multi-agent orchestration after manual gates are stable;
8. optional Confluence/test-management/release integrations.

See `README.md`, `docs/current_status.md`, `docs/agentic_qe_orchestration.md`, `docs/test_strategy.md` and `docs/master_architecture.md` for detailed architecture and controls.
