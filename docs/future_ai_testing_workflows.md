# Future AI Testing Workflows

## Scope

This roadmap records the next AI-specific test workflows for the lab. Drift testing is intentionally out of scope for the current roadmap.

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

## Already implemented

### Standard Critical Evaluation
Runs on pull requests and evaluates the governed PR Critical dataset using deterministic and semantic Oracle routing.

### Metamorphic Critical
Runs as part of PR validation. It validates critical invariants under controlled input transformations such as paraphrase and irrelevant-noise changes.

### Back-to-Back
Runs manually. The same PR Critical suite is executed against two selected models and the evaluated outputs are compared for quality, regressions, latency and token usage.

## Next implementation

### Adversarial Nightly / Scheduled Flow
Create a dedicated adversarial dataset and workflow based on `docs/adversarial_testing_contract.md`.

Initial scope:

- 10 governed adversarial cases;
- policy override attacks;
- instruction override attempts;
- unsupported-claim forcing;
- prompt/system leakage attempts;
- malicious/conflicting retrieved content;
- hard-constraint bypass attempts;
- deterministic assertions where the protected rule is formalizable;
- semantic Judge evaluation where attack success depends on meaning;
- Attack Success Rate;
- Adversarial Pass Rate;
- critical adversarial failure count;
- category-level result breakdown;
- uploaded raw and evaluated reports.

The broad adversarial suite should be scheduled/nightly rather than added to every PR. Only a small, proven critical adversarial subset should later be promoted into PR Critical when risk justifies the cost.

## Explicitly not planned now

### Drift Testing
Drift testing is not part of the next implementation phase. It can be reconsidered later when the lab has a stronger need for governed time-based baseline comparison across model, prompt, retrieval or knowledge-base changes.
