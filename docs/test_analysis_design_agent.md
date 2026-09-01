# Test Analysis & Design Agent — Skeleton

## Purpose

The agent consumes a reviewed Jira requirement plus approved Risk Analysis output and proposes only missing test coverage. It is decision support: governed datasets are not mutated before human approval.

## Intended flow

```text
Jira issue IDs
→ eligibility: Requirements Review completed + Risk Analysis available/approved
→ determine candidate governed assets to inspect
→ dataset health check
   → ERROR: block proposal, log exact broken schema/field/reference/record
   → WARNING: continue, surface issue to human
→ coverage analysis: Acceptance Criteria + Risks vs existing cases
→ duplicate/similarity analysis
   → exact duplicate
   → similar case + score
   → already covered
   → coverage gap
→ design only missing coverage
   → functional tests
   → AI-specific/evaluation tests where applicable
→ oracle assignment: deterministic | semantic
→ target proposal + rationale
   → PR Critical
   → Regression
   → Nightly
   → Golden candidate (separate governance path)
→ traceability: Requirement → AC → Risk → Test → Oracle → Target
→ proposal action: ADD | EXTEND_EXISTING | SKIP
→ human Edit / Reject / Approve
→ approved JSON change
→ deterministic post-edit validation
→ governed dataset promotion
```

## Dataset health boundary

Blocking `ERROR` examples: invalid schema, missing required field, broken reference, duplicate record ID, corrupted record. The agent does not repair these silently.

Non-blocking `WARNING` examples: inactive related case, high semantic similarity, coverage overlap, possible consolidation. Warnings remain visible to the human reviewer.

## Similarity and extension

Similarity is evidence, not an automatic duplicate decision. A similar case may produce `EXTEND_EXISTING`. The proposal must identify the existing case and show the proposed extension so the reviewer can compare before/after and approve, edit, reject, or skip it.

## Suite targeting

Risk score alone never assigns a suite. The proposal considers criticality together with execution cost, runtime, test purpose, and suitability for the gate. The human approves the target.

`golden_candidate` is deliberately separate from execution tiers. Golden assets require Golden governance before promotion.

## Traceability contract

Every proposal carries Jira issue, Acceptance Criteria references, risk IDs, oracle type, and target suite. This provides the chain:

`Requirement → Acceptance Criteria → Risk → Test → Oracle → Target`.

## Cache

Test Analysis & Design uses the shared content-aware cache primitive. Its fingerprint includes the issue, Acceptance Criteria, Risk Analysis input, dataset snapshot, model, prompt, and cache version. A changed dataset snapshot invalidates the cache even when the Jira ticket itself did not change.

Caching is an execution optimization only; it does not replace dataset health checks, human approval, or post-edit validation.

## Not implemented in this skeleton

- LLM test-generation execution
- Jira eligibility label contract for this stage
- GitHub PR/JSON mutation after approval
- interactive approval UI
- dataset promotion/write-back
- automatic orchestration across Requirements Review → Risk Analysis → Test Analysis & Design

These are intentionally left for the implementation/promotion phase after the contracts are stable.
