# AI QE Lab

Practical AI Quality Engineering lab for building, testing, evaluating, and governing AI-enabled systems.

The project currently focuses on three workstreams:

1. **Shopping RAG Assistant** — implemented
2. **QA Agent** — planned
3. **Test Management Lifecycle Agent** — planned

The current implementation demonstrates a working RAG application together with an automated AI evaluation and CI/CD quality-control pipeline.

---

## Current Architecture

```text
User / Evaluation Dataset
        ↓
Shopping AI Assistant
        ↓
Constraint Filtering
        ↓
Query Embedding
        ↓
FAISS Vector Search
        ↓
Top-K Retrieval
        ↓
Context Augmentation
        ↓
Claude LLM
        ↓
Generated Answer
        ↓
AI Evaluator
        ↓
Quality Metrics
        ↓
Quality Gate
        ↓
GitHub Actions
        ↓
PR PASS / FAIL
```

---

## Shopping RAG Assistant

The Shopping AI Assistant uses product and policy data as its controlled knowledge base.

Current capabilities include:

* Product catalogue retrieval
* Policy retrieval
* Semantic vector search
* Structured product constraint filtering
* Configurable Top-K retrieval
* Context augmentation
* Claude-based answer generation
* Out-of-domain abstention
* Retrieval tracing
* Context logging
* LLM telemetry

The current local vector implementation uses:

* `sentence-transformers`
* `all-MiniLM-L6-v2`
* FAISS

---

## AI Evaluation Framework

The repository contains an automated evaluation framework for validating RAG and LLM quality.

The evaluation pipeline is:

```text
Dataset
   ↓
Evaluation Runner
   ↓
RAG + LLM
   ↓
Case-Level Results
   ↓
LLM Evaluator
   ↓
Metrics
   ↓
Quality Gate
```

Every evaluation retains case-level evidence rather than only aggregate percentages.

### Current AI Quality Metrics

The framework currently measures:

* Overall Pass Rate
* Retrieval Hit Rate
* Correctness
* Groundedness
* Constraint Adherence
* Hallucination Rate
* Average Latency
* P95 Latency
* Input Token Usage
* Output Token Usage

---

## Golden Dataset

The Golden Dataset contains canonical and business-critical expected behaviours.

It is used to establish a stable quality baseline for the AI system.

A full Golden run currently contains **35 cases** covering areas including:

* Product retrieval
* Multi-constraint product search
* Returns policy
* Delivery policy
* Warranty policy
* Payment safety
* Out-of-domain behaviour
* Policy paraphrases

The established Golden baseline has achieved:

```text
Total cases: 35
Passed: 35
Failed: 0

Overall Pass Rate: 100%
Retrieval Hit Rate: 100%
Correctness Rate: 100%
Groundedness Rate: 100%
Constraint Adherence Rate: 100%
Hallucination Rate: 0%
```

Baseline performance is tracked separately because latency and token consumption can vary between executions and configurations.

---

## PR Critical Dataset

Pull Requests do not execute the complete Golden Dataset.

A smaller risk-based PR Critical Dataset currently contains **10 critical/high-risk cases**.

This provides faster and cheaper feedback while retaining coverage of important AI behaviours.

Current PR evaluation flow:

```text
Pull Request
      ↓
Path Filter
      ↓
10 Critical AI Cases
      ↓
RAG + LLM
      ↓
LLM Evaluation
      ↓
Quality Gate
      ↓
PASS / FAIL
```

The current PR Critical baseline is:

```text
Total cases: 10
Passed: 10
Failed: 0

Overall Pass Rate: 100%
Retrieval Hit Rate: 100%
Correctness Rate: 100%
Groundedness Rate: 100%
Constraint Adherence Rate: 100%
Hallucination Rate: 0%
```

---

## Quality Gates

AI evaluation is integrated into GitHub Actions.

The Quality Gate evaluates generated metrics against defined thresholds.

Current gate dimensions include:

* Critical-case failures
* Correctness
* Groundedness
* Retrieval Hit Rate
* Constraint Adherence
* Hallucination Rate

A Quality Gate failure returns a non-zero process exit code and causes the GitHub Actions check to fail.

The intended governance model is:

```text
AI quality acceptable
        ↓
Quality Gate PASS
        ↓
PR GREEN

AI quality regression
        ↓
Quality Gate FAIL
        ↓
PR RED
```

---

## CI/CD

GitHub Actions is used as the CI execution environment.

The current Pull Request workflow performs:

```text
Checkout Repository
        ↓
Set Up Python
        ↓
Restore pip Cache
        ↓
Install Dependencies
        ↓
Run PR Critical Dataset
        ↓
Evaluate PR Critical Dataset
        ↓
Quality Gate
        ↓
Upload Evaluation Reports
```

### Path Filtering

AI evaluation is triggered only when relevant project areas change.

Current monitored paths include:

```text
src/**
data/**
datasets/**
tests/**
.github/workflows/ai-evaluation.yml
requirements.txt
```

Documentation-only changes such as `README.md` therefore do not consume unnecessary LLM evaluation resources.

---

## RAG Experiments

The project is also used for controlled RAG experiments.

A Top-K experiment compared `K=5` and `K=10`.

Observed result:

```text
K=5 Retrieval Hit Rate:   97.14%
K=10 Retrieval Hit Rate: 100.00%
```

However, increasing K substantially increased input-token consumption.

This demonstrated an important RAG engineering trade-off:

```text
Higher retrieval coverage
        ↕
Larger context / higher cost
```

Structured constraint filtering was subsequently introduced rather than relying only on increasing Top-K.

---

## Observability

The system records evidence across the RAG/LLM pipeline.

Current telemetry includes:

### Retrieval

* Retrieved document ID
* Document type
* Rank
* Similarity score

### Augmentation

* User query
* Retrieved context
* Final context supplied to the LLM
* Prompt version

### Generation

* Model
* Token usage
* Response latency
* Generated answer

This allows failures to be localized to:

```text
Retrieval
→ Augmentation
→ Generation
→ Evaluation
```

rather than treating every incorrect AI response as a generic LLM failure.

---

## Repository Structure

```text
.github/workflows/    GitHub Actions CI workflows

data/                 Product and knowledge-source data
datasets/             Golden, evaluation and PR datasets
docs/                 Architecture and project documentation
logs/                 RAG and LLM execution traces
policies/             Approved and experimental policy sources
reports/              Evaluation outputs and baselines
src/                  RAG, LLM and evaluation implementation
tests/                Automated software tests
```

Important implementation components include:

```text
vector_store.py             Retrieval and vector search
constraint_filter.py        Structured constraint filtering
context_builder.py          RAG augmentation
llm_client.py               LLM integration

evaluation_runner.py        Full Golden execution
evaluator.py                AI evaluation
pr_evaluation_runner.py     PR critical execution
pr_evaluator.py             PR AI evaluation
quality_gate.py             CI quality-gate enforcement

retrieval_logger.py         Retrieval telemetry
context_logger.py           Context telemetry
llm_logger.py               LLM telemetry
```

---

## Planned Execution Model

The target CI/CD execution strategy is:

| Trigger         | Evaluation Scope                                   |
| --------------- | -------------------------------------------------- |
| Pull Request    | Critical AI subset                                 |
| Merge to `main` | Regression Dataset                                 |
| Nightly         | Full Evaluation Dataset                            |
| Release         | Golden + Regression + repeated critical evaluation |

This separates fast developer feedback from broader AI risk evaluation.

---
## Nightly Evaluation Baseline

The first full Nightly Evaluation executed 80 evaluation cases across the broader AI risk surface.

| Metric | Result |
|---|---:|
| Total Cases | 80 |
| Passed | 40 |
| Failed | 40 |
| Overall Pass Rate | 50.00% |
| Retrieval Hit Rate | 50.00% |
| Correctness Rate | 100.00% |
| Groundedness Rate | 98.75% |
| Constraint Adherence Rate | 100.00% |
| Hallucination Rate | 1.25% |
| Average Latency | 2914.25 ms |
| P95 Latency | 5110.67 ms |
| Total Input Tokens | 70,984 |
| Total Output Tokens | 13,573 |

The 50% overall pass rate must not currently be interpreted as 50% product quality.

The result is under root-cause analysis because the Overall Pass Rate exactly matches the 50% Retrieval Hit Rate while Correctness remains at 100%, Groundedness at 98.75%, Constraint Adherence at 100%, and Hallucination at 1.25%.

Nightly failures will therefore be classified before corrective action as:

- SUT defect;
- RAG / retrieval defect;
- dataset defect;
- expected-result / oracle defect;
- evaluator defect;
- non-deterministic / flaky AI behaviour.

Evaluation infrastructure defects must be separated from actual product-quality defects before thresholds, prompts, retrieval logic or datasets are changed.


## Next Implementation Steps

1. Analyze and classify the 80-case Nightly Evaluation failures.
2. Correct dataset, oracle, evaluator or retrieval defects identified during Nightly analysis.
3. Add Context Coverage measurement to validate whether retrieved context contains the evidence required to answer the query.
4. Add structured Priority, AI Risk and Execution Suite metadata to evaluation cases.
5. Expand risk-based AI evaluation coverage.
6. Implement the Defect → Regression mechanism so fixed AI defects become permanent regression cases.
7. Create sample Jira User Stories representing different AI risk profiles.
8. Build the Requirements / AI Risk / Test Design Agent.
9. Implement the Requirements Readiness / Entry Gate.
10. Implement AI Risk identification against a controlled project risk taxonomy.
11. Implement classical and AI-specific test-design technique selection.
12. Generate functional test coverage from eligible requirements.
13. Generate AI evaluation cases from eligible requirements and identified risks.
14. Implement semantic duplicate detection against existing evaluation coverage.
15. Recommend PR Critical, Regression or Nightly execution classification.
16. Generate and maintain the Excel-based evaluation repository for stakeholder review.
17. Add Human-in-the-Loop approval before executable dataset creation.
18. Implement approved Excel → JSON dataset export.
19. Build the Release Validation pipeline using Golden, Regression and repeated Critical coverage.
20. Add aggregated reporting across PR Critical, Regression and Nightly Evaluation.
21. Add historical metric and baseline comparison for quality, latency and token consumption.
22. Integrate Jira traceability, defect creation and evaluation evidence.
23. Build dedicated Golden and Evaluation datasets for testing the QA Agent itself.
24. Evaluate the QA Agent for correctness, hallucination, risk identification and test-generation quality.
25. Build the Test Management Lifecycle Agent.
26. Connect requirements, risks, tests, datasets, executions, defects and evidence into end-to-end traceability.
27. Add residual-risk reporting and GO / NO-GO release recommendations.
28. Update architecture diagrams, Test Strategy and project documentation as the lifecycle evolves.
29. Produce the final AI Quality Engineering case study / article.

---
## Future QA Agent

The next major extension of the AI QE Lab is a Requirements, Risk and Test Design Agent that connects requirement analysis with executable AI evaluation.

The target lifecycle is:

Jira User Story
    ↓
Requirements Review
    ↓
Entry / Readiness Gate
    ├── FAIL → Missing Information Report → STOP
    └── PASS
            ↓
AI Risk Identification
            ↓
Test Design Technique Selection
    ├── Equivalence Partitioning
    ├── Boundary Value Analysis
    ├── Pairwise / Combinatorial Testing
    ├── Negative Testing
    └── AI-specific Test Techniques
            ↓
Functional Test Generation
            +
AI Evaluation Case Generation
            ↓
Existing Dataset Review
            ↓
Duplicate / Similarity Detection
            ↓
Risk + Priority Classification
            ↓
Execution Suite Recommendation
    ├── PR Critical
    ├── Regression
    └── Nightly Evaluation
            ↓
Human Review / Approval
            ↓
Excel Test & Evaluation Repository
            ↓
Approved Dataset
            ↓
JSON Export
            ↓
Automated AI Evaluation Pipeline

### Requirements Readiness Gate

The agent must not generate tests or evaluation datasets from requirements that do not contain enough information to establish expected behaviour.

The readiness review checks:

- requirement description;
- acceptance criteria;
- identifiable expected behaviour;
- business constraints;
- data dependencies;
- source-of-truth information;
- negative and failure behaviour;
- AI-specific behaviour where applicable.

If the requirement is not ready, the agent produces a missing-information report and stops test generation.

This prevents the test-generation agent from inventing requirements that were never defined by the product team.

### AI Risk Analysis

For eligible requirements, the agent maps the requirement against the project's controlled AI risk taxonomy.

Example risks include:

- hallucination;
- retrieval failure;
- groundedness;
- constraint adherence;
- prompt injection;
- ambiguity;
- conflicting data;
- stale data;
- robustness;
- non-determinism;
- privacy and safety;
- bias and fairness where applicable.

Not every risk must apply to every requirement.

The purpose of the analysis is to identify the risks that are relevant to the specific user story or feature.

### Test Design

The agent selects appropriate classical and AI-specific test-design techniques.

Examples:

- Equivalence Partitioning for large input domains;
- Boundary Value Analysis for numeric constraints;
- Pairwise / combinatorial testing for multiple interacting constraints;
- Negative testing for invalid or unavailable conditions;
- adversarial testing for prompt injection;
- paraphrase and metamorphic testing for robustness;
- groundedness and retrieval evaluation for RAG behaviour.

Classical test-design techniques remain applicable to AI-enabled functionality and are combined with AI-specific risk-based evaluation.

### Functional Tests and AI Evaluation Cases

The agent produces two complementary forms of coverage.

Functional tests validate deterministic business behaviour.

AI evaluation cases validate probabilistic and AI-specific behaviour such as retrieval quality, hallucination, groundedness, robustness and constraint adherence.

A single Jira Story may therefore produce multiple functional tests and multiple AI evaluation cases.

### Dataset Design and Governance

The reviewable evaluation repository is maintained in Excel before becoming executable JSON.

Each evaluation case should contain traceability and governance metadata such as:

- Case ID;
- Jira Story / Requirement;
- AI Risk;
- Input / Question;
- Expected Behaviour;
- Expected Product or Source where applicable;
- Test Design Technique;
- Priority;
- Execution Suite;
- Approval Status.

Excel acts as the human-readable design and review layer.

JSON acts as the machine-executable representation used by the automated evaluation pipeline.

### Duplicate Detection

Before proposing a new evaluation case, the agent reviews existing Critical, Regression and Nightly coverage.

Duplicate detection must consider more than exact text matching.

The comparison should consider:

- requirement;
- test intent;
- AI risk;
- expected behaviour;
- semantic similarity.

For example:

"Find a waterproof black jacket under $150"

and

"Recommend a black waterproof jacket costing no more than $150"

may represent the same test intent.

The agent should identify the existing case and recommend reuse or additional requirement traceability instead of unnecessarily duplicating coverage.

### Risk-Based Execution Classification

Priority and AI Risk are separate dimensions.

Priority answers:

"How urgently and frequently should this behaviour be validated?"

AI Risk answers:

"What AI failure mode does this case mitigate?"

The agent recommends an execution suite for each approved evaluation case:

- PR Critical — fast, high-risk merge-blocking coverage;
- Regression — stable behaviour and previously fixed defects used to validate main;
- Nightly Evaluation — broad AI risk, adversarial, robustness, ambiguity, conflicting-data and extended coverage.

After human approval, Excel cases can be exported into the corresponding executable JSON datasets.

### Target End-to-End Lifecycle

Requirement
→ Requirements Review
→ Readiness Gate
→ AI Risk Analysis
→ Test Design
→ Functional Tests + AI Evaluation Cases
→ Duplicate Detection
→ Priority and Suite Classification
→ Human Approval
→ Excel Repository
→ JSON Export
→ Evaluation Runner
→ RAG
→ SUT
→ Evaluator
→ Quality Gate
→ Defect / Evidence
→ Regression Coverage


