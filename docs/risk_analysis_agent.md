# Risk Analysis Agent

## Status

**Input/output contract and Requirements Review handoff are implemented; Risk Analysis execution remains a skeleton.**

The Requirements Review workflow now emits deterministic handoff artifacts after each batch. A `READY` review produces a validated minimal `RiskAnalysisInput` payload. `NEEDS_CLARIFICATION` produces a blocked handoff and cannot proceed to Risk Analysis.

This does not yet automatically execute the Risk Analysis Agent. Automatic chaining belongs to the later orchestration slice.

## Entry gate

Risk Analysis may run only when the Requirements Review result is:

```text
READY
```

`NEEDS_CLARIFICATION` must return to requirement clarification and must not continue to risk analysis.

Current handoff state:

```text
Requirements Review
├─ READY
│  └─ READY_FOR_RISK_ANALYSIS
│     └─ validated RiskAnalysisInput artifact
└─ NEEDS_CLARIFICATION
   └─ BLOCKED
      └─ no Risk Analysis input
```

The handoff artifact also carries Requirements Review traceability such as the review content hash, batch run ID and review timestamp. Jira write-back/labels are not required for the handoff contract and remain outside the current read-only Requirements Review boundary.

## Minimal-context hand-off

The Risk Analysis Agent follows the same cost/control principle as Requirements Review: send only the semantic context needed for the decision.

Current hand-off fields:

```text
issue_key
summary
description
acceptance_criteria
components
requirements_review_decision = READY
known_constraints
dependencies
retrieved_evidence = []   # reserved for the later targeted-retrieval slice
```

Operational Jira fields such as status, priority, labels, assignee and reporter are not part of the LLM hand-off unless a future risk contract proves they are materially needed.

## Risk taxonomy

- functional
- integration
- data
- ai
- security
- resilience
- performance
- business

## Output contract

Each material risk contains:

```text
risk_id
category
risk_statement
likelihood
impact
priority
rationale
evidence[]
recommended_test_focus[]
```

The complete result also contains `overall_risk_level` and `recommended_next_action = continue_to_test_analysis_and_design`.

## Current boundary

Implemented now:

- Risk Analysis input/output Pydantic contracts;
- `READY` entry gate;
- minimal semantic handoff payload;
- deterministic Requirements Review -> Risk Analysis handoff artifact generation;
- blocked handoff for `NEEDS_CLARIFICATION`;
- unit coverage for the handoff gate and Risk Analysis contracts.

Still intentionally not implemented:

- Risk Analysis LLM execution;
- Confluence/Jira cross-document RAG;
- Top-K retrieval;
- automatic execution immediately after Requirements Review;
- Test Analysis & Design Agent;
- Jira write-back;
- dataset mutation.

The next Risk Analysis slice should first review/harden this skeleton, then add agent execution. Targeted retrieval can follow using the principle:

```text
Retrieve broadly -> select relevant evidence -> send narrowly to the LLM
```

Manual/Human governance remains the default POC control. Automatic chaining should be introduced later through the multi-agent orchestrator after the individual agent quality, confidence and cost characteristics are measured.
