# No-Context and Evidence Hardening

## Why this change exists

Adaptive Context Selection can legitimately return `Context-K=0` when all retrieval candidates are below `RAG_MIN_SIMILARITY=0.30`. Before this hardening, Claude was still called with empty retrieved context, leaving a residual risk that the model could answer from pretrained knowledge instead of governed Shopping RAG evidence.

The temporary Critical/Regression/Nightly verification also exposed three separate assumptions that fixed Top-K prompting had previously hidden:

1. `R-014` did not actually retrieve its conflicting policy fixture;
2. hard constraints with zero catalogue matches fell back to unrelated semantic Top-K products;
3. the global `cheapest product` case relied on semantic similarity instead of structured price data.

The broad Nightly run additionally showed that vague subjective requests such as `I need a good jacket` need an explicit clarification rule before recommendations are generated.

## Runtime routing

```text
Query
-> Constraint Extraction
-> hard product constraints?
   YES -> Structured Product Filtering
          -> zero matches?
             YES -> deterministic "No matching products" response
                    Claude SUT skipped; 0 SUT tokens/latency
             NO  -> continue
-> cheapest / lowest-price request?
   YES -> deterministic catalogue min-price evidence
   NO  -> semantic FAISS ranking
-> Adaptive Context Selection
-> Context-K > 0?
   YES -> Context Builder -> Claude SUT -> Answer
   NO  -> deterministic no-context abstention
          Claude SUT skipped; 0 SUT tokens/latency
```

This preserves semantic retrieval for semantic relevance while moving formalizable business rules to deterministic Python paths.

## No-context behavior

When selected evidence is empty for a normal semantic retrieval path, the SUT is not called. The response is a narrow deterministic abstention:

`I don't have enough information in the available context to answer that question.`

This is appropriate for unsupported/out-of-domain requests and removes model discretion when no grounding evidence exists.

## Structured no-match behavior

When supported hard product constraints are detected but the structured filter finds zero products, retrieval no longer falls back to arbitrary nearest products. The system returns:

`No matching products were found for all requested constraints.`

This prevents an answer from presenting a closest-but-invalid product and makes negative catalogue behavior deterministic.

## Deterministic cheapest-product routing

`cheapest`, `least expensive`, and `lowest-priced` requests are not semantic-search problems. The retrieval layer now calculates the minimum price from structured catalogue data and supplies that product as deterministic evidence. The Regression case that exposed this defect expected catalogue minimum `P-1077` at `$18.52`, while semantic retrieval had previously surfaced `P-1074` at `$28.43`.

## Vague request behavior

The SUT instruction now explicitly requires a clarifying question for vague subjective product requests such as `good`, `best`, or `nice` when there are insufficient ranking criteria. It must ask for relevant preferences before dumping recommendations.

## Why `RAG_MIN_SIMILARITY` stays at `0.30`

The completed threshold baseline showed that `0.30` removes substantial weak context while preserving the explicitly identified expected product evidence in the baseline. The failures discovered during full-suite verification were routing/behavior defects, not evidence that the threshold should be lowered.

## Case-scoped test fixtures

Production retrieval continues to index only approved policies. Evaluation cases may explicitly declare `Context Fixtures` when they need controlled adverse evidence.

`R-014` now uses:

- approved `delivery_policy.md`: free standard delivery from `$75`;
- evaluation-only `conflicting_delivery_policy_TEST_FIXTURE.md`: `$100`;
- expected behavior: expose the conflict and avoid arbitrarily selecting one source as authoritative.

The fixture is indexed only for that test case and is not promoted into the approved production corpus.

## Observability

Evaluation evidence now preserves:

- retrieval strategy (`structured_no_match`, `catalogue_min_price`, `structured_filter_then_semantic`, or `semantic_faiss`);
- Retrieval-K candidates and similarity scores;
- selected/dropped context evidence;
- `context_k`;
- generation path (`llm`, `deterministic_no_context`, or `deterministic_no_product_match`);
- `llm_call_skipped`;
- SUT/Judge tokens and latency.

## Temporary PR verification

During this hardening PR, the PR workflow temporarily runs three complete suite checks:

1. PR Critical — 10 cases;
2. Regression — 15 cases;
3. Nightly Evaluation — 80 cases.

The first broad verification was intentionally useful rather than silently green: it exposed the vague-request, no-match, and global-minimum-price defects described above. The workflow remains temporary until the corrected implementation is proven across all three suites. After confirmation, Regression and Nightly are removed from the PR workflow and continue only in their dedicated workflows.
