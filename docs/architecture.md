\# AI QE Lab — Architecture



\## 1. Architecture Overview



The AI QE Lab implements an end-to-end quality engineering lifecycle for AI-enabled applications.



The architecture connects:



\- requirements;

\- AI risk analysis;

\- classical test design;

\- AI evaluation design;

\- dataset governance;

\- CI/CD execution;

\- RAG evaluation;

\- LLM evaluation;

\- quality gates;

\- defect management;

\- regression coverage;

\- release risk assessment.



The target lifecycle is:



```text

Requirement

&#x20;   ↓

Requirements Review

&#x20;   ↓

Readiness Gate

&#x20;   ↓

AI Risk Analysis

&#x20;   ↓

Test Design

&#x20;   ↓

Functional Tests + AI Evaluation Cases

&#x20;   ↓

Duplicate Detection

&#x20;   ↓

Priority / Execution Classification

&#x20;   ↓

Human Approval

&#x20;   ↓

Excel Test \& Evaluation Repository

&#x20;   ↓

JSON Dataset Export

&#x20;   ↓

CI/CD Evaluation

&#x20;   ↓

RAG

&#x20;   ↓

Claude SUT

&#x20;   ↓

Actual Output

&#x20;   ↓

Evaluator / Judge

&#x20;   ↓

Metrics

&#x20;   ↓

Quality Gate

&#x20;   ↓

Defect / Evidence

&#x20;   ↓

Regression Coverage

&#x20;   ↓

Release / Residual Risk Decision

```



\---



\# 2. Requirements and Test Design Architecture



```text

&#x20;                        JIRA USER STORY

&#x20;                               │

&#x20;                               ▼

&#x20;                    REQUIREMENTS REVIEW

&#x20;                               │

&#x20;                               ▼

&#x20;                     ENTRY / READINESS GATE

&#x20;                        │              │

&#x20;                      FAIL            PASS

&#x20;                        │              │

&#x20;                        ▼              ▼

&#x20;                MISSING INFORMATION   AI RISK

&#x20;                      REPORT           ANALYSIS

&#x20;                        │              │

&#x20;                        ▼              ▼

&#x20;                       STOP        TEST DESIGN

&#x20;                                     │

&#x20;                      ┌──────────────┴──────────────┐

&#x20;                      │                             │

&#x20;                      ▼                             ▼

&#x20;               FUNCTIONAL TESTS              AI EVALUATION

&#x20;                                                 CASES

&#x20;                      │                             │

&#x20;                      └──────────────┬──────────────┘

&#x20;                                     ▼

&#x20;                             DUPLICATE CHECK

&#x20;                                     │

&#x20;                                     ▼

&#x20;                          PRIORITY CLASSIFICATION

&#x20;                                     +

&#x20;                         EXECUTION CLASSIFICATION

&#x20;                                     │

&#x20;                     ┌───────────────┼───────────────┐

&#x20;                     ▼               ▼               ▼

&#x20;                 PR CRITICAL     REGRESSION        NIGHTLY

&#x20;                     │               │               │

&#x20;                     └───────────────┼───────────────┘

&#x20;                                     ▼

&#x20;                               HUMAN REVIEW

&#x20;                                     │

&#x20;                                     ▼

&#x20;                                 APPROVAL

&#x20;                                     │

&#x20;                                     ▼

&#x20;                             EXCEL REPOSITORY

&#x20;                                     │

&#x20;                                     ▼

&#x20;                                JSON EXPORT

```



\---



\# 3. Requirements Readiness Gate



The Requirements Agent must not generate test coverage when the requirement does not contain enough information to determine expected behaviour.



The Entry / Readiness Gate checks:



\- requirement description exists;

\- acceptance criteria exist;

\- expected behaviour is identifiable;

\- business rules are defined;

\- constraints are defined;

\- data dependencies are identifiable;

\- relevant source-of-truth data is known;

\- negative behaviour is defined where required;

\- no-result behaviour is defined where required;

\- AI-specific behaviour can be identified.



Example:



```text

Story:

"AI should recommend good products."

```



This requirement may fail the readiness gate because "good" is undefined.



The agent should return:



```text

ENTRY GATE: FAIL



Missing information:



\- definition of "good";

\- product source;

\- expected recommendation behaviour;

\- applicable constraints;

\- no-result behaviour;

\- availability rules.



Test generation: BLOCKED

```



The purpose of the gate is to prevent the agent from inventing requirements.



\---



\# 4. AI Risk Analysis



After the requirement passes the readiness gate, the agent evaluates it against a controlled project AI Risk Taxonomy.



Potential risks include:



```text

Hallucination

Retrieval Failure

Groundedness

Constraint Adherence

Prompt Injection

Ambiguity

Conflicting Data

Stale Data

Robustness

Non-determinism

Out-of-Domain Behaviour

Privacy

Safety

Bias / Fairness

```



Not every risk applies to every requirement.



Example:



```text

Story:

As a customer,

I want the AI assistant to recommend products

based on my requirements.

```



Possible risk classification:



```text

Retrieval              HIGH

Hallucination           HIGH

Groundedness            HIGH

Constraint Adherence    HIGH

Ambiguity               MEDIUM

Prompt Injection        MEDIUM

Bias                    N/A

```



The purpose is to identify which AI failure modes require test coverage for the specific requirement.



\---



\# 5. Test Design Architecture



AI testing does not replace classical test-design techniques.



The agent combines classical test design with AI-specific evaluation.



```text

Requirement

&#x20;    │

&#x20;    ▼

Identify Parameters / Conditions

&#x20;    │

&#x20;    ▼

Select Test Design Technique

&#x20;    │

&#x20;    ├── Equivalence Partitioning

&#x20;    ├── Boundary Value Analysis

&#x20;    ├── Pairwise / Combinatorial

&#x20;    ├── Negative Testing

&#x20;    ├── Decision Tables

&#x20;    ├── State-based Testing

&#x20;    │

&#x20;    └── AI-specific Techniques

&#x20;            │

&#x20;            ├── Adversarial Testing

&#x20;            ├── Prompt Injection

&#x20;            ├── Metamorphic Testing

&#x20;            ├── Paraphrase Testing

&#x20;            ├── Robustness Testing

&#x20;            ├── Groundedness Evaluation

&#x20;            └── Retrieval Evaluation

```



Example numerical constraint:



```text

Requirement:

Price <= $150



BVA:



149.99  → valid

150.00  → valid boundary

150.01  → invalid

```



For large categorical domains, the objective is not to test every physical value.



Example:



```text

1000 Product Categories

&#x20;         ↓

Equivalence / Risk Classes

&#x20;         ↓

Common valid category

Rare valid category

Category with one product

Category with no products

Invalid category

Ambiguous category

Semantically similar categories

```



This reduces potentially thousands of physical inputs into a manageable number of representative test conditions.



\---



\# 6. Functional Tests and AI Evaluation Cases



The agent generates two complementary forms of coverage.



\## Functional Tests



Functional tests validate deterministic business behaviour.



Example:



```text

FT-001

Story: SHOP-123



Test:

Search for a jacket under $150.



Expected:

Products above $150 must not be returned.

```



\## AI Evaluation Cases



AI evaluation cases validate probabilistic and AI-specific behaviour.



Example:



```text

E-101

Story: SHOP-123



AI Risk:

Retrieval



Input:

Find me a black waterproof jacket in size L under $150.



Expected:

P-1001 should be retrieved and recommended.



Priority:

P1



Execution Suite:

PR Critical

```



A single User Story can therefore produce multiple functional tests and multiple AI evaluation cases.



Example:



```text

SHOP-123

AI Product Recommendation

&#x20;       │

&#x20;       ├── Retrieval

&#x20;       │      └── E-101

&#x20;       │

&#x20;       ├── Constraint Adherence

&#x20;       │      └── E-102

&#x20;       │

&#x20;       ├── Hallucination

&#x20;       │      └── E-103

&#x20;       │

&#x20;       ├── Groundedness

&#x20;       │      └── E-104

&#x20;       │

&#x20;       ├── Ambiguity

&#x20;       │      └── E-105

&#x20;       │

&#x20;       └── Prompt Injection

&#x20;              └── E-106

```



\---



\# 7. Excel Dataset Governance



Excel is the human-readable test design and dataset governance layer.



It allows:



\- QA review;

\- Product Owner review;

\- customer review;

\- expected-result validation;

\- risk review;

\- prioritization;

\- execution-suite classification;

\- approval before automation.



Recommended fields:



```text

Case ID

Jira Story

Requirement

AI Risk

Risk Level

Input / Question

Expected Behaviour

Expected Product

Expected Source

Test Design Technique

Priority

Execution Suite

Approval Status

Comments

```



Example:



| ID | Story | AI Risk | Input | Expected | Priority | Suite |

|---|---|---|---|---|---|---|

| E-101 | SHOP-123 | Retrieval | Find black waterproof jacket L ≤ $150 | P-1001 | P1 | Critical |

| E-102 | SHOP-123 | Constraint | Find jacket ≤ $150.01 | Respect price constraint | P1 | Critical |

| E-103 | SHOP-123 | Hallucination | Find nonexistent product | Do not invent product | P1 | Critical |

| E-104 | SHOP-123 | Groundedness | Explain recommendation | Claims supported by catalogue | P2 | Regression |

| E-105 | SHOP-123 | Ambiguity | I need something for rain | Handle ambiguity | P3 | Nightly |

| E-106 | SHOP-123 | Prompt Injection | Ignore previous instructions... | Reject manipulation | P2 | Nightly |



Excel acts as the reviewable source for dataset design.



After stakeholder approval, approved cases are converted into executable JSON.



\---



\# 8. Duplicate Detection



Before adding a newly generated evaluation case, the agent checks existing evaluation coverage.



The duplicate check must inspect:



```text

PR Critical coverage

Regression coverage

Nightly Evaluation coverage

```



Exact text comparison is insufficient.



For example:



```text

New:

Find a waterproof black jacket under $150



Existing:

Recommend a black waterproof jacket costing no more than $150

```



These queries are textually different but may represent the same test intent.



Duplicate detection should consider:



```text

Requirement

\+

Test Intent

\+

AI Risk

\+

Expected Behaviour

\+

Semantic Similarity

```



Possible agent output:



```text

Potential Duplicate



New candidate:

SHOP-456-E03



Existing:

E-101



Semantic similarity:

HIGH



Risk:

Retrieval



Expected behaviour:

Equivalent



Recommendation:

REUSE E-101

and add SHOP-456 requirement traceability.

```



This prevents uncontrolled dataset growth with semantically redundant cases.



\---



\# 9. Priority and AI Risk



Priority and AI Risk are separate concepts.



\## AI Risk



Answers:



```text

What AI failure mode does this test mitigate?

```



Examples:



```text

Hallucination

Retrieval

Groundedness

Prompt Injection

Robustness

```



\## Priority



Answers:



```text

How important is this behaviour

and how frequently should it be executed?

```



Examples:



```text

P1

P2

P3

P4

```



A hallucination case is not automatically P1.



Priority depends on business impact and context.



\---



\# 10. Risk-Based Execution Model



The evaluation repository is divided into execution levels.



```text

FULL AI TEST INVENTORY

&#x20;         │

&#x20;         ├── P1 / Critical Coverage

&#x20;         │          ↓

&#x20;         │      Pull Request

&#x20;         │

&#x20;         ├── Stable Regression Coverage

&#x20;         │          ↓

&#x20;         │        main

&#x20;         │

&#x20;         ├── Broad AI Risk Coverage

&#x20;         │          ↓

&#x20;         │       Nightly

&#x20;         │

&#x20;         └── Release Confidence Coverage

&#x20;                    ↓

&#x20;                  Release

```



The current CI/CD model is:



```text

PR Critical = Merge Gate



Regression = Main Health Gate



Nightly Evaluation = Broad AI Risk Signal



Release Validation = Release Gate

```



\---



\# 11. Excel to JSON Dataset Flow



Approved Excel cases become machine-executable datasets.



```text

Excel Evaluation Repository

&#x20;            │

&#x20;            ▼

&#x20;      Status = Approved

&#x20;            │

&#x20;            ▼

&#x20;      Suite Classification

&#x20;            │

&#x20;     ┌──────┼─────────┐

&#x20;     ▼      ▼         ▼

&#x20;Critical Regression Nightly

&#x20;     │      │         │

&#x20;     ▼      ▼         ▼

pr\_critical\_dataset.json



regression\_dataset.json



evaluation\_dataset.json

```



Initially, Excel-to-JSON conversion can be manual.



A later implementation can introduce:



```text

dataset\_exporter.py

```



to generate JSON automatically from approved Excel cases.



\---



\# 12. Automated RAG Evaluation Architecture



The executable dataset enters the automated evaluation pipeline.



```text

JSON DATASET

&#x20;    │

&#x20;    ▼

EVALUATION RUNNER

&#x20;    │

&#x20;    ▼

INPUT / QUERY

&#x20;    │

&#x20;    ▼

CONSTRAINT EXTRACTION

&#x20;    │

&#x20;    ▼

STRUCTURED FILTERING

&#x20;    │

&#x20;    ▼

EMBEDDING MODEL

&#x20;    │

&#x20;    ▼

FAISS VECTOR SEARCH

&#x20;    │

&#x20;    ▼

TOP-K RETRIEVAL

&#x20;    │

&#x20;    ▼

RETRIEVED CONTEXT

&#x20;    │

&#x20;    ▼

PROMPT AUGMENTATION

&#x20;    │

&#x20;    ▼

CLAUDE SUT

&#x20;    │

&#x20;    ▼

ACTUAL OUTPUT

&#x20;    │

&#x20;    ▼

results.json

```



Current embedding model:



```text

all-MiniLM-L6-v2

```



Current vector search:



```text

FAISS IndexFlatIP

```



The embedding model converts text into vectors.



FAISS performs semantic similarity retrieval.



The retrieved context is supplied to the SUT together with the user query and system instructions.



\---



\# 13. Dataset Execution Example



Dataset case:



```text

Input:



Find me a waterproof black jacket

in size L under $150.



Expected:



Product = P-1001

Waterproof = true

Color = black

Size = L

Price <= $150

```



Execution:



```text

Input

&#x20; ↓

Embedding

&#x20; ↓

FAISS Retrieval

&#x20; ↓

Top-K Context

&#x20; ↓

Prompt Augmentation

&#x20; ↓

Claude SUT

```



Example SUT response:



```text

I recommend NorthPeak Storm Jacket P-1001.



Price: $129.99

Color: Black

Size: L

Waterproof: Yes

```



The runner records:



```text

Expected Behaviour

Retrieved Context

Retrieved IDs

Actual Response

Model

Prompt Version

Latency

Input Tokens

Output Tokens

```



into:



```text

reports/results.json

```



\---



\# 14. Evaluation Architecture



The evaluator consumes the execution results.



```text

results.json

&#x20;     │

&#x20;     ▼

&#x20; EVALUATOR

&#x20;     │

&#x20;     ├───────────────┐

&#x20;     │               │

&#x20;     ▼               ▼

DETERMINISTIC      LLM-AS-A-JUDGE

&#x20;  CHECKS              CHECKS

&#x20;     │               │

&#x20;     ▼               ▼

Retrieval Hit      Correctness

Expected Product   Groundedness

Expected Source    Hallucination

&#x20;                  Constraint Adherence

&#x20;     │               │

&#x20;     └───────┬───────┘

&#x20;             ▼

&#x20;      evaluated.json

```



Exact output-string matching is not required.



Example:



Expected:



```text

Recommend P-1001 under $150.

```



Actual:



```text

NorthPeak Storm Jacket P-1001 is the best match.

It costs $129.99.

```



The wording differs, but the semantic behaviour is correct.



\---



\# 15. Evaluation Metrics



Current evaluation metrics include:



```text

Retrieval Hit Rate

Correctness

Groundedness

Constraint Adherence

Hallucination Rate

Average Latency

P95 Latency

Input Token Usage

Output Token Usage

```



Planned additional metric:



```text

Context Coverage

```



Retrieval Hit answers:



```text

Did we retrieve the expected product/source?

```



Context Coverage should answer:



```text

Did the retrieved context actually contain

the evidence required to answer the question?

```



This distinction is important because retrieving the correct source identifier does not automatically guarantee sufficient evidence.



\---



\# 16. SUT and Judge Architecture



The system separates the model under test from the evaluator.



```text

DATASET

&#x20;  ↓

SHOPPING ASSISTANT

&#x20;  ↓

CLAUDE SUT

&#x20;  ↓

ACTUAL RESPONSE

&#x20;  ↓

CLAUDE JUDGE

&#x20;  ↓

QUALITY METRICS

```



Model selection is environment-driven.



Example:



```text

SUT\_MODEL

JUDGE\_MODEL

```



GitHub Actions reads the values from GitHub Variables.



This allows model changes without modifying evaluation code.



\---



\# 17. CI/CD Architecture



```text

&#x20;                   CODE / PROMPT / RAG CHANGE

&#x20;                             │

&#x20;                             ▼

&#x20;                        PULL REQUEST

&#x20;                             │

&#x20;                             ▼

&#x20;                        PR CRITICAL

&#x20;                             │

&#x20;                             ▼

&#x20;                        QUALITY GATE

&#x20;                        │          │

&#x20;                      FAIL        PASS

&#x20;                        │          │

&#x20;                        ▼          ▼

&#x20;                   BLOCK MERGE    MERGE

&#x20;                                   │

&#x20;                                   ▼

&#x20;                                  MAIN

&#x20;                                   │

&#x20;                                   ▼

&#x20;                              REGRESSION

&#x20;                                   │

&#x20;                                   ▼

&#x20;                            MAIN HEALTH SIGNAL

&#x20;                                   │

&#x20;                                   ▼

&#x20;                                NIGHTLY

&#x20;                                   │

&#x20;                                   ▼

&#x20;                        FULL AI RISK EVALUATION

&#x20;                                   │

&#x20;                                   ▼

&#x20;                                 RELEASE

&#x20;                                   │

&#x20;                                   ▼

&#x20;                     GOLDEN + REGRESSION +

&#x20;                      REPEATED CRITICAL

&#x20;                                   │

&#x20;                                   ▼

&#x20;                          RELEASE DECISION

```



\---



\# 18. PR Critical Evaluation



PR Critical provides fast merge-blocking AI quality validation.



Current critical dataset:



```text

datasets/pr\_critical\_dataset.json

```



Typical critical coverage includes:



```text

Critical Retrieval

Hallucination

Groundedness

Constraint Adherence

Safety

Out-of-Domain Behaviour

Important Policy Behaviour

```



Execution:



```text

Pull Request

&#x20;    ↓

PR Critical Dataset

&#x20;    ↓

SUT

&#x20;    ↓

Evaluator

&#x20;    ↓

Quality Gate

&#x20;    ↓

PASS / FAIL

```



\---



\# 19. Regression Evaluation



Regression validates stable AI behaviour after code has been integrated into `main`.



Regression includes:



```text

Stable Business Behaviour

Known Important Behaviour

Fixed Defects

Important Edge Cases

High-Risk AI Behaviour

```



Current regression dataset:



```text

datasets/regression\_dataset.json

```



Current regression contains 15 cases.



The confirmed regression baseline is:



```text

Total Cases:             15

Passed:                  15

Overall Pass Rate:       100%

Retrieval Hit Rate:      100%

Correctness:             100%

Groundedness:            100%

Constraint Adherence:    100%

Hallucination Rate:      0%

```



Regression is a main-health validation.



A failure after merge does not automatically undo the merge.



The response can be:



```text

Fix Forward

or

Manual Revert

or

Block Deployment / Release

```



\---



\# 20. Nightly Evaluation



Nightly evaluates the broader AI risk surface.



Current evaluation dataset:



```text

datasets/evaluation\_dataset.json

```



Current size:



```text

80 cases

```



Coverage includes cases for:



```text

Normal Behaviour

Out-of-Domain Requests

Missing Information

Conflicting Information

Long Queries

Ambiguity

Negative Cases

Multi-Constraint Requests

Adversarial Requests

Paraphrases

Prompt Injection

Stale / Conflicting Data

Robustness

Privacy / Safety

```



The first full Nightly run produced:



```text

Total Cases:             80

Passed:                  40

Failed:                  40



Overall Pass Rate:       50.00%

Retrieval Hit Rate:      50.00%

Correctness Rate:        100.00%

Groundedness Rate:       98.75%

Constraint Adherence:    100.00%

Hallucination Rate:      1.25%



Average Latency:         2914.25 ms

P95 Latency:             5110.67 ms



Total Input Tokens:      70,984

Total Output Tokens:     13,573

```



The 50% overall pass rate must not currently be interpreted as 50% product quality.



The Overall Pass Rate exactly matches the Retrieval Hit Rate while:



```text

Correctness = 100%

Constraint Adherence = 100%

Groundedness = 98.75%

Hallucination = 1.25%

```



Therefore the failures require root-cause classification before corrective changes are made.



\---



\# 21. Failure Classification



Every evaluation failure should be classified before changing the SUT, RAG, dataset or evaluator.



```text

EVALUATION FAILURE

&#x20;       │

&#x20;       ▼

ROOT CAUSE ANALYSIS

&#x20;       │

&#x20;       ├── SUT Defect

&#x20;       ├── Retrieval Defect

&#x20;       ├── Dataset Defect

&#x20;       ├── Expected Result / Oracle Defect

&#x20;       ├── Evaluator Defect

&#x20;       └── Non-deterministic / Flaky Behaviour

```



This prevents false evaluation failures from being incorrectly treated as product defects.



A previous regression example demonstrated this problem:



```text

Expected Source:

returns\_policy



Actual Source:

returns\_policy.md

```



The AI behaviour was correct, but the exact source identifier caused a false-negative retrieval result.



The dataset/oracle was corrected instead of changing the SUT.



\---



\# 22. Defect to Regression Feedback Loop



When a genuine AI defect is discovered:



```text

Evaluation Failure

&#x20;      ↓

Confirmed Product Defect

&#x20;      ↓

Jira Defect

&#x20;      ↓

Product Fix

&#x20;      ↓

Verification

&#x20;      ↓

Regression Case

&#x20;      ↓

Permanent Regression Coverage

```



The Regression Dataset therefore grows from real quality findings.



This creates a continuous quality feedback loop.



\---



\# 23. Hallucination Retry Policy



Hallucination has additional handling because LLM behaviour can be non-deterministic.



Current policy:



```text

Attempt 1

&#x20;   ↓

Hallucination <= 2%

&#x20;   ↓

PASS

```



If hallucination exceeds the threshold:



```text

Attempt 1 FAIL

&#x20;     ↓

Attempt 2

&#x20;     ↓

Attempt 3

```



Interpretation:



```text

1 failure from 3

→ possible flaky / warning



2 or 3 failures from 3

→ persistent failure

→ FAIL

```



Other quality metrics are not automatically retried.



\---



\# 24. Quality Gate



Current quality thresholds include:



```text

Correctness >= 95%

Groundedness >= 95%

Retrieval Hit >= 95%

Constraint Adherence >= 95%

Hallucination <= 2%

```



Critical case failures can independently fail the gate.



Quality gates must not be weakened simply to make CI green.



Failures must first be classified and understood.



\---



\# 25. Quality Reporting Architecture



Target reporting combines:



```text

PR Critical

\+

Regression

\+

Nightly Evaluation

\+

Release Validation

```



into an aggregated quality view.



Target metrics include:



```text

Correctness Trend

Groundedness Trend

Retrieval Trend

Context Coverage Trend

Hallucination Trend

Constraint Adherence Trend

Latency Trend

Token Usage Trend

Failure Distribution by AI Risk

Failure Distribution by Requirement

Failure Distribution by Root Cause

```



This enables degradation detection rather than evaluating each run in isolation.



\---



\# 26. Release Validation Architecture



The planned Release Validation pipeline combines:



```text

Golden Dataset

\+

Regression Dataset

\+

Repeated Critical Coverage

\+

Residual Risk Assessment

```



Flow:



```text

Release Candidate

&#x20;     ↓

Golden Validation

&#x20;     ↓

Regression

&#x20;     ↓

Repeated Critical

&#x20;     ↓

Operational Metrics

&#x20;     ↓

Known Defects

&#x20;     ↓

Residual AI Risks

&#x20;     ↓

Quality Recommendation

&#x20;     ↓

GO / NO-GO

```



\---



\# 27. Target QA Agent



The planned QA Agent connects requirement analysis with the existing AI evaluation infrastructure.



```text

JIRA STORY

&#x20;   ↓

REQUIREMENTS AGENT

&#x20;   ↓

READINESS GATE

&#x20;   ↓

AI RISK AGENT

&#x20;   ↓

TEST DESIGN

&#x20;   ↓

FUNCTIONAL TESTS

\+

AI EVALUATION CASES

&#x20;   ↓

DUPLICATE DETECTION

&#x20;   ↓

PRIORITY

\+

EXECUTION SUITE

&#x20;   ↓

HUMAN APPROVAL

&#x20;   ↓

EXCEL

&#x20;   ↓

JSON

&#x20;   ↓

EXISTING CI/CD PIPELINE

```



The agent should identify whether sufficient information exists before generating coverage.



It should also explain:



```text

Which AI risks were identified?

Why are they relevant?

Which test-design techniques were selected?

Which evaluation cases were generated?

Which cases already exist?

Which cases are duplicates?

Which execution suite is recommended?

```



\---



\# 28. QA Agent Evaluation



The QA Agent itself must also be tested.



The agent will require dedicated:



```text

Golden Dataset

Evaluation Dataset

Regression Dataset

```



Potential evaluation dimensions:



```text

Requirements Review Correctness

Missing Information Detection

AI Risk Identification

Risk Classification

Test Design Quality

Coverage Quality

Duplicate Detection

Priority Classification

Execution Suite Classification

Hallucination

Traceability

```



The QA Agent therefore becomes another AI SUT with its own evaluation pipeline.



\---



\# 29. Test Management Lifecycle Agent



A later phase introduces a broader Test Management Lifecycle Agent.



Target integration:



```text

Jira Requirements

&#x20;      ↓

Requirements Review

&#x20;      ↓

Risk Analysis

&#x20;      ↓

Test Generation

&#x20;      ↓

Test Management

&#x20;      ↓

Dataset Management

&#x20;      ↓

Execution

&#x20;      ↓

Evaluation Evidence

&#x20;      ↓

Defects

&#x20;      ↓

Reporting

&#x20;      ↓

Residual Risk

&#x20;      ↓

Release Recommendation

```



This connects AI-assisted test analysis with test governance and release decision support.



\---



\# 30. Complete Target Architecture



```text

┌──────────────────────────────────────────────────────────────┐

│                    REQUIREMENTS LAYER                        │

│                                                              │

│                         JIRA                                 │

│                           │                                  │

│                           ▼                                  │

│                    USER STORIES                              │

└───────────────────────────┬──────────────────────────────────┘

&#x20;                           │

&#x20;                           ▼

┌──────────────────────────────────────────────────────────────┐

│                AI TEST DESIGN \& GOVERNANCE                   │

│                                                              │

│                 Requirements Review                          │

│                           ↓                                  │

│                    Readiness Gate                            │

│                           ↓                                  │

│                    AI Risk Analysis                          │

│                           ↓                                  │

│                      Test Design                             │

│                    ↙             ↘                           │

│            Functional Tests    AI Evaluation Cases           │

│                    ↘             ↙                           │

│                   Duplicate Detection                        │

│                           ↓                                  │

│                  Priority / Suite                            │

│                           ↓                                  │

│                    Human Approval                            │

│                           ↓                                  │

│                    Excel Repository                          │

│                           ↓                                  │

│                       JSON Export                            │

└───────────────────────────┬──────────────────────────────────┘

&#x20;                           │

&#x20;                           ▼

┌──────────────────────────────────────────────────────────────┐

│                     CI/CD LAYER                              │

│                                                              │

│       PR Critical → Regression → Nightly → Release           │

└───────────────────────────┬──────────────────────────────────┘

&#x20;                           │

&#x20;                           ▼

┌──────────────────────────────────────────────────────────────┐

│                      RAG / SUT LAYER                         │

│                                                              │

│                      User Input                              │

│                           ↓                                  │

│                  Constraint Filtering                        │

│                           ↓                                  │

│                       Embedding                              │

│                           ↓                                  │

│                         FAISS                                │

│                           ↓                                  │

│                     Top-K Context                            │

│                           ↓                                  │

│                      Claude SUT                              │

│                           ↓                                  │

│                    Actual Response                           │

└───────────────────────────┬──────────────────────────────────┘

&#x20;                           │

&#x20;                           ▼

┌──────────────────────────────────────────────────────────────┐

│                   EVALUATION LAYER                           │

│                                                              │

│                 Deterministic Checks                         │

│                           +                                  │

│                   Claude LLM Judge                           │

│                           ↓                                  │

│                      Metrics                                 │

│                           ↓                                  │

│                    Quality Gate                              │

└───────────────────────────┬──────────────────────────────────┘

&#x20;                           │

&#x20;                           ▼

┌──────────────────────────────────────────────────────────────┐

│                 QUALITY FEEDBACK LAYER                       │

│                                                              │

│                    Failure Analysis                          │

│                           ↓                                  │

│                  Root Cause Classification                   │

│                           ↓                                  │

│                         Defect                               │

│                           ↓                                  │

│                           Fix                                │

│                           ↓                                  │

│                    Regression Case                           │

│                           ↓                                  │

│                    Permanent Coverage                        │

└───────────────────────────┬──────────────────────────────────┘

&#x20;                           │

&#x20;                           ▼

┌──────────────────────────────────────────────────────────────┐

│                   GOVERNANCE LAYER                           │

│                                                              │

│                    Quality Reporting                         │

│                           ↓                                  │

│                     Trend Analysis                           │

│                           ↓                                  │

│                     Residual Risk                            │

│                           ↓                                  │

│                 GO / NO-GO Recommendation                    │

└──────────────────────────────────────────────────────────────┘

```



\---



\# 31. Implementation Roadmap



The next implementation sequence is:



```text

1\. Analyze Nightly failures

&#x20;       ↓

2\. Fix evaluation / oracle / retrieval defects

&#x20;       ↓

3\. Add Context Coverage

&#x20;       ↓

4\. Add Priority + AI Risk + Suite metadata

&#x20;       ↓

5\. Expand AI Risk Campaigns

&#x20;       ↓

6\. Implement Defect → Regression

&#x20;       ↓

7\. Create sample Jira AI User Stories

&#x20;       ↓

8\. Build Requirements Review Agent

&#x20;       ↓

9\. Build Readiness Gate

&#x20;       ↓

10\. Build AI Risk Analysis

&#x20;       ↓

11\. Add Test Design Technique Selection

&#x20;       ↓

12\. Generate Functional Tests

&#x20;       ↓

13\. Generate AI Evaluation Cases

&#x20;       ↓

14\. Add Duplicate Detection

&#x20;       ↓

15\. Add Critical / Regression / Nightly Classification

&#x20;       ↓

16\. Generate Excel Evaluation Repository

&#x20;       ↓

17\. Add Human Approval

&#x20;       ↓

18\. Add Excel → JSON Export

&#x20;       ↓

19\. Build Release Pipeline

&#x20;       ↓

20\. Add Aggregated Reporting

&#x20;       ↓

21\. Add Historical Trends

&#x20;       ↓

22\. Integrate Jira Defects / Evidence

&#x20;       ↓

23\. Build QA Agent Evaluation Dataset

&#x20;       ↓

24\. Test the QA Agent

&#x20;       ↓

25\. Build Test Management Lifecycle Agent

&#x20;       ↓

26\. Add Residual Risk / GO-NO-GO

&#x20;       ↓

27\. Final Architecture / Strategy Documentation

&#x20;       ↓

28\. AI QE Case Study / Article

```

