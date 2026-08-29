# No-Context and Evidence Hardening

## Why this change exists

Adaptive Context Selection can legitimately return `Context-K=0` when all retrieval candidates are below the configured similarity threshold (`RAG_MIN_SIMILARITY=0.30`). Before this hardening, the Claude SUT was still called with an empty retrieved context. That left a residual hallucination risk: the model could answer from its own pretrained knowledge instead of the governed Shopping RAG evidence.

The selector also exposed a weakness in Regression case `R-014`: the test claimed to exercise conflicting policy data, but the conflicting test fixture was not part of the indexed corpus, so the case could pass by abstaining without ever seeing a conflict.

## Runtime rule

```text
Retrieval Top-K
-> Adaptive Context Selection
-> Context-K > 0?
   YES -> Context Builder -> Claude SUT -> Answer
   NO  -> deterministic abstention -> Answer
          Claude SUT call skipped
          input/output tokens = 0
          SUT latency = 0
```

The deterministic no-context answer is intentionally generic and grounded in the absence of evidence. This removes model discretion when there is no selected grounding context.

## Why `RAG_MIN_SIMILARITY` stays at `0.30`

The completed threshold baseline showed that `0.30` already removes substantial weak context without dropping the explicitly identified expected product evidence in the baseline. The new no-context path is therefore treated as a normal branch of the architecture, not as a reason to lower the threshold.

## Case-scoped test fixtures

Production retrieval continues to index only approved policies. Evaluation cases may explicitly declare `Context Fixtures` when they need controlled adverse evidence.

`R-014` now declares:

- approved source: `delivery_policy.md` (`$75` free-standard-delivery threshold);
- evaluation-only fixture: `conflicting_delivery_policy_TEST_FIXTURE.md` (`$100` threshold);
- expected behavior: surface the conflict and avoid arbitrarily choosing one policy as authoritative.

The fixture is added only for that case and is not promoted into the production/approved corpus.

## Observability

Evaluation results preserve:

- Retrieval-K candidates and similarity scores;
- selected/dropped context evidence;
- `context_k`;
- generation path (`llm` or `deterministic_no_context`);
- `llm_call_skipped` for no-context cases;
- SUT/Judge token and latency telemetry.

## Temporary PR verification

During this hardening PR, the PR workflow temporarily runs three complete suite checks:

1. PR Critical (10 cases);
2. Regression (15 cases);
3. Nightly Evaluation (80 cases).

Once all three are confirmed healthy, the temporary Regression and Nightly executions should be removed from the PR workflow. Their normal dedicated workflows remain the long-term execution model.
