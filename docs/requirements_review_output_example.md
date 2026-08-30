# Requirements Review Output Example

The GitHub Actions summary renders findings in a compact table so reviewers can distinguish readiness blockers from useful context.

| # | Type | Severity | ISO/quality criterion | Category | Finding | Clarification |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | BLOCKING_GAP | HIGH | complete | acceptance_criteria | Success criteria are not defined. | What constitutes a successful result? |
| 2 | NON_BLOCKING_GAP | LOW | verifiable | nfr | No response-time target is stated. | |
| 3 | TECHNICAL_CONTEXT_NEEDED | MEDIUM | other | dependency | Concrete catalog service is not stated in the story. | |

Only `BLOCKING_GAP` findings affect the READY / NEEDS_CLARIFICATION gate.
