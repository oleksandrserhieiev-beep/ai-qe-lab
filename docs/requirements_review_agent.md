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

The Requirements Review POC is the first read-only agent slice. It is being validated before the framework expands into downstream agents.

Current behavior includes deterministic eligibility checks, minimal semantic payloads, content-hash reuse for unchanged requirements, structured readiness decisions, clarification gaps, and token/cost telemetry.

Not yet implemented:

- writing review results/labels back to Jira
- Confluence context retrieval
- orchestrator state transitions
- Risk Analysis Agent
- Test Generation Agent
- Human Approval → governed dataset lifecycle

## Planned Agentic QE evolution

The planned sequence after Requirements Review validation is:

```text
1. Complete Requirements Review POC validation
2. Add/confirm batch quality and cost summary
3. Freeze and document the validated Requirements Review architecture
4. Implement Risk Analysis Agent
5. Add targeted retrieval/RAG where Risk Analysis needs cross-document evidence
6. Implement Test Generation Agent
7. Connect generated test assets to the governed dataset lifecycle
8. Integrate the agentic flow with PR evaluation and regression workflows
```

### Risk Analysis Agent

Risk Analysis Agent is the next planned major agent after the Requirements Review POC is considered stable.

Entry condition:

```text
Requirements Review decision = READY
```

Primary responsibility: transform an approved requirement into a structured, risk-based QE view without prematurely generating the final test set.

Expected risk categories include, where applicable:

- functional
- integration
- data
- AI-specific
- security
- resilience
- performance
- business/process

Expected structured output should include at least:

- risk statement
- category
- likelihood
- impact
- priority
- rationale/evidence
- recommended test focus

Conceptual flow:

```text
READY Jira Story
      ↓
Risk Analysis Agent
      ↓
identify requirement-local risks
      ↓
retrieve supporting context when required
├─ architecture
├─ business rules / policies
├─ related specifications or stories
└─ historical defects
      ↓
structured risk register / risk output
      ↓
Test Generation Agent
```

### Retrieval boundary

Requirements Review intentionally evaluates whether the Jira requirement itself is sufficiently explicit. Retrieval must not hide missing acceptance criteria or compensate for an incomplete story.

Risk Analysis is the first planned stage where cross-document retrieval can add material value. The design principle is:

```text
Retrieve broadly → select relevant evidence → send narrowly to the LLM
```

Retrieval should therefore be introduced only when the downstream agent requires external evidence, with bounded top-K/context selection and observable retrieval telemetry.

### Test Generation Agent

After risks are identified, Test Generation Agent will use the validated requirement, structured risks, and only the relevant supporting context to produce risk-based test scenarios/test assets. Generated assets then enter the governed dataset lifecycle rather than being treated as automatically approved truth.
