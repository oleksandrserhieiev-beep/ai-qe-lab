# Judge Calibration Workflow

## Purpose

The LLM Judge is part of the evaluation system and therefore must itself be regression-tested when its behavior can change.

Judge behavior is treated as a configuration composed of:

```text
Judge Configuration
=
Model
+
Judge Prompt
+
Scoring Rubric
```

A material change to any of these may change evaluation outcomes even when the SUT has not changed.

## What is a rubric?

The rubric defines how the Judge interprets quality and maps observed behavior to a score/verdict.

Example:

```text
Correctness rubric

1.0 = fully correct
0.8 = correct main answer with minor non-material issue
0.5 = partially correct with important omission/error
0.2 = mostly incorrect
0.0 = completely incorrect
```

The prompt tells the Judge what task to perform. The rubric tells it how to score that task.

## Calibration dataset

Create a small, stable, human-reviewed calibration dataset containing known examples and expected Judge outcomes.

Example:

| Case | Human-approved expected verdict |
|---|---|
| JCAL-001 | PASS |
| JCAL-002 | FAIL |
| JCAL-003 | PASS |
| JCAL-004 | FAIL |

This dataset tests the evaluator, not the product SUT.

## Baseline concept

The approved Judge configuration on `main` is the baseline.

Example:

```text
MAIN / OLD
Model   = Claude Judge A
Prompt  = v3
Rubric  = v2
Agreement with human calibration set = 96%
```

A PR proposes:

```text
PR / NEW
Model   = Claude Judge B
Prompt  = v4
Rubric  = v2
```

The workflow evaluates the same calibration dataset and reports:

```text
Judge Calibration

Configuration
────────────────────────────
Model:   A  → B
Prompt:  v3 → v4
Rubric:  v2 → v2

Human agreement:
OLD = 96%
NEW = 88%
Delta = -8 percentage points

RESULT = FAIL
```

## How OLD and NEW are known

The workflow must not rely on memory outside Git.

Judge configuration should be version-controlled, for example:

```text
evaluation/judge/
  judge_config.yaml
  judge_prompt.txt
  judge_rubric.yaml
```

Example config:

```yaml
model: claude-example-model
prompt_version: v3
rubric_version: v2
```

For a pull request:

- OLD = files/configuration from the PR base (`main`)
- NEW = files/configuration from the PR head
- Git diff tells the workflow which dimensions changed

The approved historical baseline can also store the previous calibration result as a version-controlled report/metadata artifact if trend comparison is required.

## Trigger strategy

Calibration should run when Judge behavior may change, for example when any of these are modified:

```text
Judge model configuration
Judge system/user prompt
Judge rubric
Judge parsing/scoring logic
```

Conceptual GitHub Actions path trigger:

```text
src/llm_evaluator.py
evaluation/judge/**
datasets/judge_calibration_dataset.*
.github/workflows/judge-calibration.yml
```

It should also support manual `workflow_dispatch` for deliberate re-calibration.

## Workflow logic

```text
PR changes Judge-related configuration
        ↓
Detect OLD configuration from base branch
        ↓
Detect NEW configuration from PR head
        ↓
Load same human-approved calibration dataset
        ↓
Run OLD Judge configuration
        ↓
Run NEW Judge configuration
        ↓
Compare both against human-approved verdicts
        ↓
Calculate agreement / disagreement
        ↓
Calculate OLD → NEW delta
        ↓
Apply Judge Calibration Gate
        ↓
PASS / FAIL + evidence
```

## Why compare both to human truth?

OLD vs NEW alone is insufficient.

A new Judge can differ from the old Judge because the new one is better.

Therefore the primary comparison is:

```text
OLD Judge → Human Baseline
NEW Judge → Human Baseline
```

Then compare their agreement rates and important disagreement cases.

## Initial metrics

At minimum report:

- total calibration cases
- Judge vs human agreement rate
- false PASS count
- false FAIL count
- disagreement case IDs
- OLD agreement
- NEW agreement
- delta
- model/prompt/rubric versions
- token/cost telemetry

For binary PASS/FAIL calibration, simple agreement is sufficient for the first POC implementation. More advanced inter-rater metrics can be introduced later if useful.

## Gate policy

Do not hard-code the final production calibration threshold before collecting a baseline.

Initial POC approach:

1. create human-reviewed calibration cases;
2. measure current Judge agreement;
3. record the current configuration as baseline;
4. define acceptable regression tolerance;
5. block a proposed Judge change if it materially worsens agreement or creates unacceptable false-PASS behavior.

False PASS should normally be considered more dangerous than false FAIL because it can allow a real SUT defect through the quality gate.

## Versioning rule

Every evaluation result should record enough information to reconstruct which Judge produced it:

```text
judge_model
judge_prompt_version or prompt hash
judge_rubric_version or rubric hash
judge_code/config version
```

This allows a failed quality gate to be distinguished from a change in evaluator behavior.

## Target implementation artifacts

```text
datasets/judge_calibration_dataset.json
evaluation/judge/judge_config.yaml
evaluation/judge/judge_prompt.txt
evaluation/judge/judge_rubric.yaml
src/judge_calibration_runner.py
.github/workflows/judge-calibration.yml
reports/judge_calibration_*.json
```

The first implementation should remain intentionally small and should reuse the existing Judge/evaluation client where practical.