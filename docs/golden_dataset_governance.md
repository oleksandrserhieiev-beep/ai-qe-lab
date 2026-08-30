# Golden Dataset Governance Policy

## Purpose

The Golden Dataset is the trusted canonical reference set used for release/reference validation. Because it represents expected behavior, changing it can change what the quality gate considers correct.

Therefore Golden Dataset changes require stronger governance than routine evaluation dataset edits.

## Core rule

A failing evaluation is not, by itself, a valid reason to change Golden expected behavior.

```text
Evaluation FAIL
≠
Change Golden until CI passes
```

Golden changes must be supported by approved evidence that the canonical expected behavior itself should change.

## Valid reasons to change Golden

Examples of acceptable reasons:

- approved requirement change;
- approved business-rule change;
- approved policy/specification change;
- canonical expected behavior was proven incorrect;
- an approved critical behavior is intentionally promoted into Golden;
- an obsolete canonical case is removed because the underlying requirement is formally retired.

A production defect may lead to new regression coverage, but does not automatically justify a Golden change.

## Invalid reasons

Golden must not be changed merely because:

- a model or prompt started producing a different answer;
- an evaluation case failed;
- a quality gate is blocking a PR/release;
- a new Judge produces a different verdict;
- changing expected behavior would make CI green;
- there is no approved requirement/business evidence for the new expectation.

## Required change evidence

Every material Golden change should identify:

1. Golden case ID(s).
2. Previous expected behavior.
3. Proposed expected behavior.
4. Reason for change.
5. Linked source of truth, such as requirement, policy decision, approved business rule, defect analysis, or deprecation decision.
6. Impacted risk/requirement traceability where available.
7. Human reviewer/approval evidence through the pull-request process.

Example PR rationale:

```text
Golden Case: GOLD-017

Previous:
Return period = 30 days

Proposed:
Return period = 60 days

Reason:
Approved return-policy change.

Source:
AIQE-456 / approved business requirement
```

## Change lifecycle

```text
Golden Change Proposed
        ↓
Reason + Source Evidence Added
        ↓
Dataset Validation
        ↓
Human Review
        ↓
Approval
        ↓
Merge
        ↓
New Governed Golden Version
```

Golden changes should be performed through a dedicated Git branch / pull request so Git retains:

- who changed it;
- what changed;
- when it changed;
- why it changed;
- reviewer discussion;
- approval;
- diff and commit history.

## Human-in-the-loop rule

Agents or automation may:

- detect that Golden may be stale;
- identify conflicting evidence;
- propose a Golden update;
- generate a candidate diff;
- explain why a change may be needed.

They must not silently rewrite governed Golden expectations after a failed evaluation.

Target rule:

```text
Evaluation FAIL
        ↓
RCA
        ↓
"Golden may be outdated"
        ↓
Proposed Golden Change
        ↓
Human Approval
        ↓
Golden PR
```

Not:

```text
Evaluation FAIL
        ↓
Automatic Golden Rewrite
        ↓
PASS
```

## Regression vs Golden

A confirmed defect normally produces regression coverage first.

```text
Confirmed Defect
        ↓
Fix
        ↓
Regression Case
```

Promotion to Golden is a separate decision:

```text
Regression Case
        ↓
Is this canonical / release-critical reference behavior?
        ↓
YES → propose Golden promotion
NO  → remain Regression coverage
```

This prevents Golden from becoming an unbounded copy of the regression suite.

## Versioning

Git history is the authoritative version history for the initial POC.

Where useful, individual Golden cases may also carry explicit metadata such as:

```json
{
  "id": "GOLD-017",
  "requirement_id": "AIQE-456",
  "change_reason": "Approved return-policy change"
}
```

Do not duplicate metadata in JSON if the same governance evidence is more appropriately maintained in PR/TMS traceability. The key requirement is reconstructability and auditability.

## Validation expectations

Dataset Validation should continue to validate Golden structure/Oracle requirements before Release Validation.

Future hardening may additionally validate that material Golden modifications include required traceability/change-reason metadata or PR evidence.

## Ownership and approval

For the POC, a human project owner/Test Lead may act as the approving authority.

For a production implementation, approval responsibility should be assigned explicitly according to the organization, for example:

- QE/Test Lead for test-governance integrity;
- Product/Business owner for business-truth changes;
- both for material canonical expectation changes.

The strategy should avoid requiring business stakeholders to review low-level JSON. They approve the underlying expected behavior; QE governs the executable representation.

## Relationship to release validation

Release Validation should consume the governed Golden version from the approved branch/ref.

If Golden itself is being changed as part of a release, the release evidence should make that change visible rather than comparing only against the newly edited expectation.

## Summary

Golden is not simply another test file.

It is a governed reference baseline.

The minimum controls are:

```text
Explicit reason
+
Source-of-truth traceability
+
Dataset validation
+
Human review
+
PR history
+
No automatic goalpost moving
```
