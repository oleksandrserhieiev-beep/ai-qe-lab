# Proposal — Agentic QE Orchestration with Human-in-the-Loop

## Status

**Proposal / future-state design. Not implemented yet.**

This note captures the intended orchestration model so it can be reviewed and implemented later without relying on chat history.

## Core principle

Agent output is evidence, not an automatic lifecycle approval.

Until empirical trust is established, every material agent gate uses mandatory Human-in-the-Loop (HITL).

```text
Agent produces evidence
        ↓
Human reviews
        ↓
Human approves / rejects
        ↓
Orchestrator records governed state
        ↓
Only then may the next lifecycle condition trigger downstream work
```

## Proposed Jira orchestration

```text
Jira Story
   │
   │ status → Ready for Refinement / Review
   ▼
Requirements Review Agent
   │
   ├── NEEDS_CLARIFICATION
   │       ↓
   │   Human Review
   │       ↓
   │   Story updated
   │       ↓
   │   Re-run Requirements Review
   │
   └── READY
           ↓
      Human Review  ← MANDATORY initially
           ↓
      Human APPROVES
           ↓
      label: requirements-reviewed
           ↓
      Story lifecycle continues
           │
           │ status = Development Started
           │ AND
           │ label = requirements-reviewed
           ▼
      Test Analysis / Risk Agent
           ↓
      Test Design Agent
           ↓
      Proposed Tests / Dataset Cases
           ↓
      Human Review  ← MANDATORY initially
           │
      ┌────┴────┐
      │         │
   Reject     Approve
      │         │
   Rework       ▼
           label: test-design-reviewed
                  ↓
             TMS / Dataset PR
```

## Why status and label are separate

A Jira status represents where the Story is in the delivery lifecycle.

A governance label represents that a specific AI-produced artifact has been reviewed and approved by a human.

Therefore downstream agents should use compound conditions rather than assuming that status alone proves approval.

Example:

```text
status == Development Started
AND
label contains requirements-reviewed
→ Test Analysis / Risk Agent may run
```

## Initial gate ownership

| Gate | Agent responsibility | Human responsibility | Orchestrator responsibility |
| --- | --- | --- | --- |
| Requirements Review | Produce structured findings and readiness recommendation | Approve/reject findings and readiness | Record approval state; prevent downstream trigger until approved |
| Test Analysis / Risk | Propose risks/test conditions | Validate material risks and coverage | Record approved analysis |
| Test Design | Propose tests/dataset cases | Approve/reject proposed tests | Record approval and trigger governed dataset/TMS flow |
| Dataset PR | Validate generated artifacts | Review/approve PR | Merge only through normal governance |

## Trust maturation

Do not move directly from mandatory HITL to autonomous approval.

### Stage 1 — Mandatory HITL

Every relevant agent result is reviewed by a person. Agent decisions are advisory.

### Stage 2 — Conditional HITL

Only empirically proven low-risk/high-confidence cases may proceed automatically. Ambiguous, high-risk, low-confidence, or policy-sensitive cases are escalated to a person.

### Stage 3 — Trusted automation

Approved classes of decisions may pass automatically. Human accountability remains through audit sampling, escalation, and governance controls.

## Evidence required before reducing HITL

Trust should be established separately for every agent capability.

Measure at minimum:

| Metric | Purpose |
| --- | --- |
| Agent/Human decision agreement | Overall alignment |
| False READY rate | Detect dangerous acceptance of incomplete requirements |
| False blocker rate | Detect unnecessary lifecycle stops |
| Gap precision | Findings accepted as valid by human reviewer |
| Missed-gap rate | Important findings discovered by human but missed by agent |
| Human override rate | How often the agent decision is changed |
| Rework after approval | Whether approved AI output later proves inadequate |

A trusted Requirements Review Agent does **not** imply a trusted Test Design Agent. Trust is capability-specific.

## Auditability requirements

For every governed transition, preserve:

- Story ID
- agent name/version
- model
- agent output
- token/cost/latency telemetry
- agent recommendation
- human reviewer identity/reference when available
- human approve/reject decision
- timestamp
- resulting Jira label/state transition
- downstream trigger

## Future implementation questions

Still to decide:

- exact Jira statuses used by the production workflow
- exact label names and whether labels or custom Jira fields are preferable
- approval UI/mechanism
- whether Risk Analysis and Test Design are separate HITL gates or one combined review initially
- criteria and sample size required to move from mandatory to conditional HITL
- confidence/calibration mechanism for agents
- audit retention policy

## Relationship to existing roadmap

The detailed target lifecycle remains in `docs/desired_next_steps.md`. This proposal adds the explicit governance rule that agent recommendations do not automatically advance the lifecycle while the system is still in the evidence-building stage.
