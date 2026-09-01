# CI/CD / Suite Execution Pipeline

_Last synchronized with repository: 2026-09-01._

## Purpose

This document is the detailed zoom-in for the **CI/CD / Suite Execution** block from the Master Architecture. It shows how lifecycle triggers select governed assets, invoke the shared validation → SUT → evaluation components, and turn evidence into the corresponding lifecycle decision.

Ordinary lifecycle suites use the common linear execution chain. Specialized AI-testing workflows reuse the same governed SUT/evaluation components where applicable but have their own execution topology, Oracle/aggregation and gate.

## Detailed state / decision flow

```mermaid
flowchart TD
    T{"Lifecycle trigger"}

    T -->|Pull Request| PR["PR Critical Standard"]
    T -->|Manual Regression| REG["Regression"]
    T -->|Manual Broad Nightly| NIGHT["Broad Nightly Evaluation"]
    T -->|Release Candidate / Manual| REL["Release Validation"]

    PR --> SEL["Selected Governed Suite"]
    REG --> SEL
    NIGHT --> SEL
    REL --> SEL

    SEL --> DV{"Dataset / Oracle Validation passes?"}
    DV -->|no| VF["Validation FAIL\nStop before model calls"]
    DV -->|yes / fallback-eligible| SUT["Application / SUT Pipeline"]
    SUT --> OUT["SUT Output + Telemetry"]
    OUT --> EV["Evaluation Pipeline"]
    EV --> MR["Metrics / Risk Aggregation + Localization"]
    MR --> QG{"Product Quality Gate"}
    QG -->|pass| PASS["PASS Evidence"]
    QG -->|fail| FAIL["FAIL Evidence"]
    PASS --> DEC["Lifecycle Decision"]
    FAIL --> DEC
    VF --> DEC

    T -->|Pull Request| META["Metamorphic Critical"]
    T -->|Manual comparison| B2B["Back-to-Back"]
    T -->|Nightly / Manual| ADV["Adversarial"]

    META --> MDV{"Dataset Validation passes?"}
    MDV -->|no| MVF["Validation FAIL"]
    MDV -->|yes| BASE["Base SUT Invocation"]
    MDV -->|yes| TRANS["Transformed SUT Invocation"]
    BASE --> MOR["Deterministic Relation Oracle"]
    TRANS --> MOR
    MOR --> MG{"Metamorphic Gate"}
    MG --> ME["Metamorphic Evidence"]
    MVF --> ME

    B2B --> BDV{"Dataset / Oracle Validation passes?"}
    BDV -->|no| BVF["Validation FAIL"]
    BDV -->|yes| MA["Model A SUT + Evaluation"]
    BDV -->|yes| MB["Model B SUT + Evaluation"]
    MA --> CMP["Comparator\nQuality + Regression + Telemetry Deltas"]
    MB --> CMP
    CMP --> BE["Comparison Evidence"]
    BVF --> BE

    ADV --> ADVV{"Dataset / Oracle Validation passes?"}
    ADVV -->|no| AVF["Validation FAIL"]
    ADVV -->|yes| ASUT["Application / SUT Pipeline"]
    ASUT --> AEV["Evaluation Pipeline"]
    AEV --> AAGG["Adversarial Aggregation\nPass Rate / Attack Success Rate / Category"]
    AAGG --> AG{"Adversarial Gate"}
    AG --> AE["Adversarial Evidence"]
    AVF --> AE

    ME --> SDEC["Specialized Lifecycle Evidence / Decision"]
    BE --> SDEC
    AE --> SDEC
```

## Current lifecycle state

```mermaid
flowchart LR
    PR["PR Critical"] -->|automatic| M["Merge Decision"]
    META["Metamorphic Critical"] -->|automatic| M
    REG["Regression"] -->|manual| RE["Regression Evidence"]
    NIGHT["Broad Nightly"] -->|manual| NE["Broad Quality Evidence"]
    ADV["Adversarial"] -->|manual + nightly| AE["Adversarial Gate"]
    REL["Release Validation"] -->|manual / RC| RD["GO / NO-GO Evidence"]
    B2B["Back-to-Back"] -->|manual| CMP["Model / Configuration Comparison"]
```

Broad Regression/Nightly product schedules are intentionally paused. Back-to-Back reuses the 10 standard PR Critical cases. Golden is used as canonical release/reference truth under separate governance; Judge Calibration validates evaluator quality separately.

## Shared execution boundary

Ordinary governed suites reuse the same architectural chain:

```text
Selected Governed Suite
-> Dataset / Oracle Validation
-> Application / SUT Pipeline
-> SUT Output + Telemetry
-> Evaluation Pipeline
-> Metrics / Risk Aggregation + Failure Localization
-> Product Quality Gate
-> Evidence
-> Lifecycle Decision
```

Specialized workflows reuse those components compositionally rather than redefining the SUT architecture:

```text
Metamorphic
validated META cases
-> base + transformed SUT invocations
-> deterministic relation Oracle
-> Metamorphic Gate

Back-to-Back
same validated 10 PR Critical standard cases
-> Model A SUT + Evaluation
-> Model B SUT + Evaluation
-> comparator
-> comparison evidence

Adversarial
validated adversarial cases
-> SUT
-> Evaluation
-> adversarial-specific aggregation
-> Adversarial Gate
```
