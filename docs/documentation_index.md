# Documentation

Canonical current documentation:

- `architecture.md` — implemented RAG/SUT, adaptive context selection, evaluation and CI architecture;
- `no_context_hardening.md` — zero-context abstention, case-scoped conflict fixtures, generation-path telemetry and temporary three-suite verification;
- `automated_ai_evaluation.md` — Dataset Validation, Oracle routing and deterministic/semantic evaluation;
- `metric_contract.md` — canonical current metric definitions, owners, pipeline layers, denominators, N/A rules and metric evolution;
- `test_strategy.md` — quality strategy, risks, test levels, metrics, gates and failure localization;
- `dataset_design.md` — purpose-based dataset model;
- `dataset_lifecycle_evolution.md` — current validation/governance and Jira-driven lifecycle evolution;
- `oracle_routing_fallback.md` — canonical Oracle fallback mechanism;
- `current_status.md` — concise implemented state;
- `project_overview.md` — target end-state AI QE operating model, intentionally written in present tense as the completed product description.

`project_overview.md` is descriptive rather than a claim that every target-state capability is already implemented. Use `current_status.md`, the current architecture docs and `main` code when determining actual implementation status.

Metric interpretation rule: semantic metrics (`Correctness`, `Groundedness`, `Hallucination`, `Context Coverage`, `Context Sufficiency`) use judged cases only. A mixed 10-case suite with 4 semantic cases reports semantic outcomes as `x/4 judged`, not `x/10`. An empty semantic population is `N/A`, not `100%`.

Adaptive Context Selection rule: `Retrieval-K` is diagnostic candidate evidence; `Context-K` is the selected evidence sent to generation. If `Context-K=0`, the SUT LLM call is skipped and a deterministic no-context abstention is returned.

DOT sources `rag.dot` and `overall.dot` represent the maintained generated-diagram source architecture and include the no-context generation branch.
