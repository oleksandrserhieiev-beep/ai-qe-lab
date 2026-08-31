# Future AI Testing Workflows

## Scope

This roadmap records the specialized AI-testing workflow model for the lab. Drift testing is intentionally out of scope for the current roadmap.

## Current workflow model

```text
PR
├─ Standard Critical Evaluation     ← always
└─ Metamorphic Critical             ← always / cheap subset

Manual
└─ Back-to-Back                     ← compare models/configurations

Nightly / scheduled
└─ Adversarial                      ← broader hostile-input suite
```

## Implemented

### Standard Critical Evaluation
Runs on pull requests and evaluates the governed PR Critical standard cases using deterministic and semantic Oracle routing.

### Metamorphic Critical
Runs as part of PR validation. It validates critical invariants under controlled input transformations such as paraphrase and irrelevant-noise changes. The current PR Critical dataset contains 2 dedicated metamorphic records.

### Back-to-Back
Runs manually through `Back-to-Back Model Comparison`. The same non-metamorphic PR Critical suite is executed against two selected generation models. Both outputs are evaluated through the existing evaluator and compared for quality deltas, case regressions, latency and token usage.

### Adversarial Nightly / Scheduled Flow

Implemented and merged via PR #80.

It adds:

- `datasets/adversarial_dataset.json` with 10 governed adversarial cases;
- policy override attacks;
- instruction override attempts;
- unsupported-claim forcing;
- prompt/system leakage attempts;
- malicious/conflicting retrieved content;
- hard-constraint bypass attempts;
- existing semantic Judge evaluation for governed expected behavior;
- Attack Success Rate;
- Adversarial Pass Rate;
- critical adversarial failure count;
- category-level result breakdown;
- a critical adversarial gate;
- manual `workflow_dispatch` plus nightly schedule;
- uploaded raw, evaluated and adversarial summary reports.

The broad adversarial suite is intentionally separate from every-PR execution because it has a different attack taxonomy, cost profile, metrics and gate. A small, proven adversarial subset can later be promoted into PR Critical if risk justifies the added PR cost.

## Explicitly not planned now

### Drift Testing
Drift testing is not part of the current implementation phase. It can be reconsidered later when the lab has a stronger need for governed time-based baseline comparison across model, prompt, retrieval or knowledge-base changes.
