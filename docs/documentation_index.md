# Documentation

Canonical current documentation:

- `architecture.md` — canonical implemented reference-SUT architecture, Dataset Validation, evaluation, CI/CD execution and target Agentic QE flow;
- `current_status.md` — concise authoritative statement of what is implemented on `main` and the immediate next phase;
- `project_overview.md` — target/end-state AI QE operating model, intentionally written in present tense as the completed-product description;
- `test_strategy.md` — reusable test strategy: risks, techniques, datasets, Oracles, metrics, CI levels, entry/exit criteria, failure localization and release governance;
- `automated_ai_evaluation.md` — Dataset Validation, Oracle routing and deterministic/semantic evaluation architecture;
- `metric_contract.md` — canonical metric definitions, owners, pipeline layers, denominators and N/A rules;
- `dataset_design.md` — purpose-based dataset model and current Oracle metadata contract;
- `dataset_lifecycle_evolution.md` — current governed test-asset controls and Jira/Confluence-driven lifecycle evolution;
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
- Release Validation is a separate workflow level using Golden plus broad Nightly validation/evidence.

## Diagram sources

`rag.dot` and `overall.dot` are maintained architecture sources and must stay aligned with the canonical Constraint Validation → Clarification, No-Product-Match and Context-K=0 branches described in `architecture.md` and README.
