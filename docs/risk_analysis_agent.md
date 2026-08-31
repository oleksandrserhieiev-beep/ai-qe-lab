# Risk Analysis Agent

## Status

Initial skeleton / contract only. This slice defines the hand-off from Requirements Review to Risk Analysis without adding cross-document retrieval or automatic chaining.

## Entry gate

Risk Analysis may run only when the Requirements Review result is:

```text
READY
```

`NEEDS_CLARIFICATION` must return to requirement clarification and must not continue to risk analysis.

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

This PR intentionally does **not** add:

- Confluence/Jira cross-document RAG;
- Top-K retrieval;
- automatic execution immediately after Requirements Review;
- Test Analysis & Design Agent;
- Jira write-back;
- dataset mutation.

The next Risk Analysis slice should add targeted retrieval using the principle:

```text
Retrieve broadly -> select relevant evidence -> send narrowly to the LLM
```

Manual/Human governance remains the default POC control. Automatic chaining can be considered later only after the quality, confidence and cost characteristics are measured.