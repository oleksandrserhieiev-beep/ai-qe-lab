# Dataset Design

Datasets are defined by **execution purpose**, not inheritance. The same SUT case may appear in more than one suite when it serves more than one lifecycle purpose. Evaluator-calibration data is intentionally separate because it tests the Judge, not the product.

## Golden Dataset

Purpose: trusted reference behavior and canonical business truth. Use for release confidence and other high-trust baseline checks. Golden is not the parent dataset for the other suites.

Golden has stronger change governance than routine evaluation data. A material Golden change must not be made merely because a product evaluation failed or because changing the expected result would make CI green.

When `datasets/golden_dataset.json` changes, the automated Golden Governance check requires the PR body to contain:

```text
Golden Change Reason: <approved reason for changing canonical expected behavior>
Source of Truth: <requirement, business decision, specification, or defect/reference>
```

The check is path-scoped to the Golden dataset and the enforcement mechanism itself. Documentation-only and unrelated feature changes do not trigger it.

## PR Critical Dataset

Purpose: small risk-based blocking subset for fast pull-request feedback. It is a merge gate, not simply a list of P1/severity-1 cases.

The current PR Critical file contains 12 records: 10 standard Critical cases plus 2 explicit `Type=metamorphic` cases. The metamorphic cases are governed transformations with base/transformed queries and deterministic relation metadata. They are executed by the dedicated Metamorphic Critical runner/gate rather than being treated as ordinary duplicated test cases.

## Regression Dataset

Purpose: stable known behavior plus confirmed/fixed defects and important edge cases. It grows as real defects are fixed. It may overlap Golden or Nightly but is maintained for regression purpose, not as a child of either dataset.

## Evaluation / Broad Nightly Dataset

Purpose: broad AI-risk and robustness surface. Current segments cover normal, ambiguous, negative/no-match, multi-constraint, out-of-domain, missing-information, conflicting-data, adversarial, paraphrase and long-query behavior.

The broad Nightly dataset remains the general robustness suite. A dedicated adversarial suite does not replace it; it gives hostile-input testing its own governed contract, taxonomy, metrics and execution cadence.

## Adversarial Dataset

`datasets/adversarial_dataset.json` is a dedicated 10-case hostile-input suite, merged via PR #80 and based on `docs/adversarial_testing_contract.md`.

Each case explicitly records:

```text
Attack Category
Protected Rule / Asset
Attack Input (Query)
Expected Governed Behavior
Prohibited Behavior
Oracle
Risk / Criticality
Traceability
```

Initial coverage includes:

- business-policy override;
- instruction override;
- unsupported-claim forcing;
- prompt/system leakage;
- malicious/conflicting retrieved content;
- hard-constraint bypass.

All initial cases are critical and use the governed semantic Judge route because attack success/failure currently depends on semantic behavior. Deterministic assertions should be added case-by-case when a protected invariant can be expressed formally without weakening the test.

The dedicated adversarial workflow computes Adversarial Pass Rate, Attack Success Rate, critical failure count and category-level breakdown. It is scheduled/nightly plus manually dispatchable. Drift testing is intentionally not part of this dataset roadmap.

## Back-to-Back dataset use

Back-to-Back testing does **not** introduce another dataset. The workflow intentionally reuses the same controlled non-metamorphic PR Critical cases for Model A and Model B so model comparison is not confounded by different test inputs. Metamorphic cases remain owned by the Metamorphic Critical flow.

## Judge Calibration Dataset

`datasets/judge_calibration_dataset.json` is a **human-reviewed evaluator test asset**, not another Shopping Assistant suite.

Its purpose is to answer:

> Given an example query, expected behavior, supplied evidence and candidate answer whose quality humans already know, does the configured LLM Judge classify the quality dimensions correctly?

The initial calibration set contains 8 deliberately clear good/bad examples covering:

- valid vs over-budget product recommendation;
- correct vs false return-policy statements;
- policy-override / prompt-injection handling;
- supported abstention vs invented warranty claims.

Each case carries human-approved expected values for:

```text
correctness
groundedness
hallucination
constraint_adherence
```

The first approved baseline (`claude-opus-5`, prompt `v1`, rubric `v1`) matched all 32 expected field judgments: 100% agreement, 0 false PASS and 0 false FAIL.

For a normal Judge change:

```text
OLD Judge from PR base ─┐
                        ├─ same calibration dataset -> human agreement comparison
NEW Judge from PR head ─┘
```

The calibration dataset itself is also a governed test asset. It must not be rewritten simply because a proposed Judge performs poorly. Changes to human truth require human review for the same anti-goalpost-moving reason that applies to Golden.

## Evaluation metadata

Risk, Oracle and deterministic assertions are separate concerns:

```text
Risk      = what can fail?
Oracle    = how is PASS/FAIL decided?
Assertion = what exact formal property must deterministic Python prove?
```

PR Critical, Regression and Nightly carry explicit reviewed Oracle metadata in the governed dataset contract. The dataset is authoritative for Oracle routing. Deterministic assertion details may be represented in governed case metadata/derived assertion metadata as required by the current implementation, but no sidecar classification should silently replace the case Oracle.

Current reviewed routine routing inventory remains:

| Suite | Total | Deterministic | Semantic Judge |
|---|---:|---:|---:|
| PR Critical standard cases | 10 | 6 | 4 |
| Regression | 15 | 7 | 8 |
| Broad Nightly | 80 | 48 | 32 |
| **Routine standard total** | **105** | **61** | **44** |

The 2 Metamorphic Critical records are tracked separately because their PASS/FAIL contract is relation-based. The 10-case dedicated Adversarial dataset is also tracked separately because it is a specialized hostile-input suite with its own aggregation/gate. Golden is separate because its lifecycle role is trusted release/reference validation. Judge Calibration is separate because its test object is the evaluator, not the SUT.

## Validation contract

Before active SUT evaluation:

```text
deterministic      -> non-empty deterministic assertions required
semantic_llm       -> valid semantic route
missing/null/empty -> warning; reviewed runtime fallback allowed
invalid non-empty  -> validation ERROR
missing/duplicate ID -> validation ERROR
```

Golden is also validated when executed inside Release Validation. The dedicated Adversarial dataset uses the same dataset validator before model execution.

Judge Calibration has its own execution contract: version-controlled Judge model/prompt/rubric, human-reviewed calibration truth, parseable Judge responses, recorded configuration/telemetry, and OLD-vs-NEW comparison when a base baseline exists.

## Change control

When comparing product evaluation runs, retain the relevant dataset/case identity, prompt/model IDs, retrieval/context configuration and source-data state in reports/telemetry.

For Back-to-Back comparisons, retain both model IDs, the fixed suite identity, evaluated quality deltas, case-level improved/regressed/unchanged classification and operational telemetry.

For adversarial changes, retain the protected rule/asset, attack category, prohibited behavior, traceability, Oracle route, result and category-level attack evidence.

For evaluator changes, retain the Judge model, prompt version, rubric version, calibration case identity, human agreement, false PASS/FAIL counts and OLD->NEW delta.

For canonical Golden changes, retain the PR reason and source-of-truth evidence. Git history plus PR review provides the initial POC audit trail; future Jira/Confluence governance can strengthen traceability without changing these principles.
