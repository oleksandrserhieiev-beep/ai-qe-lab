# Dataset Design

Datasets are defined by **execution purpose**, not inheritance. The same case may appear in more than one suite when it serves more than one lifecycle purpose.

## Golden Dataset

Purpose: trusted reference behavior and canonical business truth. Use for release confidence and other high-trust baseline checks. Golden is not the parent dataset for the other suites.

## PR Critical Dataset

Purpose: small risk-based blocking subset for fast pull-request feedback. It is a merge gate, not simply a list of P1/severity-1 cases.

## Regression Dataset

Purpose: stable known behavior plus confirmed/fixed defects and important edge cases. It grows as real defects are fixed. It may overlap Golden or Nightly but is maintained for regression purpose, not as a child of either dataset.

## Evaluation / Nightly Dataset

Purpose: broad AI-risk and robustness surface. Current segments cover normal, ambiguous, negative/no-match, multi-constraint, out-of-domain, missing-information, conflicting-data, adversarial, paraphrase and long-query behavior.

## Evaluation metadata

Risk, Oracle and deterministic assertions are separate concerns:

```text
Risk      = what can fail?
Oracle    = how is PASS/FAIL decided?
Assertion = what exact formal property must deterministic Python prove?
```

PR Critical, Regression and Nightly carry explicit reviewed Oracle metadata in the governed dataset contract. The dataset is authoritative for Oracle routing. Deterministic assertion details may be represented in governed case metadata/derived assertion metadata as required by the current implementation, but no sidecar classification should silently replace the case Oracle.

Current reviewed routing inventory:

| Suite | Total | Deterministic | Semantic Judge |
|---|---:|---:|---:|
| PR Critical | 10 | 6 | 4 |
| Regression | 15 | 7 | 8 |
| Nightly | 80 | 48 | 32 |
| **Total** | **105** | **61** | **44** |

Golden is separate from this 105-case routine routing inventory because its lifecycle role is trusted release/reference validation.

## Validation contract

Before active evaluation:

```text
deterministic      -> non-empty deterministic assertions required
semantic_llm       -> valid semantic route
missing/null/empty -> warning; reviewed runtime fallback allowed
invalid non-empty  -> validation ERROR
missing/duplicate ID -> validation ERROR
```

Golden is also validated when executed inside Release Validation.

## Change control

When comparing evaluation runs, retain the relevant dataset/case identity, prompt/model IDs, retrieval/context configuration and source-data state in reports/telemetry. Future Jira/Confluence governance can strengthen version/baseline semantics without changing the principle that the governed dataset is the executable test contract.
