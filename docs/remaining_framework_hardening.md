# Remaining Evaluation Framework Hardening

## Purpose

This document tracks non-blocking hardening work that remains after the current AI QE evaluation-framework baseline.

These items are intentionally **deferred**. They do not block moving into the Agentic QE phase. When an item is implemented and validated, mark its checkbox complete and link the implementation PR/evidence where useful.

## Deferred checklist

- [ ] **Judge Calibration negative regression test**
  - Create an intentionally degraded Judge change in a controlled PR.
  - Verify OLD remains aligned with the human calibration baseline while NEW degrades or introduces a false PASS.
  - Verify the Judge Calibration gate fails as designed.
  - Keep this as safeguard validation rather than a prerequisite for starting Agentic QE.

- [ ] **Judge Calibration workflow coverage hardening**
  - Review all production Judge behavior paths that should trigger calibration.
  - In particular, evaluate whether changes to `src/llm_evaluator.py` must trigger `.github/workflows/judge-calibration.yml`.
  - Ensure changes capable of altering production evaluator behavior cannot bypass calibration accidentally.

- [ ] **OLD vs NEW Judge runner architecture review**
  - Current calibration intentionally uses the NEW calibration runner to execute OLD configuration/prompt/rubric against the same human truth.
  - Decide whether this stable-harness model is sufficient.
  - If evaluator/runner code itself becomes part of governed Judge behavior, design a true OLD-code vs NEW-code comparison or reuse the production evaluator path directly.

- [ ] **Adversarial coverage audit**
  - Audit existing PR Critical, Regression and Nightly datasets against `docs/adversarial_testing_contract.md`.
  - Identify which governed adversarial categories already have executable coverage.
  - Add only genuinely missing cases; do not duplicate existing coverage.

- [ ] **Risk-based quality-threshold policy**
  - Treat current metric thresholds as POC baseline values rather than universal production targets.
  - Derive thresholds from business impact, risk severity and acceptable failure tolerance.
  - Document rationale and evidence for customer/product-specific thresholds.
  - Revisit whether hard business constraints require stricter or absolute tolerance compared with semantic recommendation quality.

- [ ] **Golden Governance enforcement hardening**
  - Re-run/retain explicit positive and negative governance evidence.
  - Verify valid Golden changes with `Golden Change Reason` and `Source of Truth` pass.
  - Verify invalid/missing governance metadata fails.
  - If non-bypassable enforcement is required, configure the Golden Governance status check as required in repository branch rules/rulesets.

## Current decision

The items above are **future hardening**, not blockers for the next implementation phase.

The project now proceeds to the Agentic QE phase described in `docs/desired_next_steps.md`:

```text
Jira + Confluence
→ Requirements Review / Entry Gate
→ Test Analysis & Risk
→ Test Design
→ Human Approval / Governance
→ Governed Dataset Update
→ Existing AI QE Evaluation Engine
→ CI / Quality Evidence
```

The existing evaluation framework remains the downstream execution and quality-control engine while the upstream agentic/governance layer is implemented incrementally.
