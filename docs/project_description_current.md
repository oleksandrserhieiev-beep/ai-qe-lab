# AI QE Lab — Current Project Description

AI QE Lab demonstrates practical Quality Engineering for AI-enabled systems using a Shopping RAG Assistant as the current reference SUT. The current RAG flow includes structured filtering, FAISS Top-K retrieval candidates, adaptive similarity-based Context-K selection, deterministic context construction and Claude generation.

Evaluation combines governed datasets, Dataset/Oracle Validation, deterministic Python oracles, semantic LLM-as-a-Judge evaluation, AI-risk metadata, observability, CI/CD gates, specialized AI testing workflows, telemetry and failure localization.

## Current assets

```text
Standard routine SUT inventory
PR Critical standard = 10 cases (6 deterministic / 4 semantic)
Regression           = 15 cases (7 deterministic / 8 semantic)
Broad Nightly        = 80 cases (48 deterministic / 32 semantic)
Total                = 105 cases (61 deterministic / 44 semantic)

Specialized / separate assets
Metamorphic Critical = 2 records in pr_critical_dataset.json
Adversarial          = 10 cases
Golden               = 35 cases
Judge Calibration    = 8 evaluator cases
```

Back-to-Back has no dedicated dataset; it reuses the 10 standard PR Critical cases.

## Current execution split

```text
PR
├─ Standard Critical Evaluation
└─ Metamorphic Critical

Manual
└─ Back-to-Back Model Comparison

Scheduled / manual
└─ Adversarial Evaluation

Regression / Broad Nightly / Release Validation remain separate lifecycle workflows.
```

Explicit Oracle metadata is primary; missing/null/empty metadata uses the reviewed fallback in `judge_routing.py`; unknown IDs safely default to `semantic_llm`; invalid non-empty Oracle metadata fails Dataset Validation.

The production Judge is version-controlled. Semantic verdicts require a short non-empty rationale; missing `reason` is an evaluator contract violation. Judge prompt/config changes must pass the existing Judge Calibration control.

Drift testing is intentionally deferred from the current roadmap.

Use `README.md`, `docs/current_status.md`, `docs/test_strategy.md` and `docs/documentation_index.md` as the canonical current references.
