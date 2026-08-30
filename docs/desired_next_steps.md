# Desired Next Steps — Agentic AI QE Orchestration

## Purpose

This document is a working target-state note for the next phase of AI QE Lab.

It is intentionally written so that a future contributor or AI assistant can inspect the repository, read this file, understand where the POC is going next, and continue from the current architecture without relying on previous chat context.

This is a **desired target / working draft**, not a claim that all items below are already implemented.

---

## Current baseline

The existing repository already provides the core executable AI QE evaluation framework:

- Shopping RAG reference SUT
- deterministic constraint extraction and validation
- structured hard-constraint filtering
- FAISS semantic retrieval
- adaptive context selection
- deterministic clarification / no-product-match / abstention paths
- governed evaluation datasets
- dataset and Oracle validation
- deterministic Python assertions
- semantic LLM Judge routing
- AI quality/risk metrics
- operational telemetry including tokens, latency and cost reporting
- failure-localization evidence
- quality gates
- PR Critical, Regression, Nightly and Release Validation workflows

The next phase should **reuse this engine**, not rebuild it.

Target direction:

```text
Agentic QE / Governance Layer
        ↓
Governed Tests + Datasets
        ↓
Existing Dataset Validation
        ↓
Existing SUT / RAG Execution
        ↓
Existing Evaluation + Metrics + Quality Gates
        ↓
CI / Regression / Release Evidence
```

---

# 1. Target E2E lifecycle

```text
Jira Story / Requirement
        ↓
Ready for Refinement
        ↓
Requirements Review Agent
        ↓
Requirements Reviewed
        ↓
Test Analysis & Risk Agent
        ↓
Test Analysis Completed
        ↓
Test Design Agent
       / \
      /   \
Functional Tests     AI Evaluation Tests
      ↓                     ↓
Test Management       TMS Traceability
System                + Dataset Proposal
                            ↓
                       Human Approval
                            ↓
                        Dataset PR
                            ↓
                    Dataset Validation
                            ↓
                          Merge
                            ↓
                     Dataset Governed

Development / implementation proceeds
                            ↓
                      Feature PR Open
                            ↓
                       Orchestrator
                            ↓
              Story-specific PR Evaluation
                            +
                  Global Critical Smoke
                            ↓
                       Quality Gate
                       /          \
                    FAIL          PASS
                     ↓              ↓
              PR remains open      Merge
                     ↓              ↓
                  Fix/retry   Ready for Testing
                                    ↓
                             Functional / E2E QA
                                    +
                          Broader regression evidence
```

---

# 2. Agent model

## 2.1 Requirements Review Agent

### Trigger

Jira Story changes status to:

```text
Ready for Refinement
```

### Responsibilities

Review requirement quality before downstream test analysis starts.

Check at minimum:

- Summary / intent
- Description
- Acceptance Criteria
- ambiguity
- actors / flows
- dependencies
- business rules
- error / negative behavior where relevant
- missing information required for testability
- relevant NFR expectations where applicable

### Output

Structured result, for example:

```json
{
  "requirement_id": "AIQE-123",
  "entry_gate": "PASS",
  "readiness_score": 0.87,
  "gaps": [],
  "ambiguities": [],
  "missing_dependencies": []
}
```

### State transition

If review passes, add a governed state/label such as:

```text
Requirements Reviewed
```

If review fails, return gaps to refinement and do not continue automatically.

---

## 2.2 Test Analysis & Risk Agent

This should be broader than an "AI Risk Agent".

Its role corresponds to **Test Analysis — what needs to be tested**.

### Inputs

- reviewed requirement
- Acceptance Criteria
- architecture / integration information where available
- business rules
- known product risks
- relevant historical defects / risk register where available

### Responsibilities

Identify test conditions and risks across both conventional and AI-specific quality areas.

Examples:

### Functional / system risks

- incorrect business behavior
- invalid state transitions
- integration failures
- incorrect mappings
- missing validation
- unavailable downstream dependencies
- data quality / transformation issues

### AI-specific risks

- hallucination
- ungrounded response
- ignored hard constraint
- retrieval miss
- poor context selection
- non-deterministic instability
- stale/conflicting evidence
- business-rule violation
- prompt injection / adversarial behavior where relevant

### Output

Traceable relationship:

```text
Requirement
→ Test Condition
→ Risk
→ Priority
→ Required Coverage
```

When complete:

```text
Test Analysis Completed
```

Do **not** mark `Dataset Updated` here. Risk analysis does not itself update a governed dataset.

---

## 2.3 Test Design Agent

Its role corresponds to **Test Design — how the identified conditions/risks will be tested**.

### Inputs

- reviewed requirement
- identified test conditions
- functional/system risks
- AI risks
- coverage priorities

### Outputs

Two related test representations should be produced.

#### Functional tests

Create proposed functional/integration/E2E tests in the Test Management System.

Traceability:

```text
Requirement
→ Risk / Test Condition
→ Functional Test
```

#### AI evaluation tests

AI evaluation cases should also have human-readable traceability in the Test Management System, but their executable source should live as governed version-controlled datasets in GitHub.

Example traceability record:

```text
TMS Test: AIQE-T42
Requirement: STORY-123
Risk: RISK-AI-07
Type: AI Evaluation
Dataset Case ID: EVAL-0042
```

Executable dataset representation:

```json
{
  "id": "EVAL-0042",
  "requirement_ids": ["STORY-123"],
  "test_management_id": "AIQE-T42",
  "risk_ids": ["RISK-AI-07"],
  "suite": "pr_critical"
}
```

The Test Management System is the human-facing governance / traceability layer.
GitHub datasets are the executable AI evaluation artifacts.

---

# 3. Human approval and dataset governance

Generated tests must not immediately become governed production evaluation cases.

Target lifecycle:

```text
Test Design Agent
        ↓
Draft / Proposed Tests
        ↓
Pending Review
        ↓
Human Approval
        ↓
Test Design Approved
        ↓
Dataset Update / Sync
        ↓
Dataset Git Branch
        ↓
Dataset Pull Request
        ↓
Dataset Validation
        ↓
PR Review / Approval
        ↓
Merge
        ↓
Dataset Governed
```

A future implementation may provide an action such as:

```text
Approve Test Design
```

The exact UI/mechanism is still to be decided, but approval must be explicit and auditable.

`Dataset Updated` / `Dataset Governed` must only mean that the executable case is actually present in the approved version-controlled dataset, not merely that an agent proposed it.

---

# 4. Dataset strategy and traceability

AI tests should not live only in the Test Management System.

Use the following separation:

| Artifact | Primary home |
|---|---|
| Requirement | Jira |
| Test Analysis / Risk | Jira / governance metadata |
| Functional Test | Test Management System |
| AI Test human-readable traceability | Test Management System |
| Executable AI Evaluation Case | GitHub governed dataset |
| Evaluation results | CI / reports / artifacts |
| Defect | Jira |

Dataset cases should include traceability metadata such as:

- requirement ID(s)
- risk ID(s)
- TMS test ID
- suite
- Oracle route / assertion metadata as required

This enables:

```text
Requirement
→ Risk
→ Test
→ Dataset Case
→ Evaluation Result
→ Quality Gate
→ Defect / Regression Evidence
```

---

# 5. Feature PR evaluation strategy

AI evaluation should happen **before feature implementation is merged**, not only after a Story reaches Ready for Testing.

Expected sequence:

```text
Requirement
→ Risk Analysis
→ Test Design
→ Human Approval
→ Governed Dataset merged
→ Development
→ Feature PR opened
→ AI PR Evaluation
→ PASS
→ Feature PR merge
→ Ready for Testing
```

The feature PR workflow evaluates the unmerged implementation against already-approved expected behavior.

## Story-specific PR selection

Do not run the entire broad dataset for every feature PR.

Dataset cases should be linked to requirements.

For example:

```json
{
  "id": "EVAL-0042",
  "requirement_ids": ["STORY-123"],
  "risk_ids": ["RISK-AI-07"],
  "suite": "pr_critical"
}
```

For `STORY-123`, PR evaluation should approximately be:

```text
Story-specific PR Critical cases
+
small global critical smoke subset
```

If the quality gate fails:

```text
PR stays open
→ developer fixes
→ push
→ evaluation reruns
```

If it passes, the PR may proceed through normal review/merge governance.

---

# 6. CI/CD levels

Target execution model:

| Level | Purpose |
|---|---|
| Dataset PR | Validate dataset / Oracle metadata before governance merge |
| Feature PR | Story-specific AI Critical evaluation + global smoke; merge gate |
| Main / Regression | Stable broader regression evidence |
| Nightly | Broad AI-risk, edge and adversarial evaluation |
| Release Validation | Golden + broad validation + release quality evidence |

Schedules/cadence should remain configurable based on cost and product need.

Do not assume Nightly must literally run every night if the economics do not justify it.

---

# 7. Execution and Failure / Root Cause Analysis

Do not replace deterministic execution with an LLM agent.

The existing Python/CI evaluation engine remains responsible for execution:

```text
Dataset
→ Dataset Validator
→ SUT
→ Retrieval / Context Evidence
→ Oracle Resolution
→ Deterministic Assertions / LLM Judge
→ Metrics
→ Quality Gate
```

An **Execution / Failure Analysis capability** should consume the resulting evidence.

Responsibilities:

- inspect failed cases
- inspect retrieval evidence
- inspect adaptive context evidence
- inspect generated output
- inspect deterministic assertion / Judge evidence
- inspect provider/runtime failures
- identify likely failure domain
- produce a concise root-cause hypothesis with supporting evidence

Potential localization:

```text
Dataset / Oracle authoring
Constraint handling
Retrieval / ranking
Adaptive context selection
Context building
Generation / prompt / model
External provider
Evaluation / aggregation / quality gate
```

For confirmed product failures it may draft or create a Jira defect and link the failed case as a regression candidate.

A separate Defect Agent is optional; defect creation may initially be a capability of Failure Analysis.

---

# 8. Coverage & Gap Analysis

Add an independent **Coverage & Gap Analysis Agent**.

Purpose: do not simply trust that Risk Analysis and Test Design agents found everything.

Inputs:

```text
Stories / Requirements
+
Identified Test Conditions / Risks
+
Functional Tests
+
AI Evaluation Dataset Cases
```

Outputs should identify:

- requirement coverage
- risk coverage
- AI-risk coverage
- missing functional tests
- missing AI evaluation cases
- orphan tests
- uncovered requirements
- uncovered critical risks

Example:

```text
STORY-007

Requirement:
Recommend only products available in the customer's selected market.

Identified coverage:
✓ category
✓ hallucination
✓ price

Critical gap:
✗ market availability risk not identified
✗ no functional test
✗ no AI evaluation case
```

Potential gate:

```text
Critical uncovered risk
→ Test Design / Dataset Governance NOT READY
```

This agent should act as an independent verification layer over upstream agent outputs.

---

# 9. Orchestrator

The Orchestrator should coordinate agents and deterministic tooling; it should not become another monolithic "super agent".

Responsibilities:

- react to lifecycle triggers
- read/write workflow state
- call the correct agent/capability
- enforce gates
- stop downstream work on failed prerequisites
- request Human-in-the-Loop approval
- preserve shared structured state
- trigger dataset/CI actions
- maintain traceability
- record agent inputs, outputs, tool calls and approvals

Conceptually:

```text
                         ORCHESTRATOR
                              │
       ┌──────────────────────┼──────────────────────┐
       ↓                      ↓                      ↓
Requirements Review     Test Analysis/Risk      Test Design
       │                      │                      │
       └────────────── Shared Governed State ───────┘
                              │
                       Coverage Analysis
                              │
                          HITL Gate
                              │
                    Existing AI QE Engine
                              │
                    Failure / RCA Analysis
                              │
                       Governance Evidence
```

---

# 10. TM / Governance capability

A later governance layer may consume architecture, Jira, risk, test and execution evidence to support Test Management activities such as:

```text
Architecture + Jira + Risk Register
→ Test Strategy
→ Test Plan
→ Human Approval
→ Monitor Execution + Metrics
→ Test Completion Report
→ Release Recommendation
```

Human Test Lead / release stakeholders retain accountability for entry/exit criteria, accepted residual risk and final GO/NO-GO decisions.

---

# 11. Cost observability and ROI validation

Cost must become a first-class quality-engineering metric for the agentic phase.

The current evaluation framework already captures token/cost information for relevant evaluation calls. Extend this approach to every agent/capability.

Capture at minimum:

| Component | Cost evidence |
|---|---|
| Requirements Review | calls, input/output tokens, USD / Story |
| Test Analysis & Risk | calls, tokens, USD / Story |
| Test Design | calls, tokens, USD / Story |
| Coverage Analysis | calls, tokens, USD / Story |
| Dataset governance | calls, tokens, USD |
| SUT | USD / evaluation case/run |
| LLM Judge | USD / semantic case/run |
| PR Critical | USD / run |
| Regression | USD / run |
| Nightly | USD / run |
| Release Validation | USD / release |
| Failure Analysis | USD / failed run / Story |

Target release report:

```text
Release N

Stories:                    X
Requirements Review:        $X
Test Analysis:              $X
Test Design:                $X
Coverage Analysis:          $X
Evaluation SUT:             $X
LLM Judge:                  $X
Failure Analysis:           $X
Regression/Release runs:    $X
Retries:                    $X
──────────────────────────────
Total tokens:               X
Total AI QE Cost:           $X
Cost / Story:               $X
Cost / PR:                  $X
Cost / Release:             $X
```

---

# 12. Planned POC scale experiment

## Release 1 — baseline

Create/import **10 realistic Stories** with sufficiently complete requirements, Acceptance Criteria, business rules and dependencies.

Run them through the full target lifecycle:

```text
10 Stories
→ Requirements Review
→ Test Analysis / Risk
→ Test Design
→ Human Approval
→ TMS + Dataset Governance
→ Feature PR Evaluation
→ Regression / Release Validation
→ Cost + Coverage Report
```

Measure actual:

- number of agent calls
- tokens by component
- USD by component
- total USD
- cost per Story
- number of functional tests
- number of AI evaluation cases
- coverage/gaps
- evaluation execution cost
- retries / failures

## Scale experiment — 30 Stories total

Add another **20 Stories** and compare the resulting 30-Story scope with the 10-Story baseline.

Compare:

- total cost
- cost / Story
- dataset growth
- execution cost growth
- regression cost
- context/token growth
- number of retries
- coverage
- whether cost scales approximately linearly

This becomes the empirical basis for ROI decisions.

---

# 13. ROI decision after measurement

Do not assume every agent belongs in the final production architecture.

First:

```text
Build
→ Instrument
→ Run 10-Story Baseline
→ Scale to 30 Stories
→ Measure Real Cost
→ Compare Human Effort Saved
→ Calculate ROI
→ Optimize Target Architecture
```

Possible outcomes:

- keep Requirements Review if its quality/time savings justify cost
- reduce or remove it if it is expensive and low-value
- keep Risk/Test Analysis if it materially improves coverage
- keep Test Design if it saves substantial manual effort
- use cheaper models for simpler agent tasks
- escalate to stronger models only for ambiguous/complex cases
- keep deterministic Python for work that does not require LLM reasoning
- tune Regression/Nightly cadence according to cost/risk rather than naming convention

The existing dataset/evaluator/quality-gate framework remains valuable even if some upstream agents are later removed for economic reasons.

---

# 14. Desired target summary

The intended end state is not merely a RAG evaluation demo.

It is an E2E AI Quality Engineering lifecycle:

```text
Requirement
→ Requirements Quality Gate
→ Test Analysis / Risks
→ Test Design
→ Human Governance
→ Functional Tests + Governed AI Datasets
→ Coverage Verification
→ Feature PR AI Evaluation
→ CI Quality Gate
→ Functional / Integration QA
→ Regression / Nightly / Release Evidence
→ Failure / Root Cause Analysis
→ Defect / Regression Candidate
→ Test Management / Release Governance
→ Cost / ROI Evidence
```

Core principle:

> Agents create, analyze and govern quality inputs and evidence. Deterministic tooling and the existing evaluation framework execute repeatable checks. Humans retain approval and release accountability.

---

# 15. Immediate next implementation steps

Working order for the next phase:

1. Define shared orchestration state and traceability contract.
2. Integrate Jira / Confluence requirement ingestion and lifecycle triggers.
3. Implement Requirements Review Agent and `Requirements Reviewed` gate.
4. Implement Test Analysis & Risk Agent.
5. Implement Test Design Agent with TMS + dataset proposal outputs.
6. Implement explicit Human Approval → Dataset PR → Dataset Governed lifecycle.
7. Add Story ↔ Risk ↔ Test ↔ Dataset Case traceability metadata.
8. Add Story-specific Feature PR case selection + global critical smoke.
9. Implement Coverage & Gap Analysis Agent/gate.
10. Implement Failure / Root Cause Analysis over existing evaluation evidence.
11. Add TM / governance reporting capability as needed.
12. Extend token/cost telemetry to all agent calls.
13. Execute the 10-Story baseline release experiment.
14. Scale to 30 Stories total and measure cost/coverage/ROI.
15. Optimize the final agent mix and CI cadence based on empirical results.

This file should be updated as orchestration decisions are finalized.