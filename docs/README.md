# AI QE Lab Documentation

Canonical current documentation:

- [Master Architecture](master_architecture.md) — implemented framework boundaries and current agent/human-gate chain.
- [Agentic QE Orchestration](agentic_qe_orchestration.md) — Requirements Review, Risk Analysis, Test Analysis & Design, Jira Risk approval and Human Decision workflows.
- [Current Status](current_status.md) — authoritative concise implementation status and remaining work only.
- [Test Strategy](test_strategy.md) — quality strategy, agent governance, datasets, Oracles, CI/CD, gates and traceability.
- [Project Description](PROJECT.md) — concise project and orchestration summary.
- [Architecture](architecture.md) — Shopping RAG reference-SUT architecture.
- [Layered Metric Architecture](metric_architecture.md) — metric taxonomy and diagnostic mapping.
- [Automated AI Evaluation](automated_ai_evaluation.md) — Dataset Validation, Oracle routing and evaluation.
- [Dataset Design](dataset_design.md) — governed asset model.
- [Adversarial Testing Contract](adversarial_testing_contract.md) — hostile-input taxonomy and gate.
- [Judge Calibration Workflow](judge_calibration_workflow.md) — evaluator regression governance.
- [Golden Dataset Governance](golden_dataset_governance.md) — canonical-truth change control.
- [Metric Contract](metric_contract.md) — metric definitions/populations/N/A rules.

## Current Agentic QE orientation

```text
Jira
→ Requirements Review
→ human readiness boundary
→ Risk Analysis
→ human approval → Jira Risk write-back
→ Test Analysis & Design
→ Human Decision workflow
→ decision evidence
→ [next: governed dataset promotion]
```

The Human Decision workflow provides the actionable `APPROVE / REJECT / EDIT / EXTEND_EXISTING` choice + explicit confirmation that cannot be embedded as a continuation control inside a GitHub Step Summary.

## Current downstream workflow orientation

```text
PR: Standard Critical + Metamorphic
Manual: Back-to-Back
Manual + nightly: Adversarial
Manual: Regression / Broad Nightly / Release Validation
```

Back-to-Back reuses the 10 standard PR Critical cases. Metamorphic uses 2 META records. Adversarial uses its own 10-case dataset. Drift testing is outside the current roadmap.

Use `current_status.md` plus executable code/workflows on `main` to determine implementation status. Historical/change-note documents must not override the canonical current documents above.
