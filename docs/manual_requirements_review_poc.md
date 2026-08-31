# Manual Requirements Review Batch — Current POC Approach

## Status

This document describes the current POC decision, not the final production architecture.

The Requirements Review Agent remains read-only. Jira status changes do not automatically trigger LLM execution in this version.

## Why this approach

The POC separates workflow eligibility from paid AI execution.

A Jira status can indicate that a story is ready to be considered for AI review, but it is not itself an execution trigger. This reduces accidental token/cost consumption, keeps execution auditable, and lets the team validate the approach before adding automation.

## Manual execution point

The current entry point is GitHub Actions:

1. Open the repository.
2. Open **Actions**.
3. Select **Requirements Review Agent**.
4. Select **Run workflow**.
5. Enter one or more Jira issue keys in the `issue_keys` field, for example:

```text
AIQE-101, AIQE-105, AIQE-109
```

6. Start the workflow.

The input supports comma, whitespace, or semicolon separators. Duplicate issue keys are removed before processing.

## Processing flow

```text
Manual GitHub Actions run
→ parse Jira issue keys
→ deterministic Python pre-check
→ reject ineligible stories with zero LLM calls
→ run Requirements Review Agent only for eligible stories
→ store one report per executed story
→ aggregate tokens/cost/results into one batch report
→ publish batch summary in GitHub Actions
```

## Deterministic pre-check

The pre-check intentionally happens before Anthropic is called.

A story is rejected before LLM execution when any configured eligibility rule fails. Current rules are:

- invalid Jira issue key format;
- issue belongs to a different configured Jira project;
- issue cannot be found/read from Jira;
- status is not in `JIRA_ALLOWED_STATUSES`;
- description is missing when `JIRA_REQUIRE_DESCRIPTION=true`;
- Acceptance Criteria are missing when `JIRA_REQUIRE_ACCEPTANCE_CRITERIA=true`.

These checks are deterministic and therefore do not consume LLM tokens.

## Acceptance Criteria source

Two POC patterns are supported:

1. Set `JIRA_ACCEPTANCE_CRITERIA_FIELD` when Jira stores Acceptance Criteria in a dedicated custom field.
2. Leave it empty when Acceptance Criteria are stored as an explicit `Acceptance Criteria` section inside Description.

Presence is checked by Python. Quality, ambiguity, completeness, and testability remain the responsibility of the Requirements Review Agent.

## Configuration

The main POC controls are:

```text
JIRA_PROJECT_KEY=AIQE
JIRA_ALLOWED_STATUSES=Ready for Refinement,Ready for AI Review
JIRA_REQUIRE_DESCRIPTION=true
JIRA_REQUIRE_ACCEPTANCE_CRITERIA=true
JIRA_ACCEPTANCE_CRITERIA_FIELD=
REQUIREMENTS_REVIEW_MODEL=claude-sonnet-5
```

In GitHub Actions these values should be configured as repository variables, while API credentials remain repository secrets.

## Batch observability

Every manual execution receives a batch Run ID. The batch summary records:

- requested issue count;
- rejected-before-LLM count;
- executed issue count;
- execution failure count;
- per-story decision and readiness score;
- per-story token usage and estimated cost;
- total input/output tokens;
- total estimated batch cost.

Individual story reports are kept in `reports/requirements_review_<ISSUE>.json`. The batch report is stored as `reports/requirements_review_batch_<RUN_ID>.json` and the entire `reports/` directory is uploaded as a GitHub Actions artifact.

## Current boundary

This POC does not yet include:

- automatic Jira status-change execution;
- scheduled queue processing;
- duplicate/content-hash suppression between separate batches;
- Jira write-back;
- daily/weekly persistent cost aggregation across GitHub workflow runs;
- downstream Risk Analysis or Test Design agents.

Those capabilities should be considered only after the manual batch flow has been validated on real Jira stories and its cost/quality behavior is understood.

## Decision for now

For the current POC, manual GitHub Actions batch execution is the control boundary:

```text
Jira status = eligible for review
Manual GitHub Actions run = explicit permission to spend AI tokens
Python pre-check = zero-cost eligibility gate
Requirements Review Agent = semantic quality review
Batch report = execution and cost evidence
```

This is intentionally a reversible POC choice rather than a final orchestration design.
