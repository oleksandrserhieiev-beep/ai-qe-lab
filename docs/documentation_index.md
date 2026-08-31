# Documentation

## Canonical current documentation

Use these files as the current source-of-truth set:

- `README.md` — repository-level orientation, current asset counts and workflow split;
- `docs/PROJECT.md` — concise current project description;
- `docs/current_status.md` — authoritative implementation status and immediate Agentic QE next phase;
- `docs/master_architecture.md` — current framework boundaries, core execution, specialized AI testing and governance control planes;
- `docs/architecture.md` — canonical implemented reference-SUT architecture;
- `docs/test_strategy.md` — reusable strategy covering risks, techniques, datasets, Oracles, Metamorphic, Back-to-Back, Adversarial, metrics/gates, evaluator governance and release governance;
- `docs/automated_ai_evaluation.md` — Dataset Validation, Oracle routing, deterministic/semantic evaluation and current Judge v2 rationale contract;
- `docs/dataset_design.md` — purpose-based SUT asset model, separate specialized assets, Judge Calibration and Oracle metadata;
- `docs/future_ai_testing_workflows.md` — current specialized-workflow split: PR Standard + Metamorphic, manual Back-to-Back, scheduled/manual Adversarial; Drift deferred;
- `docs/adversarial_testing_contract.md` — adversarial/prompt-injection design and governance contract;
- `docs/metric_contract.md` — canonical metric definitions, owners, populations and N/A rules;
- `docs/judge_calibration_workflow.md` — implemented OLD-vs-NEW evaluator calibration, including the approved v1 -> v2 prompt-contract comparison;
- `docs/golden_dataset_governance.md` — Golden truth policy and deterministic PR enforcement;
- `docs/agentic_qe_orchestration.md` — implemented Requirements Review orchestration and downstream target flow;
- `docs/requirements_review_agent.md` — Requirements Review contract and boundaries;
- `docs/manual_requirements_review_poc.md` — operating instructions for manual Requirements Review batches;
- `docs/dataset_oracle_validation_pipeline.md` — dataset/oracle execution-precondition pipeline;
- `docs/dataset_lifecycle_evolution.md` — governed test-asset lifecycle evolution;
- `docs/project_overview.md` — target/end-state AI QE operating model, explicitly distinguished from current implementation status;
- `docs/README.md` — documentation landing page.

Working-draft, historical and hardening-note files remain useful records of project evolution, but they do not override the canonical current set above. In particular, older references to earlier suite counts, temporary full-suite PR execution, earlier Judge prompt versions or pre-specialized workflow architecture should be interpreted in their historical context.

## Canonical current asset model

```text
Standard routine SUT inventory
PR Critical standard = 10 cases (6 deterministic / 4 semantic)
Regression           = 15 cases (7 deterministic / 8 semantic)
Broad Nightly        = 80 cases (48 deterministic / 32 semantic)
Total                = 105 cases (61 deterministic / 44 semantic)

Separate / technique-specific / governance assets
Metamorphic Critical = 2 META records in pr_critical_dataset.json
Adversarial          = 10 cases in adversarial_dataset.json
Golden               = 35 canonical cases
Judge Calibration    = 8 evaluator cases
Back-to-Back         = no separate dataset; reuses 10 standard Critical cases
```

The physical `pr_critical_dataset.json` therefore contains 12 records: 10 standard Critical cases plus 2 META records. The standard evaluator and Back-to-Back exclude the META records; the metamorphic runner owns the META execution path.

## Current workflow model

```text
PR Quality
├─ Standard PR Critical Evaluation
└─ Metamorphic Critical Evaluation

Back-to-Back
└─ manual workflow_dispatch, Model A + Model B, same 10 standard Critical cases

Adversarial
└─ workflow_dispatch + nightly schedule, dedicated 10-case dataset

Other lifecycle workflows
├─ Regression         = manual-only
├─ Broad Nightly      = manual-only
└─ Release Validation = manual-only: Golden + broad Nightly evidence + Release Quality Gate
```

Drift testing is intentionally deferred from the current AI-testing workflow roadmap.

## Canonical interpretation rules

- The Shopping RAG Assistant is the reference SUT; the reusable product is the AI QE framework around it.
- `Retrieval-K` is diagnostic candidate evidence; `Context-K` is selected evidence actually eligible for generation.
- `Context-K=0` produces deterministic abstention and skips Claude.
- Valid hard constraints with zero matching catalogue products produce deterministic No-Product-Match and skip Claude.
- Unresolved governed input produces deterministic Clarification before retrieval.
- Explicit dataset Oracle metadata is primary; the fallback registry is resilience only.
- Semantic metrics use only the semantic/Judge population. Empty semantic populations are N/A.
- The production Judge is version-controlled as model + prompt + rubric. Current approved prompt contract is `v2`.
- Every semantic PASS/FAIL verdict must carry a short non-empty rationale. Missing/null/empty `reason` is an evaluator contract violation.
- Judge Calibration compares OLD/base and NEW/head configurations on the same 8-case human-reviewed dataset and protects against unacceptable human-agreement regression or additional false PASS behavior.
- The approved v1 -> v2 prompt-contract comparison preserved 100% human agreement and 0 false PASS / 0 false FAIL.
- Golden is canonical truth. A failing evaluation is not sufficient justification to rewrite Golden expected behavior.
- Release Validation is a separate workflow level using Golden plus broad relevant evidence.
- Metamorphic validates governed invariants across controlled transformations using its dedicated relation runner/gate.
- Back-to-Back is manual comparative testing and reuses the same 10 standard Critical cases rather than creating a duplicate dataset.
- Adversarial testing has a dedicated governed 10-case dataset, attack taxonomy, summary metrics and gate.
- Requirements Review is an upstream Agentic QE control; it does not replace independent SUT evaluation or governance.

## CI governance trigger boundaries

```text
PR Quality:
  Standard PR Critical Evaluation
  Metamorphic Critical Evaluation

Back-to-Back:
  manual workflow_dispatch
  Model A + Model B
  10 standard PR Critical cases

Adversarial:
  workflow_dispatch + nightly schedule
  datasets/adversarial_dataset.json
  adversarial summary + critical gate

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
  explicit issue batch scope
  force_review = explicit cache-bypass control
```

Documentation-only changes do not trigger Judge Calibration or Golden Governance unless the enforcement workflow itself is changed.

## Diagram sources

- `rag.dot` — focused reference-SUT/RAG diagram;
- `overall.dot` — framework-level current quality architecture including specialized AI testing and governance;
- `qa_agent.dot` — target QA/Agentic QE flow;
- `tm_agent.dot` — target Test Management/governance flow;
- Mermaid diagrams in `master_architecture.md`, `architecture.md`, `automated_ai_evaluation.md` and `agentic_qe_orchestration.md` — canonical text-rendered architecture views.
