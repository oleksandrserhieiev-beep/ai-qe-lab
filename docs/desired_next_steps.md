# Desired Next Steps — Agentic AI QE Orchestration

## Purpose

This document captures the agreed target direction for evolving AI QE Lab from the current RAG/evaluation POC into an Agentic AI Quality Engineering framework.

The existing executable evaluation foundation remains in place:

- governed datasets;
- dataset/oracle validation;
- deterministic assertions;
- semantic LLM Judge;
- Judge calibration;
- Golden Dataset governance;
- PR/Regression/Nightly/Release quality gates;
- telemetry and failure localization.

The next phase adds requirements-driven orchestration and governed agent-assisted test design around that foundation.

---

## Target lifecycle

```text
Jira Story / Requirement
→ Requirements Review / Entry Gate
→ AI Risk Analysis
→ Test Design
→ Governance / Human Review
→ Governed Test Assets
→ Dataset PR / Validation
→ Existing SUT Execution + Evaluation
→ Quality Gate
→ Failure / RCA
→ Defect / Regression / Release Evidence
```

Agents create and govern quality inputs. They do not replace the independent evaluator or human release accountability.

---

## Planned agent responsibilities

### Requirements Review Agent

Checks readiness before downstream work starts:

- Summary / Description / Acceptance Criteria;
- actors and flows;
- constraints;
- dependencies;
- failure/no-result behavior;
- data/source dependencies;
- NFRs where applicable;
- ambiguity and missing information.

Output: PASS/FAIL readiness plus explicit gaps.

### Test Analysis & Risk Agent

Maps applicable conventional and AI-specific risks to the actual architecture and feature. It must not mechanically assign RAG risks to non-RAG components.

Output should preserve requirement → risk → test condition → priority/coverage traceability.

### Test Design Agent

Creates both conventional tests and executable AI evaluation cases.

Functional/API/integration/E2E coverage goes to Test Management. AI evaluation cases are proposed as governed dataset changes.

### Governance / Coverage Agent

Checks proposed coverage for:

- duplicates;
- uncovered risks;
- Oracle choice;
- suite placement;
- criticality;
- requirement/risk traceability;
- consistency with approved business behavior.

Material changes remain subject to human review.

### Orchestrator

Coordinates agents, states, gates, permissions, HITL steps and CI evidence. It should not collapse all responsibilities into one monolithic agent.

---

## Target governed test-asset lifecycle

```text
Test Design Agent
→ Draft Tests
→ Pending Review
→ Human Review / Approval
→ Governed Dataset Update
→ Git branch
→ Dataset PR
→ Dataset Validation
→ Merge
→ Governed Coverage
```

For AI evaluation cases, target traceability should include identifiers such as:

```text
Requirement: STORY-123
Risk: RISK-AI-07
Test Management ID: AIQE-T42
Dataset Case ID: EVAL-0042
Suite: PR Critical / Regression / Nightly / Golden as applicable
```

---

## CI/CD target model

```text
Dataset PR        → Dataset Validation
Feature PR        → Story-specific AI Critical + small global smoke
Merge / main      → Regression
Nightly           → broad AI-risk / edge / adversarial evaluation
Release           → Golden + valid broad release evidence
```

The intent is to avoid unrelated historical failures blocking a feature PR while retaining a small global critical signal.

---

## Judge and Golden governance already implemented

The target agentic lifecycle must reuse the existing controls rather than bypass them.

### Judge Calibration

Judge behavior is version-controlled as:

```text
Model + Prompt + Rubric
```

Relevant Judge changes are regression-tested against the human-reviewed calibration dataset. OLD/base and NEW/head are compared against the same human truth before a new Judge configuration is accepted.

### Golden Dataset Governance

Golden is canonical expected behavior and cannot be silently rewritten because evaluation failed. Material Golden changes require an explicit reason, source of truth and human PR review.

Agents may propose such changes but must not automatically move the goalposts.

---

## Production feedback loop

A future production-quality framework must close the loop from escaped defects and drift back into governed coverage.

```text
Production Failure / Escaped Defect / Drift Signal
→ Root Cause Analysis
→ Coverage & Gap Analysis
→ Was the risk known and tested?
→ Improve missing risk/test or weak Oracle/data
→ Human Review
→ Regression Dataset Update
→ Fix Validation
→ Broader Regression Evidence
```

Core rule:

> A production defect does not automatically change Golden expected behavior.

Normally it creates or strengthens Regression coverage first. Promotion to Golden is a separate governance decision for canonical/release-critical behavior.

This loop allows the framework to learn from real failures without letting the SUT or evaluator rewrite the expected truth to make CI green.

---

## Cost and ROI measurement

The agentic phase should instrument every major component rather than estimate blindly.

Track at minimum:

- model/provider;
- input/output tokens;
- latency;
- retries/errors;
- estimated USD cost;
- accepted/rejected agent output;
- human review effort;
- defects/coverage created;
- execution cost of resulting evaluation suites.

Recommended experiment:

```text
10 realistic Stories → establish end-to-end baseline
then
+20 Stories → 30-Story scale experiment
```

Use the measured data to calculate quality/effort/cost trade-offs and identify which agent steps provide real QE value.

---

## Immediate implementation sequence

1. Integrate Jira/Confluence requirement intake.
2. Implement Requirements Review / Entry Gate.
3. Implement AI Risk Analysis with architecture-aware applicability.
4. Implement Test Design output with requirement/risk traceability.
5. Add Governance / HITL approval states.
6. Generate governed dataset PRs rather than bypassing Git controls.
7. Reuse existing Dataset Validation, SUT execution, Oracle, metrics and CI gates.
8. Add failure/RCA interpretation and defect/regression proposals.
9. Add Coverage & Gap Analysis across requirements, risks, tests and datasets.
10. Instrument cost/latency/token/HITL effort for the 10-Story and 30-Story experiments.
11. Add the production feedback loop after orchestration is stable.

---

## Guiding principle

The target framework is not “agents replacing QA.” It is a governed engineering system in which agents accelerate analysis and test-asset creation while deterministic validation, calibrated evaluation, Git history, CI gates and human accountability preserve quality integrity.
