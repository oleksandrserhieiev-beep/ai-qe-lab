# Risk Analysis Agent

## Status

**Jira-driven manual Risk Analysis execution is implemented with deterministic eligibility checks, LLM risk identification, deterministic scoring, prioritized output, and human review.**

The Risk Analysis Agent remains intentionally simple: a user supplies one or more Jira issue keys, deterministic checks decide which tickets are eligible, the LLM identifies material risks for eligible tickets, Python calculates the score and priority, and the final register is reviewed by a person.

## Operational flow

```text
Jira issue keys (one or many; no configured batch-size limit)
        ↓
Eligibility check
        ↓
Ticket exists and is accessible?
Required review-completed label present?
Acceptance Criteria present and non-empty?
        ↓
Eligible tickets only
        ↓
Risk Analysis Agent (LLM)
        ↓
Functional / Non-functional / AI risks as applicable
        ↓
Likelihood 1-5 + Impact 1-5
        ↓
Python: Risk Score = Likelihood × Impact
        ↓
Python: deterministic priority + sort descending
        ↓
Prioritized Risk Register
        ↓
Human review / decision
```

If no ticket is eligible, the run reports `No eligible tickets for Risk Analysis` and does not call the LLM.

## Entry gate

Risk Analysis does not re-run Requirements Review. Jira acts as the operational gate for this version.

Default required label:

```text
review-completed
```

It can be overridden with `JIRA_REVIEW_COMPLETED_LABEL`.

A ticket is eligible only when:

1. the Jira issue key is valid and the issue can be loaded;
2. the required review-completed label is present;
3. Acceptance Criteria are present and non-empty.

The label is expected to be applied only after Requirements Review has been accepted/proceeded by a person. Jira write-back from the Requirements Review Agent itself is still a later orchestration step.

## Input

The manual GitHub Actions workflow accepts one required string input:

```text
issue_keys
```

Examples:

```text
AX-101
AX-101,AX-102,AX-103
AX-101 AX-102 AX-103
AX-101;AX-102;AX-103
```

The parser de-duplicates issue keys and has no configured maximum batch-size limit.

## Risk analysis responsibility

The LLM performs semantic risk identification from the eligible Jira requirement. It may return:

- functional risks;
- non-functional risks;
- AI-specific risks when AI behavior or dependency is actually present.

The prompt explicitly tells the model not to invent AI risks when the ticket has no AI behavior or AI dependency.

Risk categories remain:

- functional
- integration
- data
- ai
- security
- resilience
- performance
- business

Each risk contains:

```text
risk_id
risk_type
category
risk_statement
likelihood (1-5)
impact (1-5)
rationale
evidence[]
recommended_test_focus[]
```

## Deterministic scoring

The LLM does not calculate the final score or priority.

Python calculates:

```text
Risk Score = Likelihood × Impact
```

Priority is derived deterministically from the score:

```text
20-25 -> CRITICAL
12-19 -> HIGH
 6-11 -> MEDIUM
 1-5  -> LOW
```

Risks are sorted by Risk Score descending before the final table is rendered.

## GitHub Actions output

The workflow is split into explicit steps:

1. Validate ticket input
2. Eligibility check
3. Analyze eligible tickets
4. Likelihood × Impact scoring
5. Prioritized risk table
6. Upload Risk Analysis reports

GitHub Step Summary tables use centered Markdown alignment so values remain aligned under their columns.

The final Prioritized Risk Register contains:

```text
Rank
Issue
Risk Type
Category
Risk
Likelihood
Impact
Score
Priority
```

## Human review boundary

The Risk Analysis output is decision support, not an autonomous approval.

A person reviews the generated risk register and decides what to do next. Because human review is already mandatory in this version, no additional LLM-based semantic Risk Agent evaluator is executed in the operational workflow. This avoids spending extra tokens on a parallel AI review that does not replace the human decision.

Contract tests remain on pull requests because they are deterministic code checks and do not require an LLM call.

## Execution contract

`src/risk_analysis_agent.py` performs the Anthropic LLM call using `config/risk_analysis_prompt.txt`. Model resolution is:

```text
RISK_ANALYSIS_MODEL
-> REQUIREMENTS_REVIEW_MODEL fallback
-> SUT_MODEL fallback
```

The execution path validates input before the call, requests compact JSON, tolerates fenced/embedded JSON, validates the complete output contract, checks that the returned issue key matches the input, and performs one bounded repair retry for malformed or contract-invalid output.

Telemetry includes model, latency, attempts, token usage and estimated cost.

## Evaluation assets

The existing bootstrap controlled evaluation dataset and evaluator remain in the repository as development assets, but the operational Risk Analysis workflow no longer executes semantic Risk Agent evaluation automatically.

If later evidence shows that human review is insufficient or the agent becomes autonomous, the evaluation approach can be strengthened with human-reviewed expected risks and calibrated semantic matching.

## Still intentionally later

- Requirements Review Agent Jira label write-back after explicit human proceed;
- stale-content/hash validation for the review-completed label;
- Confluence/Jira cross-document retrieval / Top-K evidence selection;
- automatic Requirements Review -> Risk Analysis chaining;
- Test Analysis & Design Agent;
- multi-agent orchestration.
