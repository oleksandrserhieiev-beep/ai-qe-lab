# Production Feedback Loop

## Purpose

Production failures, incidents, user complaints, drift signals, or escaped defects should feed back into the governed AI QE lifecycle rather than ending at the release decision.

This capability is intentionally planned for implementation after the core agent orchestration and evaluation-governance layers are stable.

## Target flow

```text
Production Failure / Escaped Defect / Drift Signal
        ↓
Root Cause Analysis
        ↓
Coverage & Gap Analysis
        ↓
Was the risk known?
Was there a functional test?
Was there an AI evaluation case?
Did an existing test pass incorrectly?
        ↓
┌─────────────────────┬──────────────────────┬────────────────────────┐
│ Risk was missing    │ Test was missing     │ Existing test was weak │
│ → add risk          │ → add test/case      │ → improve Oracle/data  │
└─────────────────────┴──────────────────────┴────────────────────────┘
        ↓
Human Review / Approval
        ↓
Regression Dataset Update
        ↓
Fix Validation
        ↓
Broader Regression Evidence
```

## Golden governance rule

```text
Production defect
≠ automatic Golden Dataset update
```

A confirmed escaped defect normally becomes Regression coverage after analysis and approval. Promotion to Golden is a separate governance decision and should happen only when the behavior is canonical or release-critical reference truth.

## Detecting QE-framework failures

The feedback loop must also detect when the product failed even though the QE framework claimed PASS.

```text
Production failed
+
Requirement / risk / test / dataset case already existed
+
CI evaluation passed
        ↓
Investigate:
- weak test data
- weak assertion
- incorrect Oracle
- Judge false positive / instability
- environment/context mismatch
- non-representative dataset
- missing production condition
```

This is important because the failure may be in the test system rather than only in the SUT.

## Closed lifecycle

```text
Requirement
→ Risk
→ Test
→ Dataset
→ Evaluation
→ Release
→ Production Evidence
→ RCA / Coverage Gap
→ Risk/Test/Dataset Improvement
→ Regression
```

## Related governance controls

Several hardening items that were originally roadmap work are now implemented or formalized elsewhere in the repository:

1. **Judge calibration/version control** — implemented. Judge behavior is version-controlled as Model + Prompt + Rubric and relevant changes are calibrated against human-reviewed truth.
2. **Risk/business-derived quality thresholds** — still a roadmap item. Current thresholds should be treated as provisional until tied to business risk tolerances.
3. **Adversarial testing contract** — formalized in `docs/adversarial_testing_contract.md`.
4. **Golden Dataset change control** — implemented through policy plus deterministic PR enforcement; see `docs/golden_dataset_governance.md`.
5. **Production feedback loop** — specified here; implementation follows after core orchestration is stable.

## Relationship to Desired Next Steps

`docs/desired_next_steps.md` remains the detailed target-state plan for Agentic AI QE orchestration. This document preserves the later production-feedback-loop decision without replacing or shortening that full roadmap.
