# Documentation

Canonical current documentation:

- `architecture.md` — canonical implemented reference-SUT architecture, Dataset Validation, product evaluation, evaluator calibration, Golden governance, CI/CD execution and target Agentic QE flow;
- `current_status.md` — concise authoritative statement of what is implemented on `main` and the immediate next phase;
- `project_overview.md` — target/end-state AI QE operating model, intentionally written in present tense as the completed-product description;
- `test_strategy.md` — reusable test strategy: risks, techniques, datasets, Oracles, metrics, Judge calibration, Golden change controls, CI levels, entry/exit criteria, failure localization and release governance;
- `automated_ai_evaluation.md` — Dataset Validation, Oracle routing, deterministic/semantic evaluation and evaluator-governance architecture;
- `metric_contract.md` — canonical metric definitions, owners, pipeline layers, denominators and N/A rules;
- `dataset_design.md` — purpose-based SUT dataset model, separate Judge Calibration Dataset, Oracle metadata and change-control model;
- `dataset_lifecycle_evolution.md` — current governed test-asset controls and Jira/Confluence-driven lifecycle evolution;
- `judge_calibration_workflow.md` — implemented OLD-vs-NEW Judge calibration using a human-reviewed baseline, path triggers, gates and evidence;
- `golden_dataset_governance.md` — Golden truth policy plus implemented deterministic PR enforcement;
- `adversarial_testing_contract.md` — adversarial/prompt-injection test design and governance contract;
- `oracle_routing_fallback.md` — canonical Oracle fallback mechanism;
- `no_context_hardening.md` — historical hardening record for zero-context, conflict-fixture and generation-path behavior.

`project_overview.md` is descriptive rather than a claim that every target-state capability is already implemented. Use `current_status.md`, current workflows and `main` code to determine actual implementation status.

## Canonical interpretation rules

- The Shopping RAG Assistant is the reference SUT; the reusable product is the AI QE framework around it.
- `Retrieval-K` is diagnostic candidate evidence; `Context-K` is selected evidence actually eligible for generation.
- `Context-K=0` produces deterministic abstention and skips Claude.
- Valid hard constraints with zero matching catalogue products produce deterministic No-Product-Match and skip Claude.
- Unresolved governed input produces deterministic Clarification before retrieval.
- Explicit dataset Oracle metadata is primary; the fallback registry is resilience only.
- Semantic metrics use only the semantic/Judge population. Empty semantic populations are N/A.
- The production Judge uses version-controlled model/prompt/rubric assets; changes to evaluator behavior are calibrated against human-reviewed truth.
- Judge Calibration compares OLD/base and NEW/head configurations on the same calibration dataset and protects against unacceptable human-agreement regression or new false PASS behavior.
- The Judge Calibration Dataset tests the evaluator, not the Shopping Assistant, and is not counted in the 105 routine SUT cases.
- Golden is canonical truth. A failing evaluation is not sufficient justification to rewrite Golden expected behavior.
- Golden changes require explicit reason and source-of-truth metadata through the automated governance check.
- Release Validation is a separate workflow level using Golden plus broad Nightly validation/evidence.

## CI governance trigger boundaries

```text
Judge Calibration:
  config/judge_config.json
  config/judge_prompt.txt
  config/judge_rubric.txt
  datasets/judge_calibration_dataset.json
  src/judge_calibration_runner.py
  .github/workflows/judge-calibration.yml

Golden Governance:
  datasets/golden_dataset.json
  src/golden_governance_check.py
  .github/workflows/golden-governance.yml
```

Documentation-only changes do not trigger these controls. The workflow files themselves are intentionally included so a change to enforcement/calibration logic self-tests its own control.

## Diagram sources

`rag.dot` remains the focused reference-SUT/RAG diagram. `overall.dot` is the framework-level diagram and must stay aligned with the canonical product-quality loop plus the Judge Calibration and Golden Governance control loops described in `architecture.md` and README.
