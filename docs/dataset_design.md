# Dataset Design

Datasets are defined by **execution purpose**, not by inheritance. The same case may appear in more than one suite when it serves more than one lifecycle purpose.

## Golden Dataset

Purpose: trusted reference behavior and canonical business truth. Use for baseline comparisons, architecture/model/prompt/retrieval changes and release confidence. It is not the parent dataset for the other suites.

## PR Critical Dataset

Purpose: small risk-based blocking subset for fast pull-request feedback. It is a merge gate, not simply a list of P1/severity-1 cases.

## Regression Dataset

Purpose: stable known behavior plus confirmed/fixed defects and important edge cases. It grows as real defects are fixed. It may overlap Golden or Evaluation but is maintained for regression purpose, not as a child of either dataset.

## Evaluation / Nightly Dataset

Purpose: broad AI-risk and robustness surface. Current segments cover normal, ambiguous, negative/no-match, multi-constraint, out-of-domain, missing-information, conflicting-data, adversarial, paraphrase and long-query behavior.

## Evaluation metadata

Risk, Oracle and deterministic assertion metadata are separate concerns:

```text
Risk      = what can fail?
Oracle    = how is PASS/FAIL decided?
Assertion = what exact formal property must deterministic Python prove?
```

Critical and Regression carry explicit Oracle metadata. Nightly uses reviewed sidecar metadata for Oracle/risk/assertions where required by the current dataset schema. All three active suites are validated before execution.

## Change control

When comparing evaluation runs, retain the relevant dataset/case identity, prompt version, model IDs, retrieval/context configuration and source-data state in the available reports/telemetry. A future explicit dataset-version field may be added if release governance requires stronger version semantics; it is not currently presented as implemented.
