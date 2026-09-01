# AI QE Lab — Master Architecture

_Last synchronized with repository: 2026-09-01._

## Purpose

This is the compact top-level architecture. Detailed branching belongs to the pipeline documents; the master view intentionally shows responsibility boundaries without becoming a spaghetti diagram.

## Master architecture

```mermaid
flowchart LR
    subgraph UP["Agentic QE / STLC"]
        J["Jira Requirement"] --> RR["Requirements Review"]
        RR --> RG["Human readiness gate"]
        RG --> RA["Risk Analysis"]
        RA --> RAG["Human risk gate"]
        RAG --> TD["Test Analysis & Design"]
        TD --> HD["Human Decision"]
        HD --> DP["Decision Evidence"]
    end

    DP -. "NEXT: validated promotion" .-> GTA["Governed Test Assets"]

    subgraph EXEC["Product Quality Execution"]
        GTA --> DV["Dataset / Oracle Validation"]
        DV --> SUT["SUT Execution"]
        SUT --> OR["Oracle Resolution"]
        OR --> MET["Metrics + Risk"]
        MET --> QG["Quality Gate"]
        QG --> E["Evidence / Decision"]
    end

    JG["Judge Calibration"] -. "validates evaluator" .-> OR
    GG["Golden Governance"] -. "protects canonical truth" .-> GTA
```

The upstream and downstream systems are deliberately separated. Agents propose quality assets; governed assets enter product execution only after human governance and technical validation.

## Canonical pipeline map

| Pipeline | Responsibility | Detailed document |
|---|---|---|
| Agentic QE orchestration | Requirement → risk → test proposal → human decision | `agentic_qe_orchestration.md` |
| Reference SUT / RAG | Constraint → retrieval → context → generation, including deterministic exits | `architecture.md` |
| Dataset / Oracle Validation | Technical contract before paid execution | `dataset_oracle_validation_pipeline.md` |
| Product evaluation | Oracle routing → Python/Judge → metrics/gate | `automated_ai_evaluation.md` |
| Judge governance | OLD vs NEW evaluator against human truth | `judge_calibration_workflow.md` |
| Golden governance | Canonical expected-truth change control | `golden_dataset_governance.md` |
| Specialized AI testing | Metamorphic, Back-to-Back, Adversarial | `future_ai_testing_workflows.md` |

## Implemented upstream responsibilities

| Stage | Deterministic responsibilities | Semantic responsibilities | Mutation boundary |
|---|---|---|---|
| Requirements Review | input/eligibility, cache, contract, telemetry | requirement quality, gaps/questions | no automatic Jira approval write-back yet |
| Risk Analysis | eligibility, cache, L×I scoring, priority, contract | risk identification, mitigation/test-focus proposals | explicit approval writes Risk Register to Jira |
| Test Analysis & Design | dataset health, cache, contract normalization/retry, failure isolation | coverage/similarity reasoning, test proposals, Oracle/suite rationale | analysis never mutates datasets |
| Human Decision | proposal lookup, decision validation, explicit confirmation | human judgment | decision evidence only; promotion is next slice |

## Governed asset model

| Asset | Scope / state |
|---|---|
| PR Critical standard | 10 |
| Metamorphic Critical | 2 |
| Regression | 15, manual |
| Broad Nightly | 80, manual |
| Golden | 35 canonical cases |
| Adversarial | 10, manual + nightly |
| Judge Calibration | 8 evaluator cases |
| Back-to-Back | reuses 10 PR cases |
| Agent Evaluation | planned |

Golden is canonical truth, not an ordinary execution tier. Judge Calibration tests evaluator quality, not product quality.

## Cross-cutting architecture rules

- deterministic Python owns formal contracts and exact decisions;
- LLMs own semantic reasoning where meaning-level judgment is required;
- deterministic eligibility runs before paid semantic calls;
- content-aware caches avoid unchanged repeat calls;
- prompts/models/cache versions participate in invalidation;
- human approval precedes governed/external mutation where defined;
- agent batches isolate per-ticket failures;
- similarity is evidence, not an automatic duplicate verdict;
- Judge quality and Golden truth have independent governance;
- no retry-until-green policy.

## Remaining architecture work

Only unimplemented items remain:

1. confirmed Human Decision → governed dataset ADD/EDIT/EXTEND_EXISTING mutation;
2. deterministic post-mutation validation;
3. source-control dataset diff/commit/PR promotion;
4. optional Requirements Review approval → Jira `review-completed` write-back;
5. targeted cross-document Risk evidence retrieval where useful;
6. Agent Evaluation Dataset and agent-behavior evaluation;
7. state-driven multi-agent orchestration after manual gates are stable;
8. optional Confluence/test-management/release integrations.

Drift testing remains outside the current roadmap.
