# Agentic QE Orchestration

_Last synchronized with repository: 2026-09-01._

## Purpose

Canonical source of truth for upstream Agentic QE/STLC orchestration. Agents create decision-support evidence and proposals; humans retain approval/mutation boundaries. Downstream SUT/evaluation remains an independent quality-control system.

## Overall implemented workflow

```mermaid
flowchart LR
    J["Jira Requirement"] --> RR["Requirements Review"]
    RR --> HR{"Human readiness?"}
    HR -->|proceed| RL["review-completed"]
    HR -->|clarify / reject| STOP1["Stop / requirement update"]
    RL --> RA["Risk Analysis"]
    RA --> RH{"Approve risks?"}
    RH -->|yes| JW["Risk Register → Jira\nrisk-analysis-completed"]
    RH -->|no| STOP2["No Jira mutation"]
    JW --> TD["Test Analysis & Design"]
    TD --> HD["Human Decision Workflow"]
    HD --> DE["Confirmed Decision Evidence"]
    DE -. "NEXT" .-> DP["Governed Dataset Promotion"]
```

The next unimplemented boundary is **confirmed decision → governed dataset mutation/promotion**.

## Architectural rules

- **Understand → Identify Risks → Design Tests.** Agent responsibilities remain separated.
- **Deterministic before semantic.** Python owns parsing, eligibility, contracts, scoring, cache, dataset health and mutation controls.
- **Minimal context.** Each LLM receives only evidence needed for its responsibility.
- **Human mutation boundaries.** Semantic output remains a proposal until the relevant human gate is passed.
- **Per-ticket isolation.** One failed ticket must not abort valid tickets in a batch where isolation is implemented.
- **No silent dataset mutation.** Test Analysis never changes governed assets.

## 1. Requirements Review Agent — implemented decision flow

```mermaid
flowchart TD
    A["Input Jira IDs"] --> B{"At least one valid ID?"}
    B -->|no| X1["FAIL input"]
    B -->|yes| C["Parse + de-duplicate"]
    C --> D["Load Jira ticket"]
    D --> E{"Eligibility satisfied?"}
    E -->|no| X2["INELIGIBLE\n0 LLM calls"]
    E -->|yes| F["Build minimal semantic payload"]
    F --> G{"Matching content fingerprint?"}
    G -->|yes| H["Reuse cached review\n0 LLM calls"]
    G -->|no / force_review| I["Claude Requirements Review"]
    H --> J{"Review decision"}
    I --> J
    J -->|NEEDS_CLARIFICATION| K["Blocking gaps + questions"]
    J -->|READY| L["READY evidence"]
    K --> M["Human / Jira requirement update\nthen re-run"]
    L --> N{"Human proceed?"}
    N -->|no| O["Stop / hold"]
    N -->|yes| P["review-completed\ncurrently manual/external"]
    P --> Q["Eligible for Risk Analysis"]
```

Requirements Review evaluates whether the Jira requirement itself is sufficient. External retrieval must not hide missing requirement behavior. Automatic approval → `review-completed` write-back is not implemented.

## 2. Risk Analysis Agent — implemented decision flow

```mermaid
flowchart TD
    A["Jira IDs"] --> B{"Ticket accessible?"}
    B -->|no| X1["INELIGIBLE"]
    B -->|yes| C{"review-completed present?"}
    C -->|no| X2["INELIGIBLE\n0 LLM calls"]
    C -->|yes| D{"Acceptance Criteria present?"}
    D -->|no| X3["INELIGIBLE\n0 LLM calls"]
    D -->|yes| E{"Matching content fingerprint?"}
    E -->|yes| F["Reuse cached Risk result\n0 LLM calls"]
    E -->|no / force_analysis| G["Claude Risk Analysis"]
    F --> H["Python contract + L×I scoring"]
    G --> H
    H --> I["Prioritized Risk Register\nRisk + Mitigation + Test Focus"]
    I --> J{"Human approves write-back?"}
    J -->|no| K["No Jira mutation"]
    J -->|yes| L["Append Reviewed Risk Register\nto Jira Description"]
    L --> M["Add risk-analysis-completed"]
    M --> N["Eligible input for Test Analysis"]
```

Risk Analysis itself is read-only. The separate approval workflow owns Jira mutation.

## 3. Test Analysis & Design Agent — implemented decision flow

```mermaid
flowchart TD
    A["Jira IDs"] --> B{"Ticket + AC available?"}
    B -->|no| X1["INELIGIBLE"]
    B -->|yes| C{"Reviewed Risk Register available?"}
    C -->|no| X2["INELIGIBLE"]
    C -->|yes| D["Load PR / Regression / Nightly / Golden snapshots"]
    D --> E{"Dataset health valid?"}
    E -->|blocking error| X3["BLOCK\nNo dataset mutation"]
    E -->|healthy / warning| F{"Matching content fingerprint?"}
    F -->|yes| G["Reuse cached analysis\n0 LLM calls"]
    F -->|no / force| H["Semantic coverage analysis"]
    G --> I{"Coverage state?"}
    H --> I
    I -->|already covered| J["SKIP proposal"]
    I -->|similar / extendable| K["EXTEND_EXISTING proposal"]
    I -->|coverage gap| L["ADD proposal"]
    J --> M["Traceability + Decision Package"]
    K --> M
    L --> M
    M --> N["Human Decision Workflow"]
```

Similarity is decision evidence, not an automatic duplicate threshold. Runtime resilience includes strict Pydantic validation, schema instructions, known-alias normalization, bounded malformed/truncated-output retry and per-ticket failure isolation.

## 4. Human Decision — implemented decision flow

```mermaid
flowchart TD
    A["Decision Package"] --> B["Select Issue + Proposal ID"]
    B --> C{"Human decision"}
    C -->|REJECT| R["No change"]
    C -->|APPROVE| AP["Accept proposed ADD"]
    C -->|EDIT| ED["Provide edited proposal JSON"]
    C -->|EXTEND_EXISTING| EX["Reviewed existing-case extension"]
    AP --> CF{"Explicit confirm = true?"}
    ED --> CF
    EX --> CF
    R --> EV["Decision Evidence"]
    CF -->|no| X["Stop / no mutation"]
    CF -->|yes| EV
    EV -. "NEXT implementation" .-> MUT["Apply governed dataset mutation"]
    MUT -.-> VAL["Post-mutation deterministic validation"]
    VAL -.-> PR["Dataset diff / commit / PR"]
```

`Run workflow` is the explicit confirmation action. Today the workflow validates and records the decision; the dotted promotion path is deliberately marked as future because dataset mutation is not implemented yet.

### Decision semantics

| Agent recommendation / human action | Meaning |
|---|---|
| ADD → APPROVE | add a new proposed case after promotion is implemented |
| SKIP / REJECT | no governed change |
| EDIT | human changes the proposed new case before addition |
| EXTEND_EXISTING | exact reviewed BEFORE → AFTER modification of an existing case |

## 5. Downstream handoff

```mermaid
flowchart LR
    A["Approved Governed Dataset"] --> V{"Dataset / Oracle valid?"}
    V -->|no| F["FAIL before model calls"]
    V -->|yes| S["SUT Execution"]
    S --> O{"Oracle"}
    O -->|deterministic| P["Python Assertions"]
    O -->|semantic_llm| J["Calibrated Judge"]
    P --> M["Metrics + Risk"]
    J --> M
    M --> G{"Quality Gate"}
    G -->|pass| E1["PASS Evidence"]
    G -->|fail| E2["FAIL + Localization"]
```

Golden canonical truth and Judge Calibration remain separate governance systems.

## Remaining orchestration roadmap

Only unimplemented work:

1. apply confirmed Human Decisions to governed JSON datasets;
2. generate exact BEFORE → AFTER change for `EXTEND_EXISTING`;
3. validate schema, IDs, references, Oracle contract and integrity after mutation;
4. produce governed dataset diff/commit/PR;
5. optionally automate Requirements Review approval → `review-completed` Jira write-back;
6. add targeted Risk evidence retrieval from architecture/rules/policies/specs/defects where justified;
7. add Agent Evaluation Dataset for tools, permissions, prohibited actions and HITL;
8. move to state-driven orchestration only after manual gates are stable and measurable;
9. add Confluence/test-management/release integrations only when required.

Drift testing remains outside the current roadmap.
