# Documentation

Canonical current documentation:

- `architecture.md` — implemented RAG/SUT, adaptive context selection, evaluation and CI architecture;
- `automated_ai_evaluation.md` — Dataset Validation, Oracle routing and deterministic/semantic evaluation;
- `metric_contract.md` — canonical current metric definitions, owners, pipeline layers, denominators, N/A rules and metric evolution;
- `test_strategy.md` — quality strategy, risks, test levels, metrics, gates and failure localization;
- `dataset_design.md` — purpose-based dataset model;
- `dataset_lifecycle_evolution.md` — current validation/governance and planned Jira-driven lifecycle;
- `oracle_routing_fallback.md` — canonical Oracle fallback mechanism;
- `project_overview.md` and `current_status.md` — concise current state.

Metric interpretation rule: semantic metrics (`Correctness`, `Groundedness`, `Hallucination`, `Context Coverage`, `Context Sufficiency`) use judged cases only. A mixed 10-case suite with 4 semantic cases reports semantic outcomes as `x/4 judged`, not `x/10`. An empty semantic population is `N/A`, not `100%`.

DOT sources `rag.dot` and `overall.dot` represent the maintained generated-diagram source architecture.
