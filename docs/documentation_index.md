# Documentation

Canonical current documentation:

- `architecture.md` — canonical implemented reference-SUT architecture, Dataset Validation, product evaluation, evaluator calibration, Golden governance, CI/CD execution and target Agentic QE flow;
- `agentic_qe_orchestration.md` — current implemented Requirements Review orchestration, cache/force-review sequence, batch metrics, POC boundary and downstream Risk Analysis/Test Generation flow;
- `requirements_review_agent.md` — Requirements Review purpose, Python-vs-LLM responsibility boundary, cache contract, Definition of Done and next-agent boundary;
- `manual_requirements_review_poc.md` — operating instructions for manual GitHub Actions batches, validation scenarios, `force_review`, cache invalidation and batch metric interpretation;
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
- Requirements Review status is an eligibility concern; the current POC spends LLM tokens only through an explicit manual GitHub Actions batch.
- Requirements Review uses deterministic Python pre-check/cache control and Claude only for semantic readiness review.
- Unchanged semantic requirement content reuses a cached structured review; changed Summary/Description/Acceptance Criteria/Components invalidates the fingerprint.
- `force_review=true` is a manual cache bypass, not a normal automatic trigger.
- Requirements Review does not retrieve external knowledge to hide a deficient Jira story; Risk Analysis is the planned first cross-document retrieval stage.

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

Requirements Review:
  manual workflow_dispatch
  issue_keys = explicit batch scope
  force_review = explicit cache-bypass control
```

Documentation-only changes do not trigger Judge Calibration or Golden Governance. The workflow files themselves are intentionally included in their respective path controls so a change to enforcement/calibration logic self-tests its own control.

## Diagram sources

`rag.dot` remains the focused reference-SUT/RAG diagram. `overall.dot` is the framework-level product/evaluator/governance diagram. `agentic_qe_orchestration.md` is the canonical diagram source for the implemented Requirements Review control flow and the planned Requirements Review → Risk Analysis → Test Generation orchestration sequence.
