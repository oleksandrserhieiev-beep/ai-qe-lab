# Judge Calibration Workflow

## Implementation status

**Implemented on `main`.** The LLM Judge is a version-controlled and regression-tested component of the evaluation system.

Implemented assets:

```text
config/judge_config.json
config/judge_prompt.txt
config/judge_rubric.txt
datasets/judge_calibration_dataset.json
src/judge_calibration_runner.py
.github/workflows/judge-calibration.yml
src/llm_evaluator.py
```

The production evaluator loads the same approved model/prompt/rubric assets that are subject to calibration.

## Purpose

The LLM Judge is part of the quality system and therefore must itself be tested when its behavior can change.

```text
Judge Configuration
=
Model
+
Judge Prompt
+
Scoring Rubric
```

A model, prompt or rubric change can alter product-quality verdicts even when the SUT has not changed. Calibration prevents an evaluator regression from being mistaken for a product regression or silently weakening the quality gate.

## Version history and current approved configuration

The first version-controlled baseline was:

```text
Model  = claude-opus-5
Prompt = v1
Rubric = v1
Cases  = 8
Expected semantic fields = 32
Human agreement = 100%
False PASS = 0
False FAIL = 0
```

PR #83 changed the semantic Judge prompt contract from `v1` to `v2` so every semantic PASS/FAIL verdict must return a short non-empty rationale. The OLD-vs-NEW calibration run completed successfully:

```text
OLD = claude-opus-5 + prompt v1 + rubric v1
NEW = claude-opus-5 + prompt v2 + rubric v1
OLD human agreement = 100%
NEW human agreement = 100%
Delta = 0 percentage points
OLD false PASS / false FAIL = 0 / 0
NEW false PASS / false FAIL = 0 / 0
Result = PASS
```

The current production Judge configuration is therefore:

```text
Model  = claude-opus-5
Prompt = v2
Rubric = v1
```

## Semantic rationale contract

The production semantic evaluator requires a short non-empty `reason` for both PASS and FAIL verdicts.

```text
semantic Judge verdict
-> metrics / booleans
-> non-empty reason
-> semantic evidence
```

If `reason` is missing, null or empty, `src/llm_evaluator.py` treats the response as an evaluator contract violation instead of silently storing a valid semantic result with no rationale.

## Calibration dataset

`datasets/judge_calibration_dataset.json` contains 8 human-reviewed examples whose expected semantic outcomes are known. It tests the evaluator, not the Shopping Assistant.

Current cases cover:

| Area | Good example | Bad example |
|---|---|---|
| Product constraint | waterproof black jacket <= $150 is recommended correctly | recommendation violates the $150 maximum |
| Policy truth | answer states governed 30-day return period | answer invents 90-day return period |
| Instruction override | assistant preserves governed return policy | assistant follows user request to override policy |
| Missing evidence | assistant abstains on unsupported lifetime warranty | assistant invents lifetime warranty |

For each case, humans approve expected values for:

```text
correctness
groundedness
hallucination
constraint_adherence
```

The calibration dataset is itself a governed evaluator-test asset. It must not be rewritten simply because a proposed Judge performs poorly.

## How OLD and NEW are resolved

Git is authoritative:

```text
OLD = Judge assets from PR base / main
NEW = Judge assets from PR head
```

Both configurations are evaluated against the **same human-reviewed calibration dataset**.

```text
OLD Judge ─┐
           ├─> Human Calibration Truth -> agreement / false PASS / false FAIL
NEW Judge ─┘
```

OLD-vs-NEW alone would be insufficient because NEW can legitimately differ from OLD by being better. The primary reference is human-approved truth.

## Automatic trigger strategy

The GitHub Action runs automatically on pull requests to `main` when one of these paths changes:

```text
config/judge_config.json
config/judge_prompt.txt
config/judge_rubric.txt
datasets/judge_calibration_dataset.json
src/judge_calibration_runner.py
.github/workflows/judge-calibration.yml
```

It also supports manual `workflow_dispatch`.

Ordinary documentation and unrelated SUT changes do not trigger Judge Calibration.

## Workflow logic

```text
Judge-related PR
        ↓
Checkout NEW / PR head
        ↓
Run NEW against human calibration truth
        ↓
Checkout OLD / PR base
        ↓
If OLD baseline exists:
    run OLD against same calibration truth
    compare OLD vs NEW
Else:
    validate NEW as bootstrap baseline
        ↓
Judge Calibration Gate
        ↓
PASS / FAIL + JSON evidence artifact
```

## Current gate policy

```text
NEW human agreement >= 90%
OLD -> NEW agreement drop <= 5 percentage points
NEW false PASS count <= OLD false PASS count
```

On bootstrap, NEW must have agreement >= 90% and zero false PASS verdicts.

These are POC controls. Production tolerances should be reviewed against business risk after additional calibration evidence is collected.

False PASS is especially important because an evaluator false PASS can allow a genuine SUT defect through a semantic product quality gate.

## Response/parsing resilience

Calibration distinguishes semantic disagreement from infrastructure/response-format failure.

The runner:

- requires a non-empty Judge text response;
- tolerates JSON code fences;
- can extract a JSON object from a short textual prefix/suffix;
- retries invalid/empty semantic responses up to the configured bounded attempt count;
- logs case ID, model, stop reason, content block types and a bounded raw-text preview;
- records response-attempt counts;
- raises a clear calibration infrastructure failure if no valid JSON is obtained after retries.

## Versioning and production Judge rule

`src/llm_evaluator.py` loads:

```text
config/judge_config.json
config/judge_prompt.txt
config/judge_rubric.txt
```

A runtime `JUDGE_MODEL` / `JUDGE_MODEL_LIGHT` override must match the version-controlled configuration where a configured value exists. A conflicting runtime model is rejected so evaluator behavior cannot change silently outside calibrated Git governance.

Semantic evaluation telemetry records the Judge model plus prompt/rubric versions.

## Evidence produced

Calibration reports include:

- configuration identity;
- case count;
- Judge-vs-human agreement;
- matching/total field judgments;
- false PASS count;
- false FAIL count;
- token usage;
- response attempts;
- per-case field comparisons and reasons.

GitHub Actions uploads `judge_calibration_*.json` evidence artifacts.

## Governing principle

> **Product evaluation tests the SUT. Judge Calibration tests the evaluator that evaluates the SUT.**

Both controls are necessary before semantic quality-gate evidence can be treated as trustworthy.
