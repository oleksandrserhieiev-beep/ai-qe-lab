# AI QE Lab Documentation

Canonical current documentation:

- [Master Architecture](master_architecture.md) — expanded framework boundaries and CI/CD execution model.
- [Architecture](architecture.md) — canonical current reference-SUT architecture.
- [Layered Metric Architecture](metric_architecture.md) — canonical metric taxonomy across SUT/Product Quality, Evaluation Pipeline Health, Judge Quality and Operational metrics, with the RAG-stage diagnostic mapping and legend.
- [Automated AI Evaluation](automated_ai_evaluation.md) — Dataset Validation, Oracle routing, deterministic vs semantic evaluation and metric populations.
- [Dataset Design](dataset_design.md) — purpose-based PR Critical, Regression, Nightly, Golden, Metamorphic, Adversarial and Judge Calibration asset model.
- [Specialized AI Testing Workflows](future_ai_testing_workflows.md) — current PR Metamorphic, manual Back-to-Back and scheduled/manual Adversarial execution split; Drift deferred.
- [Adversarial Testing Contract](adversarial_testing_contract.md) — governed hostile-input taxonomy, Oracle strategy and lifecycle.
- [Dataset Lifecycle Evolution](dataset_lifecycle_evolution.md) — governed JSON controls and Jira/Confluence-driven test-asset lifecycle evolution.
- [Oracle Routing Fallback](oracle_routing_fallback.md) — explicit Oracle resolution, safe runtime fallback and mapper evolution.
- [Project Overview](project_overview.md) — target/end-state AI QE operating model, intentionally written in present tense.
- [Project Description](PROJECT.md) — concise current project description and workflow/asset inventory.
- [Test Strategy](test_strategy.md) — reusable quality strategy including Metamorphic, Back-to-Back, Adversarial, datasets, AI risks, entry/exit criteria, metrics, gates and failure localization.
- [Current Status](current_status.md) — authoritative concise statement of what is implemented now and what is immediately next.
- [Metric Contract](metric_contract.md) — canonical metric definitions, owners, populations and N/A rules.
- [Judge Calibration Workflow](judge_calibration_workflow.md) — evaluator regression control against human-reviewed truth.
- [Golden Dataset Governance](golden_dataset_governance.md) — canonical-truth change control.
- [Documentation Index](documentation_index.md) — complete source-of-truth map and interpretation rules.

## Current specialized workflow orientation

```text
PR
├─ Standard Critical Evaluation
└─ Metamorphic Critical

Manual
└─ Back-to-Back Model Comparison

Scheduled / manual
└─ Adversarial Evaluation
```

Back-to-Back reuses the 10 standard PR Critical cases. Metamorphic uses 2 dedicated META records stored in the PR Critical JSON asset. Adversarial uses its own 10-case dataset. Drift testing is intentionally outside the current roadmap.

Use `current_status.md` plus executable code/workflows on `main` to determine actual implementation status. Use `project_overview.md` for the intended completed operating model. Historical/change-note files document earlier design steps and must not override the canonical current documents listed above.
