# Requirements Review Quality Model

The Requirements Review Agent uses a focused review model derived from ISO/IEC/IEEE 29148:2018 requirement quality characteristics and the tester-focused interpretation used by ISTQB.

## Primary requirement checks

These checks are the core readiness gate because they can be evaluated from the requirement itself and directly affect whether expected behavior can be tested without material assumptions.

| Criterion | Agent question | Blocking when |
| --- | --- | --- |
| Unambiguous | Is there one clear interpretation of the expected behavior? | Different reasonable interpretations would produce different expected results. |
| Complete | Is the information needed to understand the required behavior present? | A material business rule, outcome, exception, constraint, or acceptance condition is missing. |
| Consistent | Does the requirement avoid contradictions internally and with explicitly supplied requirement content? | Conflicting statements make expected behavior uncertain. |
| Singular / Atomic | Is each requirement or acceptance condition focused enough to understand and verify independently? | Bundled behaviors make the expected outcome materially unclear. |
| Verifiable | Can compliance be demonstrated through observable acceptance conditions? | There is no objective way to determine pass/fail for the required behavior. |

## Supporting checks

The agent may also identify necessity, correctness, feasibility, appropriateness, comprehensibility, or conformance concerns when the supplied requirement itself provides evidence of a problem. Absence of implementation detail or external context is not, by itself, a failure of these characteristics.

## Gap classification

### BLOCKING_GAP

Missing, ambiguous, or contradictory information that prevents a reviewer from determining expected business behavior or designing meaningful risk-based tests without inventing a material assumption.

Only blocking gaps can cause `NEEDS_CLARIFICATION`.

Typical examples:
- undefined acceptance outcome;
- referenced business rule or hard constraint is not defined;
- missing behavior for a material exception or no-result path;
- ambiguous terms that change expected behavior;
- contradictory acceptance criteria;
- no objective acceptance condition for a required outcome.

### NON_BLOCKING_GAP

A useful improvement to the requirement that does not prevent risk analysis or meaningful test design.

Examples:
- an NFR is not specified but the functional behavior remains testable;
- wording could be clearer without changing the expected result;
- optional edge-case detail can be refined later.

### TECHNICAL_CONTEXT_NEEDED

Information that may be needed later for implementation, integration analysis, detailed test design, or observability, but is not required to establish business requirement readiness.

Examples:
- concrete service/API used by the implementation;
- logging implementation;
- internal data source;
- deployment topology;
- technical response codes not specified as business behavior.

Technical context must not make the requirement fail the readiness gate.

## Decision rule

`READY` means there are zero `BLOCKING_GAP` findings.

`NEEDS_CLARIFICATION` means there is at least one `BLOCKING_GAP`.

The agent must not fail a requirement merely because it does not contain architecture, implementation, logging, API, database, or other technical details that can be resolved later from design documentation or Confluence.
