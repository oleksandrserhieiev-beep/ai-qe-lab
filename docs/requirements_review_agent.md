# Requirements Review Agent

## Status

**POC closure target: validated first Agentic QE component.**

The Requirements Review Agent is the first executable upstream component in the Agentic QE framework. It is read-only: it reviews Jira requirements but does not modify Jira.

Detailed current orchestration: `docs/agentic_qe_orchestration.md`  
Manual execution/validation instructions: `docs/manual_requirements_review_poc.md`

## Purpose

The agent answers one controlled question:

> Is this Jira requirement sufficiently explicit, complete and testable to continue into downstream risk analysis/test design without inventing material expected behavior?

It does **not** use external retrieval to compensate for an incomplete Jira story.

## Current execution flow

```text
Manual GitHub Actions batch
→ selected Jira issue keys
→ Jira retrieval / normalization
→ deterministic Python pre-check
   ├─ reject → 0 LLM tokens
   └─ eligible
       ↓
minimal semantic payload
       ↓
content fingerprint
       ↓
cache / force-review decision
   ├─ matching cache → reuse structured review → 0 LLM tokens
   └─ fresh execution → Claude Requirements Review
       ↓
READY / NEEDS_CLARIFICATION
       ↓
blocking gaps / clarification questions
       ↓
batch quality + cache + token + cost metrics
```

## Jira retrieval vs LLM payload

Python may retrieve/normalize operational Jira fields required for deterministic control, including status and other metadata.

After pre-check, Claude receives only:

```text
issue_key
summary
description
acceptance_criteria
components
```

This keeps semantic review focused and reduces repeated token cost.

## Review contract

The structured result contains:

- `decision`: `READY` or `NEEDS_CLARIFICATION`;
- `readiness_score`: 0–100;
- concise summary;
- categorized gaps with severity;
- clarification questions;
- explicit known constraints/dependencies where present;
- testability notes;
- recommended next action.

Finding types are:

- `BLOCKING_GAP`;
- `NON_BLOCKING_GAP`;
- `TECHNICAL_CONTEXT_NEEDED`.

Only `BLOCKING_GAP` can produce `NEEDS_CLARIFICATION`.

## Deterministic vs semantic responsibilities

```text
Python
  Jira retrieval / normalization
  issue/status/project/required-field eligibility
  minimal payload construction
  SHA-256 content fingerprint
  cache hit / cache miss
  manual force-review override
  report persistence
  quality/cost aggregation

Claude
  ambiguity assessment
  semantic completeness/testability
  requirement-quality findings
  READY vs NEEDS_CLARIFICATION
  blocking gaps
  clarification questions
```

## Cache contract

The fingerprint covers the cache version, configured model, Requirements Review prompt, and semantic requirement payload.

```text
unchanged Summary / Description / AC / Components + same prompt/model
→ same fingerprint
→ cached review
→ 0 Claude calls

changed semantic content / prompt / model
→ different fingerprint
→ fresh Claude review

force_review=true
→ deliberately bypass matching cache
→ fresh Claude review
```

## Batch observability

The batch summary exposes:

- requested;
- eligible;
- rejected before LLM;
- READY;
- NEEDS_CLARIFICATION;
- cache hits;
- LLM attempts;
- successful fresh reviews;
- execution failures;
- cache hit rate;
- LLM execution rate;
- avoided LLM calls;
- input/output/total tokens;
- actual estimated batch cost.

## Configuration

Use `.env` / GitHub variables and secrets based on `config/.env.example`.

Core controls include:

```text
LLM_API_KEY=...
REQUIREMENTS_REVIEW_MODEL=...
JIRA_BASE_URL=...
JIRA_EMAIL=...
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=...
JIRA_ALLOWED_STATUSES=In Progress
JIRA_REQUIRE_DESCRIPTION=true
JIRA_REQUIRE_ACCEPTANCE_CRITERIA=true
```

GitHub Actions additionally exposes `force_review` as a manual boolean workflow input.

## POC Definition of Done

The Requirements Review slice includes:

- deterministic zero-cost eligibility gating;
- semantic readiness assessment;
- READY / NEEDS_CLARIFICATION governance contract;
- detailed blocking gaps/questions;
- compact semantic payload;
- persistent content-hash cache;
- semantic-content invalidation;
- manual force-review bypass;
- token/cost telemetry;
- batch quality/efficiency metrics;
- validation scenarios/tests;
- orchestration diagrams and operating instructions.

Items below are therefore treated as **next architecture slices**, not missing Requirements Review behavior.

## Planned Agentic QE evolution

```text
Requirements Review Agent
        ↓ READY
Risk Analysis Agent
        ↓
Targeted retrieval/RAG when cross-document evidence is required
        ↓
Test Generation Agent
        ↓
Governance / Human Approval
        ↓
Governed Dataset Update
        ↓
Existing Dataset Validation + Evaluation + CI/CD framework
```

### Risk Analysis Agent — next major agent

Entry condition:

```text
Requirements Review decision = READY
```

Expected risk categories, where applicable:

- functional;
- integration;
- data;
- AI-specific;
- security;
- resilience;
- performance;
- business/process.

Expected structured output will include risk statement, category, likelihood, impact, priority, rationale/evidence and recommended test focus.

Risk Analysis is the first planned stage where cross-document retrieval should be evaluated. Candidate sources include architecture, business rules, policies, related specifications/stories and historical defects.

Design principle:

```text
Retrieve broadly → select relevant evidence → send narrowly to the LLM
```

### Explicitly not implemented by this POC

- Risk Analysis Agent implementation;
- Risk Analysis retrieval/RAG;
- Test Generation Agent;
- Jira write-back;
- automatic status-change execution;
- scheduled agent queue;
- HITL dataset promotion;
- full multi-agent state orchestration.
