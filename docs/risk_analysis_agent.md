# Risk Analysis Agent

## Status

**Requirements Review handoff, Risk Analysis execution, contract validation and controlled agent evaluation are implemented.**

Automatic Requirements Review -> Risk Analysis execution is intentionally not enabled yet. The existing handoff artifact remains the orchestration boundary: `READY` produces `READY_FOR_RISK_ANALYSIS`; `NEEDS_CLARIFICATION` remains blocked.

## Entry gate

```text
Requirements Review
├─ READY
│  └─ READY_FOR_RISK_ANALYSIS
│     └─ validated RiskAnalysisInput artifact
│        └─ Risk Analysis Agent (manual/controlled execution now)
└─ NEEDS_CLARIFICATION
   └─ BLOCKED
```

Risk Analysis accepts only `requirements_review_decision = READY`. This is enforced by the Pydantic input contract before any LLM call.

## Minimal-context handoff

Fields sent to Risk Analysis:

```text
issue_key
summary
description
acceptance_criteria
components
requirements_review_decision = READY
known_constraints
dependencies
retrieved_evidence = []
```

Operational Jira metadata is excluded unless future evidence shows that it materially improves risk decisions. `retrieved_evidence` is reserved for the later cross-document retrieval slice.

## Risk taxonomy

- functional
- integration
- data
- ai
- security
- resilience
- performance
- business

## Execution contract

`src/risk_analysis_agent.py` now performs the Anthropic LLM call using `config/risk_analysis_prompt.txt`. Model resolution is:

```text
RISK_ANALYSIS_MODEL
-> REQUIREMENTS_REVIEW_MODEL fallback
-> SUT_MODEL fallback
```

The execution path validates input before the call, requests compact JSON, tolerates fenced/embedded JSON, validates the complete output contract, checks that the returned issue key matches the input, and performs one bounded repair retry for malformed or contract-invalid output.

Telemetry includes model, latency, attempts, token usage and estimated cost.

## Output contract

Every execution must return at least one material risk. Each risk contains:

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

The result also contains:

```text
overall_risk_level
recommended_next_action = continue_to_test_analysis_and_design
```

## Agent evaluation

`datasets/risk_analysis_evaluation_dataset.json` is a small controlled evaluation asset for the Risk Analysis Agent itself. It currently covers functional/data filtering risk, AI/RAG grounding/constraint risk, and integration/resilience risk.

`src/evaluate_risk_analysis_agent.py` executes the agent and applies deterministic evaluation signals:

- expected risk-category recall;
- required test-focus term coverage;
- forbidden unsupported-claim terms;
- minimum/maximum risk-count bounds;
- execution telemetry (tokens/cost).

This is deliberately a bootstrap evaluation contract, not a claim that risk quality is fully solved. The dataset should grow from reviewed examples and observed agent failure modes. Human-reviewed expected risk truth can be added later if semantic risk-quality scoring becomes necessary.

The GitHub workflow `.github/workflows/risk-analysis-agent.yml` runs contract tests plus the controlled evaluation automatically when Risk Agent implementation/prompt/evaluation assets change, and also supports manual dispatch.

## Current boundary

Implemented:

- Risk Analysis input/output contracts;
- READY-only gate;
- Requirements Review handoff artifacts;
- Anthropic execution;
- bounded JSON/contract repair retry;
- telemetry and cost evidence;
- standalone handoff runner;
- controlled Risk Agent evaluation dataset and deterministic evaluation;
- PR/manual Risk Agent evaluation workflow.

Still intentionally later:

- Confluence/Jira cross-document retrieval / Top-K evidence selection;
- automatic Requirements Review -> Risk Analysis chaining;
- Test Analysis & Design Agent;
- Jira write-back;
- dataset promotion/mutation;
- multi-agent orchestration.

Targeted retrieval should follow the principle:

```text
Retrieve broadly -> select relevant evidence -> send narrowly to the LLM
```

Automatic chaining should be introduced only after the individual agent quality, confidence and cost characteristics are reviewed from controlled evaluation evidence.
