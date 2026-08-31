# Manual Requirements Review Batch — Validated POC Approach

## Status

This document describes the implemented Requirements Review POC control boundary. The agent is read-only and the current execution model remains intentionally manual.

A Jira status makes a story **eligible** for review; it does not automatically spend LLM tokens. A GitHub Actions manual run is the explicit execution permission.

## Run the workflow

1. Open the repository in GitHub.
2. Open **Actions**.
3. Select **Requirements Review Agent**.
4. Select **Run workflow**.
5. Enter one or more Jira issue keys in `issue_keys`, for example:

```text
SCRUM-2, SCRUM-3, SCRUM-4
```

6. Leave `force_review=false` for normal cache-aware execution.
7. Set `force_review=true` only when you intentionally want Claude to review eligible stories again even if their semantic content has not changed.
8. Start the workflow.

The input accepts comma, whitespace, or semicolon separators and removes duplicate issue keys.

## Current orchestration

```text
Manual GitHub Actions run
→ parse Jira issue keys
→ retrieve selected Jira fields
→ deterministic Python pre-check
   ├─ reject ineligible story → 0 LLM tokens
   └─ eligible
       ↓
   build minimal semantic payload
       ↓
   content fingerprint
       ↓
   force_review?
       ├─ yes → fresh Claude review
       └─ no → cache lookup
                ├─ same hash → cached review → 0 LLM tokens
                └─ no match → fresh Claude review
       ↓
READY / NEEDS_CLARIFICATION
       ↓
batch quality + efficiency + cost summary
       ↓
JSON reports + GitHub Actions Step Summary
```

For the detailed flowchart and sequence diagram, see `docs/agentic_qe_orchestration.md`.

## Deterministic pre-check

Before Anthropic can be called, Python rejects a story when any configured eligibility rule fails:

- invalid Jira issue key format;
- issue belongs to a different configured Jira project;
- issue cannot be found/read from Jira;
- status is not in `JIRA_ALLOWED_STATUSES`;
- Description is missing when `JIRA_REQUIRE_DESCRIPTION=true`;
- Acceptance Criteria are missing when `JIRA_REQUIRE_ACCEPTANCE_CRITERIA=true`.

These checks consume zero LLM tokens.

## Semantic payload sent to Claude

After pre-check, Claude receives only the fields relevant to the semantic Requirements Review:

```text
issue_key
summary
description
acceptance_criteria
components
```

Operational Jira metadata such as status, priority, labels, assignee, reporter, issue type and parent metadata are not sent to Claude after pre-check.

## Content-hash cache

A SHA-256 fingerprint is calculated over:

- cache schema version;
- configured Requirements Review model;
- Requirements Review prompt text;
- issue key;
- summary;
- description;
- acceptance criteria;
- components.

### Normal cache behavior

```text
same semantic content + same prompt/model
→ same hash
→ cached structured review
→ 0 Claude calls
→ 0 LLM tokens
```

### Cache invalidation

Any change to Summary, Description, Acceptance Criteria or Components creates a different fingerprint and triggers a fresh Claude review. Prompt/model/cache-schema changes also invalidate the prior fingerprint.

### Force review

`force_review=true` is a manual override. It deliberately bypasses a valid matching cache entry and executes a fresh Claude review.

Use it for a controlled re-review, for example when investigating a suspicious cached result or explicitly testing agent repeatability. It is not the normal execution mode.

## Validation scenarios

| Scenario | Expected result | LLM call |
|---|---|---:|
| Unchanged eligible story | cached prior review | No |
| Summary changed | fresh review | Yes |
| Description changed | fresh review | Yes |
| Acceptance Criteria changed | fresh review | Yes |
| Components changed | fresh review | Yes |
| `force_review=true` | fresh review despite matching cache | Yes |
| Missing required AC | rejected by Python | No |
| Ineligible status | rejected by Python | No |
| Semantically complete story | READY | Yes on fresh review |
| Ambiguous/incomplete eligible story | NEEDS_CLARIFICATION + blocking gaps/questions | Yes on fresh review |

## Batch quality and cost summary

The batch report now provides both requirement-quality and execution-efficiency evidence.

### Example

```text
Requested: 10
Eligible after pre-check: 7
Rejected before LLM: 3

READY: 4
NEEDS_CLARIFICATION: 3

Cache hits: 5
LLM attempts: 2
Successful fresh LLM reviews: 2
Cache hit rate: 71.4%
LLM execution rate: 28.6%
Avoided LLM calls: 5

Input tokens: 3100
Output tokens: 1240
Total tokens: 4340
Actual estimated batch cost: $0.021400
```

The metrics mean:

- **Requested** — unique Jira IDs submitted to the batch.
- **Eligible** — stories that passed deterministic Python pre-check.
- **Rejected** — stories stopped before any semantic review.
- **READY / NEEDS_CLARIFICATION** — final semantic outcomes, including cached outcomes.
- **Cache hits** — eligible stories whose exact current review fingerprint already existed.
- **LLM attempts** — eligible stories that did not use cache and therefore entered fresh semantic execution.
- **Cache hit rate** — cache hits / eligible stories.
- **LLM execution rate** — fresh LLM attempts / eligible stories.
- **Avoided LLM calls** — known calls skipped by cache reuse.
- **Actual estimated batch cost** — estimated cost for calls actually executed in this run.

The POC intentionally does not claim a precise "saved USD" metric because a hypothetical fresh review cost varies by story/token volume. Avoided calls are exact; hypothetical avoided cost is not.

## Reports

Each reviewed or cached eligible story produces:

```text
reports/requirements_review_<ISSUE>.json
```

Each batch produces:

```text
reports/requirements_review_batch_<RUN_ID>.json
```

The GitHub Actions artifact uploads `reports/`, and the Step Summary renders batch metrics plus per-story results and clarification gaps.

## Requirements Review POC Definition of Done

The first Agentic QE slice is considered complete when the repository contains and tests the following behavior:

- Jira retrieval / normalization;
- configurable deterministic eligibility pre-check;
- required Description / Acceptance Criteria presence checks;
- minimal semantic Claude payload;
- READY / NEEDS_CLARIFICATION contract;
- blocking gaps and clarification questions;
- token/cost telemetry;
- content-hash reuse for unchanged requirements;
- invalidation when semantic requirement content changes;
- manual `force_review` bypass;
- persistent GitHub Actions cache with serialized writes;
- batch quality / cache / LLM / cost metrics;
- documented orchestration and validation examples.

## Explicitly outside this POC

The following are downstream roadmap items, not unfinished Requirements Review work:

- Risk Analysis Agent;
- cross-document retrieval/RAG for Risk Analysis;
- Test Generation Agent;
- Jira write-back;
- automatic Jira status-change execution;
- scheduled queue processing;
- HITL promotion into governed datasets;
- full multi-agent state orchestration.

## Current control boundary

```text
Jira status = eligibility
Manual GitHub Actions run = permission to execute
Python = deterministic control / cache / telemetry
Claude = semantic Requirements Review
Batch report = quality + execution + cost evidence
```

This remains a reversible POC orchestration choice; it is not presented as the final production trigger architecture.
