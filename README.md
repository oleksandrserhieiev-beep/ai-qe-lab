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

## Next Implementation Steps

The next planned engineering tasks are:

1. Separate the **System Under Test model** from the **LLM Judge model**.
2. Add Hugging Face/model caching to CI.
3. Establish the Regression Dataset and regression baseline.
4. Add regression execution after changes to `main`.
5. Add scheduled full Evaluation Dataset execution.
6. Expand AI risk coverage for stale data, conflicting data, missing information, prompt injection, adversarial inputs, robustness, and bias/fairness.
7. Capture evidence-based RAG defects.
8. Integrate the lab with Jira.
9. Build and evaluate the QA Agent.
10. Build and evaluate the Test Management Lifecycle Agent.
11. Add end-to-end quality reporting, traceability, residual-risk assessment, and release governance.

---

## Future QA Agent

The planned QA Agent will support:

```text
Jira Requirement
      ↓
Requirements Review
      ↓
Risk Identification
      ↓
Test Generation
      ↓
Human Approval
      ↓
Execution Analysis
      ↓
Defect Draft
```

Agent evaluation will cover both expected and prohibited actions, including tool usage and Human-in-the-Loop controls.

---

## Future Test Management Lifecycle Agent

The planned Test Management Agent will consume:

* Requirements
* Architecture
* Risks
* Tests
* Executions
* Defects
* AI evaluation metrics
* Agent metrics

It will support:

* Test Strategy generation
* Test Planning
* Entry/Exit Criteria
* Test progress monitoring
* Test Completion Reporting
* GO / NO-GO recommendations

Final release accountability remains with the human Test Lead.

---

## Security and Cost Controls

* Never commit API keys or `.env`.
* Store CI credentials using GitHub Secrets.
* Use risk-based PR subsets to control LLM execution cost.
* Use dependency/model caching to reduce CI execution time.
* Keep future Jira agents read-only until Human-in-the-Loop controls are validated.
* Enable write operations only against a dedicated lab environment.
* Preserve case-level evidence for AI quality decisions.

---

## Project Goal

The final lab is intended to demonstrate an end-to-end AI Quality Engineering lifecycle:

```text
Requirements
    ↓
Risk Analysis
    ↓
AI System
    ↓
RAG / LLM Testing
    ↓
Automated Evaluation
    ↓
CI/CD Quality Gates
    ↓
Regression
    ↓
Agent Testing
    ↓
Traceability
    ↓
Metrics
    ↓
Residual Risk
    ↓
Release Decision
```

The objective is not merely to build an AI assistant, but to demonstrate how AI-enabled software can be **tested, measured, traced, governed, and released using an engineering-grade quality process**.
