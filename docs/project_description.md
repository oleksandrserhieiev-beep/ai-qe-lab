# AI QE Lab — Project Description

AI QE Lab is a practical Quality Engineering reference implementation for AI-enabled systems. Its current System Under Test is a Shopping RAG Assistant. The implemented RAG path is: constraint extraction -> structured product filtering where applicable -> embedding/FAISS semantic ranking -> Top-K retrieval candidates -> adaptive similarity-based context selection -> deterministic Context Builder -> Claude SUT.

The surrounding framework demonstrates governed datasets, Dataset/Oracle Validation, deterministic and semantic test oracles, observability, AI-risk coverage, specialized AI testing techniques, CI/CD quality gates, operational telemetry and failure localization.

## Evaluation asset model

The standard routine SUT inventory is 105 cases:

- 10 standard PR Critical cases: 6 deterministic / 4 semantic;
- 15 Regression cases: 7 deterministic / 8 semantic;
- 80 Broad Nightly cases: 48 deterministic / 32 semantic.

Additional governed assets are intentionally separate from that standard routing inventory:

- 2 Metamorphic Critical records in `pr_critical_dataset.json`;
- 10 Adversarial cases in `adversarial_dataset.json`;
- 35 Golden cases;
- 8 Judge Calibration cases, whose test object is the evaluator.

Back-to-Back reuses the 10 standard PR Critical cases and therefore does not create another dataset.

## Specialized AI testing workflows

```text
PR
├─ Standard Critical Evaluation
└─ Metamorphic Critical

Manual
└─ Back-to-Back Model Comparison

Scheduled / manual
└─ Adversarial Evaluation
```

Metamorphic testing validates governed invariants across controlled transformations. Back-to-Back executes the same controlled Critical cases against Model A and Model B and compares quality/regressions/latency/tokens. Adversarial testing executes the dedicated 10-case hostile-input dataset and reports Adversarial Pass Rate, Attack Success Rate, category breakdown and critical failures.

Drift testing is not part of the current roadmap.

## Dataset and Oracle safety

Before ordinary evaluation, `dataset_validator.py` validates IDs, Oracle values and deterministic assertion presence. Explicit Oracle metadata is primary. Missing/null/empty Oracle is recoverable and uses `judge_routing.py`; an unknown ID safely defaults to `semantic_llm`. Invalid non-empty Oracle metadata is a validation error and stops evaluation before model calls.

Semantic Judge results must include a short non-empty `reason` for both PASS and FAIL. Missing rationale is treated as an evaluator contract violation.

## Current lifecycle

```text
Governed test asset
 -> Dataset / Oracle Validation where applicable
 -> SUT execution / technique-specific execution
 -> Oracle resolution
 -> deterministic Python assertions or semantic LLM Judge
 -> metric / risk / technique-specific aggregation
 -> quality gate
 -> CI evidence / defect localization / lifecycle decision
```

For current implementation status use `docs/current_status.md`; for the full strategy use `docs/test_strategy.md`.
