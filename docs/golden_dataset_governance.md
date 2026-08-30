# Golden Dataset Governance Policy

## Implementation status

**Policy and deterministic PR enforcement are implemented on `main`.**

Implemented assets:

```text
datasets/golden_dataset.json
src/golden_governance_check.py
.github/workflows/golden-governance.yml
```

The automated check has already been negative-tested: a governed PR without the required change reason/source metadata fails with exit code 1.

## Purpose

The Golden Dataset is the trusted canonical reference set used for release/reference validation. Because it represents expected behavior, changing it can change what the quality gate considers correct.

Therefore Golden Dataset changes require stronger governance than routine evaluation dataset edits.

## Core rule

A failing evaluation is not, by itself, a valid reason to change Golden expected behavior.

```text
Evaluation FAIL
!=
Change Golden until CI passes
```

Golden changes must be supported by approved evidence that the canonical expected behavior itself should change.

## Automated enforcement

The GitHub Action runs automatically on pull requests to `main` only when one of these paths changes:

```text
datasets/golden_dataset.json
src/golden_governance_check.py
.github/workflows/golden-governance.yml
```

Therefore these **do not** trigger Golden Governance by themselves:

```text
docs/**
README.md
ordinary SUT feature code
Regression dataset
Nightly dataset
Judge configuration
```

The checker/workflow paths are intentionally included so changes to the enforcement mechanism self-test the mechanism.

When the check runs, the PR body must contain non-placeholder values for:

```text
Golden Change Reason: <approved reason for changing canonical expected behavior>
Source of Truth: <requirement, business decision, specification, or defect/reference>
```

Missing, empty or placeholder values such as `N/A`, `TBD`, `TODO`, `none` or `-` fail the check.

The workflow creates a GitHub status check. To make that check an **unbypassable merge blocker**, repository branch protection/rulesets must explicitly require the `golden-governance` check.

## Valid reasons to change Golden

Examples:

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
- a product quality gate is blocking a PR/release;
- a new Judge produces a different verdict;
- changing expected behavior would make CI green;
- there is no approved requirement/business evidence for the new expectation.

## Required change evidence

The automated POC control currently enforces two minimum PR fields:

1. `Golden Change Reason`
2. `Source of Truth`

The complete governance evidence for a material change should additionally identify where applicable:

1. Golden case ID(s).
2. Previous expected behavior.
3. Proposed expected behavior.
4. Reason for change.
5. Linked source of truth.
6. Impacted risk/requirement traceability.
7. Human reviewer/approval evidence.

Example:

```text
Golden Case: GOLD-017

Previous:
Return period = 30 days

Proposed:
Return period = 60 days

Golden Change Reason: Approved return-policy change
Source of Truth: AIQE-456 / approved business requirement
```

## Change lifecycle

```text
Golden Change Proposed
        ↓
Reason + Source Evidence Added
        ↓
Golden Governance Check
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

Git PR history retains who changed it, what changed, when, why, reviewer discussion, approval and diff/commit evidence.

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
Source-of-truth evidence
        ↓
Human Approval
        ↓
Golden PR + Governance Check
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

A confirmed product defect normally produces regression coverage first:

```text
Confirmed Defect
        ↓
Fix
        ↓
Regression Case
```

Promotion to Golden is a separate governance decision:

```text
Regression Case
        ↓
Is this canonical / release-critical reference behavior?
        ↓
YES -> propose Golden promotion
NO  -> remain Regression coverage
```

This prevents Golden from becoming an unbounded copy of Regression.

## Versioning

Git history is the authoritative version history for the POC. Individual Golden cases may also carry traceability metadata where useful, but governance evidence should not be needlessly duplicated if the PR/TMS already provides an auditable source.

The requirement is reconstructability: we must be able to explain what canonical expectation changed, why, based on which source and who approved it.

## Validation relationship

Golden Governance and Dataset Validation solve different problems:

```text
Golden Governance
= Is this canonical change justified and traceable?

Dataset Validation
= Is the executable Golden dataset structurally valid and Oracle-valid?
```

Both are needed. A justified business change can still contain malformed JSON/assertions, and a structurally valid JSON change can still be an illegitimate goalpost move.

## Ownership and approval

For the POC, a human project owner/Test Lead may act as approving authority.

For production, approval should be assigned explicitly, for example:

- QE/Test Lead for test-governance integrity;
- Product/Business owner for business-truth changes;
- both for material canonical expectation changes.

Business stakeholders approve the underlying truth; QE governs its executable representation. They do not need to review low-level JSON syntax to approve the business decision.

## Relationship to release validation

Release Validation consumes the governed Golden version from the approved branch/ref.

If Golden itself changes as part of a release, release evidence should make that change visible rather than comparing only against the newly edited expectation and hiding the baseline movement.

## Summary

Golden is not simply another test file. It is a governed reference baseline.

Current controls are:

```text
Explicit Golden Change Reason
+
Source-of-Truth traceability
+
Automatic deterministic PR check
+
Dataset validation
+
Human review
+
Git history
+
No automatic goalpost moving
```
