# Requirements Review Agent

## Purpose

The Requirements Review Agent is the first executable component of the Agentic QE phase.

It treats Jira and Confluence as source systems, Anthropic as the intelligence layer, and Python as the orchestration/telemetry layer.

Current MVP flow:

```text
Jira Story
→ Jira ingestion / normalization
→ Requirements Review Agent
→ Anthropic API
→ structured review JSON
→ readiness gate evidence
```

The agent is read-only. It does not modify Jira.

## Input

One Jira issue key, for example:

```text
SCRUM-1
```

The Jira ingestion layer currently reads and normalizes:

- issue key
- summary
- description
- status
- issue type
- priority
- labels
- components
- assignee
- reporter
- parent key

Jira Atlassian Document Format descriptions are flattened into readable text before the requirement is sent to the model.

## Review contract

The agent returns a structured result with:

- `decision`: `READY` or `NEEDS_CLARIFICATION`
- `readiness_score`: 0-100
- short summary
- categorized gaps with severity
- clarification questions
- explicit known constraints
- explicit dependencies
- testability notes
- recommended next action

The core rule is that the model must not invent missing behavior. If meaningful test design would require material assumptions, the story is returned as `NEEDS_CLARIFICATION`.

## Configuration

Use `.env` values based on `config/.env.example`:

```text
LLM_API_KEY=...
REQUIREMENTS_REVIEW_MODEL=claude-sonnet-5
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=...
JIRA_API_TOKEN=...
```

`REQUIREMENTS_REVIEW_MODEL` falls back to `SUT_MODEL` if omitted.

## Run locally

From the repository root:

```bash
python src/run_requirements_review.py SCRUM-1
```

Optional explicit report path:

```bash
python src/run_requirements_review.py SCRUM-1 --output reports/requirements_review_SCRUM-1.json
```

## Telemetry

Each run records:

- agent name
- model
- input tokens
- output tokens
- total tokens
- cache token usage when available
- latency
- stop reason
- estimated USD cost
- Jira issue key
- normalized input requirement
- structured review result

This keeps agent execution inside the same observable orchestration boundary as the existing AI QE framework.

## Current boundary

This PR implements only the first read-only agent slice.

Not yet implemented:

- writing review results/labels back to Jira
- Confluence context retrieval
- orchestrator state transitions
- Risk Analysis Agent
- Test Design Agent
- Human Approval → governed dataset lifecycle

Those are added incrementally after the Requirements Review Agent is validated on real Jira stories.
