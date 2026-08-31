# AI QE Lab — Test Strategy

## 1. Purpose

This strategy defines how the AI QE Lab tests and governs an AI-enabled system. The executable reference SUT is the Shopping RAG Assistant, while the reusable outcome is the QE framework around it: governed datasets, deterministic and semantic Oracles, AI-specific test techniques, evaluator governance, CI/CD quality gates, observability and release evidence.

The framework combines:

- conventional functional, API, integration and E2E testing;
- AI/RAG-specific evaluation;
- deterministic Python assertions and calibrated semantic LLM-as-a-Judge evaluation;
- risk-based Metamorphic, Back-to-Back and Adversarial testing;
- governed test datasets and Dataset / Oracle Validation;
- Judge Calibration and Golden / canonical-truth governance;
- PR, Regression, Nightly, specialized AI-testing and Release workflows;
- target Agentic QE/STLC orchestration with Human-in-the-Loop governance.

Detailed architecture is maintained in `docs/master_architecture.md`; metric definitions and denominators are maintained in `docs/metric_contract.md`.

---

## 2. Test object and quality architecture

The current executable SUT is a Shopping RAG Assistant with deterministic constraint handling, structured filtering, semantic retrieval, adaptive context selection and LLM generation.

The downstream quality flow is:

```text
Governed Test Asset
-> Dataset / Oracle Validation
-> SUT Execution
-> Oracle Resolution
   -> deterministic Python
   OR
   -> calibrated semantic LLM Judge
-> Metrics / Risk Aggregation
-> Quality Gate
-> PASS / FAIL + Evidence
-> Lifecycle Decision
```

Upstream Agentic QE remains a separate quality-engineering flow:

```text
Jira / Confluence
-> Requirements Review
-> Risk Analysis
-> Test Analysis & Design
-> Proposed Test / Evaluation Assets
-> Human Review / Approval
-> Governed Test Assets
```

Agent output is a proposal until human-approved promotion. Dataset validation is a technical execution-precondition check; it does not replace human governance.

---

## 3. Quality objectives

Testing must provide confidence that:

- requirements are sufficiently explicit before downstream test design;
- material conventional and AI-specific risks are represented by executable coverage;
- explicit business rules and hard constraints are respected;
- retrieval returns relevant evidence and context selection preserves required evidence;
- unsupported claims and hallucinations are detected;
- semantic answers remain grounded in supplied evidence;
- ambiguity, no-match and no-context conditions are handled safely;
- behavior remains stable under controlled meaning-preserving transformations;
- hostile or conflicting instructions cannot override governed business truth;
- model/configuration alternatives can be compared on the same controlled evaluation scope;
- evaluator decisions remain aligned with human-reviewed truth;
- canonical Golden expected behavior cannot be silently moved to hide a failure;
- latency, retries, tokens and cost remain observable;
- merge and release decisions are supported by auditable evidence.

---

## 4. Risk-based test design

### Conventional risks

- incorrect functional behavior;
- API / contract failures;
- integration and downstream failures;
- state/data integrity defects;
- error handling and resilience;
- security/privacy failures;
- performance/capacity degradation.

### AI/RAG-specific risks

- retrieval miss or retrieval noise;
- hard-constraint non-adherence;
- relevant evidence dropped by context selection;
- insufficient context;
- semantic incorrectness;
- hallucination / unsupported claims;
- poor groundedness;
- stale or conflicting evidence;
- out-of-domain behavior;
- prompt injection / instruction override;
- malicious retrieved content;
- hidden prompt/system leakage;
- non-deterministic instability;
- model/configuration regression;
- excessive latency/token/cost growth.

### Evaluator risks

- Judge false PASS;
- Judge false FAIL / excessive noise;
- Judge model/prompt/rubric regression;
- malformed or incomplete Judge response;
- missing rationale for a semantic verdict;
- runtime Judge configuration differing from reviewed configuration.

Every material risk should map to an executable test/control, observable evidence and lifecycle decision.

---

## 5. Test techniques

| Technique | Use in the lab | Execution model |
|---|---|---|
| Equivalence Partitioning / BVA | structured fields, limits, price/size/threshold boundaries | standard suites |
| Decision Tables | business-rule and constraint combinations | standard suites |
| Pairwise / combinatorial | multi-constraint coverage | standard suites |
| Negative testing | invalid, missing, contradictory or unsupported inputs | standard suites |
| Error guessing | architecture weak points and defect history | all levels |
| **Metamorphic testing** | verify invariants under paraphrase / irrelevant-noise transformations | PR Critical, cheap deterministic subset |
| Paraphrase testing | same intent expressed differently | standard + Metamorphic |
| **Adversarial testing** | prompt injection, policy override, leakage, malicious context, constraint bypass | dedicated scheduled/manual workflow |
| **Back-to-Back testing** | compare two SUT models/configurations on the same controlled suite | dedicated manual workflow |
| OLD-vs-NEW Judge calibration | compare evaluator versions against human truth | Judge Calibration workflow |
| Repeated-run testing | stochastic stability | targeted/manual |
| Golden baseline validation | canonical release-critical behavior | Release Validation |

### 5.1 Metamorphic testing

Metamorphic testing is used when an exact expected free-text response is unnecessary, but a governed invariant must remain true after a controlled input transformation.

Current PR Critical metamorphic subset:

```text
META-001  paraphrase invariance
META-002  irrelevant-noise invariance
```

The current relation checks are deterministic. The SUT remains probabilistic; the Oracle verifies that the governed invariant survives the transformation.

### 5.2 Back-to-Back testing

Back-to-Back compares two implementations/models under the same input scope:

```text
Same PR Critical standard cases
        ├-> Model A -> Evaluation A
        └-> Model B -> Evaluation B
                         ↓
                    Comparator
                         ↓
              quality + telemetry deltas
```

It reports quality deltas, improved/regressed/unchanged cases, critical regressions, average/P95 latency and token usage. It is a controlled offline comparison, not a production A/B traffic experiment.

Back-to-Back does **not** require a separate dataset. It reuses the standard PR Critical cases and excludes the metamorphic relation cases, which have their own runner/gate.

### 5.3 Adversarial testing

Adversarial testing validates that untrusted user/retrieved instructions cannot override governed policy, business rules, constraints or protected system behavior.

Current categories include:

- business-policy override;
- instruction override;
- unsupported-claim forcing;
- prompt/system leakage attempts;
- malicious/conflicting retrieved content;
- hard-constraint bypass.

The dedicated adversarial summary reports:

- Adversarial Pass Rate;
- Attack Success Rate;
- critical adversarial failures;
- category-level outcomes;
- per-case rationale/evidence.

Detailed design contract: `docs/adversarial_testing_contract.md`.

Drift testing is intentionally outside the current implementation roadmap.

---

## 6. Dataset strategy

Datasets are governed by **execution purpose**, not inheritance.

| Dataset / asset | Test object | Current size | Purpose / use |
|---|---|---:|---|
| **PR Critical — standard cases** | SUT | 10 | fast merge-blocking high-risk evaluation |
| **PR Critical — Metamorphic cases** | SUT relations | 2 | cheap PR-level invariant checks |
| **Regression** | SUT | 15 | stable behavior + confirmed fixed defects |
| **Nightly Evaluation** | SUT | 80 | broad AI-risk / edge-case evaluation |
| **Golden** | SUT / canonical truth | 35 | trusted release/reference baseline |
| **Adversarial** | SUT | 10 | hostile-input / policy-control robustness |
| **Judge Calibration** | Evaluator | 8 | human-reviewed truth for Judge regression testing |
| **Agent Evaluation** | Agents | planned | expected/prohibited tool/action/HITL behavior |

Important interpretation:

```text
pr_critical_dataset.json = 12 physical records
                         = 10 standard evaluation cases
                         + 2 metamorphic relation cases
```

The 10 standard PR cases still have the reviewed Oracle inventory of 6 deterministic + 4 semantic Judge cases. The two `META-*` records are executed by the Metamorphic runner rather than counted in that standard Oracle-routing split.

The Adversarial dataset is a separate 10-case governed asset. Back-to-Back does not add another dataset; it reuses the 10 standard PR Critical cases.

Dataset size is not itself a quality objective. Coverage must be justified by risk, criticality, defect history and execution cost.

---

## 7. Dataset / Oracle Validation

Before active SUT evaluation, selected governed cases must satisfy the technical execution contract.

Current core validation rules:

```text
dataset root        -> JSON array required
case identity       -> ID required and unique per dataset
Oracle              -> deterministic | semantic_llm when explicitly present
deterministic route -> deterministic assertions required
invalid Oracle      -> validation ERROR
missing Oracle      -> reviewed fallback may apply where supported
```

Explicit dataset Oracle metadata is authoritative. Runtime fallback is resilience, not a competing source of truth.

---

## 8. Application / SUT execution model

```text
Evaluation Case
-> Constraint Extraction / Validation
   -> unresolved -> Deterministic Clarification
-> Structured Product Filtering
   -> zero matches -> Deterministic No-Product-Match
-> deterministic catalogue routing where applicable
-> Embedding + Semantic Ranking
-> Retrieval-K
-> Adaptive Context Selection
-> Context-K
   -> 0 -> Deterministic Abstention
   -> >0 -> Context Builder
-> LLM Generation
-> Output + Retrieval/Context/Generation Telemetry
```

A failed final answer is not automatically an LLM defect. Investigation starts at the first failing layer.

---

## 9. Oracle and metric strategy

Governing rule:

> **Formal assertion -> deterministic Python. Meaning/behavior judgment -> calibrated semantic LLM Judge.**

### Deterministic evaluation

Use deterministic assertions for exact properties such as:

- expected retrieved IDs;
- required/forbidden text patterns;
- hard product constraints;
- catalogue facts;
- policy facts expressible by regex/value checks;
- Metamorphic invariant relations.

### Semantic evaluation

Use the calibrated LLM Judge for meaning-level dimensions such as:

- Correctness;
- Groundedness;
- Hallucination;
- Context Coverage;
- Context Sufficiency;
- semantic constraint/policy adherence when deterministic proof is insufficient;
- adversarial success/failure when meaning rather than exact text determines the verdict.

The Judge does **not** choose the Oracle.

Every semantic verdict must contain a **short, non-empty rationale**. `reason=null` or an empty reason is an evaluator contract violation, not a valid PASS/FAIL result.

### Metric populations

Semantic metrics use only semantic/Judge cases in their denominator. Deterministic-only cases are excluded from non-applicable semantic metrics.

Suite-wide/hybrid metrics include Overall Pass Rate, Retrieval Hit and Constraint Adherence according to `docs/metric_contract.md`.

Current provisional product-quality thresholds remain POC baselines rather than universal customer thresholds:

```text
Correctness >= 95%
Groundedness >= 95%
Retrieval Hit >= 95%
Constraint Adherence >= 95%
Hallucination <= 2%
```

Quality-gate evaluation remains deterministic even when source evidence includes semantic Judge outputs.

---

## 10. Evaluator / Judge governance

Judge behavior is version-controlled:

```text
Judge Configuration = Model + Prompt + Rubric
```

Any material Judge model/prompt/rubric change must be calibrated against the same human-reviewed Judge Calibration Dataset.

```text
OLD approved Judge ─┐
                    ├-> same human truth -> compare agreement / false PASS / false FAIL
NEW proposed Judge ─┘
```

Current calibration gate:

```text
NEW agreement >= 90%
agreement drop vs OLD <= 5 percentage points
NEW false PASS count <= OLD false PASS count
```

Malformed responses, provider errors and missing required rationale are evaluator/infrastructure failures, not product-quality verdicts.

---

## 11. Golden / canonical-truth governance

Golden represents trusted expected behavior and receives stronger change control.

```text
Evaluation FAIL
!=
Change Golden until CI passes
```

A Golden change requires an approved reason and source of truth. Golden Governance is separate from product execution and Judge Calibration.

---

## 12. CI/CD and specialized workflow model

The current workflow architecture intentionally separates lifecycle gates from specialized AI test techniques.

```text
PR
├─ Standard Critical Evaluation     -> always for meaningful PR changes
└─ Metamorphic Critical             -> always / cheap subset

Manual comparison
└─ Back-to-Back                     -> compare models/configurations

Nightly / scheduled
└─ Adversarial                      -> broader hostile-input suite

Other lifecycle workflows
├─ Regression                       -> manual currently
├─ Broad Nightly Evaluation         -> manual currently
└─ Release Validation               -> manual / release-candidate process
```

| Level / workflow | Trigger | Scope | Gate / outcome |
|---|---|---|---|
| **PR Critical Standard** | pull request | 10 standard PR Critical cases | merge-blocking product Quality Gate |
| **Metamorphic Critical** | pull request | 2 `META-*` cases | Metamorphic Gate / invariant preservation |
| **Back-to-Back** | manual | same 10 standard PR Critical cases against Model A and Model B | comparative report; critical regression signal |
| **Adversarial** | scheduled + manual | 10 adversarial cases | Adversarial Gate / Attack Success Rate / critical failures |
| **Regression** | manual currently | 15 regression cases | regression health |
| **Broad Nightly** | manual currently | 80-case evaluation dataset | broad AI-risk signal |
| **Release Validation** | manual / RC | Golden + broad evidence | release Quality Gate / GO-NO-GO evidence |
| **Judge Calibration** | Judge behavior changes + manual | 8 human-reviewed calibration cases | evaluator regression gate |
| **Golden Governance** | Golden changes | canonical expected behavior | change-control gate |

The specialized workflows are deliberately separate because they have different datasets, Oracles, economics and decision purposes.

---

## 13. Release Validation

Release Validation is a lifecycle decision layer, not another name for Golden.

```text
Release Candidate
        ↓
Release Validation
        ├─ Golden trusted baseline
        └─ broad current risk evidence
        ↓
Release Quality Gate
        ↓
GO / NO-GO / explicit risk acceptance
```

Release readiness additionally considers unresolved defects, operational evidence, coverage, evaluator validity and residual risk.

---

## 14. Entry / exit criteria

Entry/exit criteria apply to lifecycle execution/readiness and are distinct from ticket-level Definition of Ready / Definition of Done.

### Framework/run entry

- selected governed test scope exists;
- required test-asset approval is complete;
- dataset/Oracle contract is valid;
- source data and environment are available;
- required model configuration/secrets are available;
- telemetry can be captured;
- no infrastructure issue invalidates the run.

### Product/run exit

- planned scope executed;
- blocking failures resolved or explicitly classified;
- applicable Quality Gate passed;
- reports/evidence retained;
- residual risk acceptable for the lifecycle decision.

### Specialized workflow exit

- Metamorphic: all blocking invariant relations pass;
- Back-to-Back: deltas/regressions are available and critical regressions are explicitly reviewed;
- Adversarial: Attack Success Rate / critical failures satisfy the adversarial gate;
- Judge Calibration: evaluator gate passes;
- Golden Governance: approved reason/source-of-truth controls pass.

---

## 15. Failure localization and defect policy

Investigation identifies the first failing layer:

```text
Requirement / Agent preparation
-> Human Governance
-> Dataset / Oracle Validation
-> Constraint handling
-> Filtering / Retrieval
-> Context Selection
-> Context Construction
-> Generation / SUT Model
-> Metamorphic Relation / Adversarial Contract / Back-to-Back Comparison
-> Oracle Resolution / Deterministic Engine
-> Judge / Evaluator
-> Metrics / Gate / Reporting
-> Governance Control
```

A rerun is evidence about reproducibility, not permission to retry until green. Preserve original failure evidence.

Confirmed product defects should produce permanent Regression coverage after the fix is verified.

---

## 16. Non-functional and operational testing

Measure where applicable:

- average and P95 latency;
- provider errors/retries/timeouts;
- rate limits;
- throughput/concurrency;
- token/context-size growth;
- estimated/actual model cost where available;
- repeated-run stochastic stability;
- model/provider dependency health;
- Judge calibration overhead.

Back-to-Back additionally compares Model A vs Model B latency and token telemetry on the same controlled cases.

---

## 17. Traceability

Target product traceability:

```text
Requirement
-> Risk
-> Test / Evaluation Asset
-> Human Approval
-> Governed Dataset
-> Dataset / Oracle Validation
-> SUT Execution
-> Retrieval / Context / Output Evidence
-> Oracle / Specialized Test Relation
-> Metric / Gate
-> Defect / Regression
-> Residual Risk
-> Release Decision
```

Specialized AI-testing evidence should retain:

- case ID and dataset identity;
- risk / attack / transformation category;
- model and prompt identity;
- Oracle / relation type;
- semantic Judge rationale where applicable;
- retrieval/context/generation evidence;
- comparison delta for Back-to-Back;
- Attack Success Rate / adversarial category outcome for Adversarial;
- Quality Gate result.

---

## 18. Roles and reporting

**Test Lead / Quality Owner** owns strategy, risk model, gate policy, residual-risk assessment and release recommendation.

**QA/QE** designs and reviews coverage, datasets, deterministic assertions, metamorphic relations and adversarial contracts; executes tests; analyzes evidence; localizes failures.

**Development / AI Engineering** owns the SUT implementation and fixes product/retrieval/prompt/model defects.

**Product / Business** validates business truth and approves material canonical expectation changes.

**Human Governance / Reviewers** approve/reject promotion of proposed governed test assets.

Reports should expose where applicable:

- executed/passed/failed counts;
- actual metric populations/denominators;
- critical failures and risk outcomes;
- Metamorphic relation outcomes;
- Back-to-Back quality/latency/token deltas;
- Adversarial Pass Rate / Attack Success Rate / category results;
- per-case semantic rationale;
- dataset/Oracle validation errors;
- retrieval/context/generation evidence;
- Judge configuration/calibration evidence;
- latency/tokens/cost;
- defect classification and residual-risk recommendation.

---

## 19. Strategy evolution

This is a living strategy and must be updated when architecture, agents, models, prompts, datasets, specialized test techniques, metrics/gates, governance controls or release processes materially change.

Current specialized AI-testing position:

```text
Implemented:
✓ Standard Critical Evaluation
✓ Metamorphic Testing
✓ Back-to-Back Testing
✓ Adversarial Testing

Not in current roadmap:
- Drift Testing
```

> **Quality confidence must come from traceable evidence across the whole AI system, not from a single model score or a single successful answer.**
