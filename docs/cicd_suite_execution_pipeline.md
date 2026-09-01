# CI/CD / Suite Execution Pipeline

_Last synchronized with repository: 2026-09-01._

## Purpose

This document is the detailed zoom-in for the **CI/CD / Suite Execution** block from the Master Architecture. It shows how a lifecycle trigger selects a governed suite, invokes the shared validation → SUT → evaluation chain, and turns evidence into the corresponding lifecycle decision.

## Detailed state / decision flow

```mermaid
flowchart TD
    T{"Lifecycle trigger"}
    T -->|Pull Request| PR["PR Critical + Metamorphic Critical"]
    T -->|Manual Regression| REG["Regression"]
    T -->|Manual Broad Nightly| NIGHT["Broad Nightly Evaluation"]
    T -->|Nightly / Manual Adversarial| ADV["Adversarial"]
    T -->|Release Candidate / Manual| REL["Release Validation"]
    T -->|Manual comparison| B2B["Back-to-Back"]

    PR --> SEL["Selected Governed Suite"]
    REG --> SEL
    NIGHT --> SEL
    ADV --> SEL
    REL --> SEL
    B2B --> SEL

    SEL --> DV{"Dataset / Oracle Validation passes?"}
    DV -->|no| VF["Validation FAIL\nStop before model calls"]
    DV -->|yes / fallback-eligible| SUT["Application / SUT Pipeline"]

    SUT --> OUT["SUT Output + Telemetry"]
    OUT --> EV["Evaluation Pipeline"]
    EV --> QG{"Applicable Quality Gate"}

    QG -->|pass| PASS["PASS Evidence"]
    QG -->|fail| FAIL["FAIL Evidence + Localization"]

    PASS --> DEC["Lifecycle Decision"]
    FAIL --> DEC
    VF --> DEC
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

Every ordinary governed suite reuses the same architectural chain rather than owning another application or evaluation architecture:

```text
Selected Governed Suite
-> Dataset / Oracle Validation
-> Application / SUT Pipeline
-> SUT Output + Telemetry
-> Evaluation Pipeline
-> Quality Gate
-> Evidence
-> Lifecycle Decision
```

Specialized workflows may add their own comparison/relation/adversarial aggregation, but they do not redefine the SUT pipeline.