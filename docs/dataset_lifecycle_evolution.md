# Dataset Lifecycle Evolution

_Last synchronized with repository: 2026-09-01._

## Controlled SUT data vs QE governance inputs

The catalogue/policy knowledge base is controlled reference-SUT data. Jira requirements, reviewed risks and test metadata are QE governance inputs. They serve different purposes and must not be conflated.

```text
SUT knowledge/application data
= catalogue, policies, enterprise KB, databases, APIs, tools

QE governance inputs
= Jira requirements, reviewed Risk Registers, test proposals, governed datasets
```

## Current governed assets

PR Critical, Regression, Nightly and Golden are executable product-evaluation assets. Golden additionally represents canonical truth and has stronger change control. Judge Calibration is evaluator truth, not SUT test data. Adversarial and Metamorphic are technique-specific assets; Back-to-Back reuses the standard PR Critical cases.

Dataset/Oracle Validation checks technical execution contracts such as unique IDs, required fields, supported Oracle routes and deterministic assertions. It does not decide whether a proposed test should become governed coverage.

## Implemented upstream lifecycle

```text
Jira Requirement
→ Requirements Review
→ human readiness boundary
→ Risk Analysis
→ human Risk approval
→ approved Risk Register written to Jira Description
→ Test Analysis & Design
→ compare AC + risks against governed dataset snapshots
→ ADD / EXTEND_EXISTING / SKIP proposals
→ Human Decision
→ APPROVE / REJECT / EDIT / EXTEND_EXISTING
→ explicit confirmation
→ decision evidence
```

Test Analysis currently reads governed PR Critical, Regression, Nightly and Golden snapshots. Dataset health is validated deterministically before semantic analysis. Similarity is used as human decision evidence, not as an automatic duplicate threshold.

## Current promotion boundary

The following is intentionally **not implemented yet**:

```text
Confirmed Human Decision
→ mutate governed JSON
→ validate mutated dataset
→ create governed source-control diff/commit/PR
```

Until that slice exists, analysis and human-decision workflows do not mutate governed datasets.

## Required promotion semantics

When implemented:

- `APPROVE` → add the proposed new case;
- `REJECT` → no dataset change;
- `EDIT` → validate the human-edited proposal and then add it;
- `EXTEND_EXISTING` → apply a reviewed exact BEFORE → AFTER change to the selected existing case; never blindly concatenate JSON.

After mutation, deterministic validation must run before promotion. Golden candidates remain subject to separate Golden Governance and cannot bypass canonical-truth controls.

## Remaining lifecycle work

1. implement approved decision → dataset mutation;
2. validate schema, IDs, references, Oracle contract and integrity after mutation;
3. generate the source-control diff/commit/PR;
4. add Agent Evaluation Dataset for agent tools/permissions/HITL behavior;
5. later integrate external test-management systems where required.
