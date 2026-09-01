# Human review boundary

The intended GitHub-native review model is proposal-first. The agent produces a reviewable proposal and does not silently mutate governed JSON.

Reviewer decisions:
- ADD: accept a new proposed record;
- EXTEND_EXISTING: review the existing record and proposed extension before approving the merged form;
- SKIP: keep the governed dataset unchanged;
- EDIT/REJECT/APPROVE are human controls around the proposed JSON change.

The concrete interactive GitHub implementation is deferred until the dataset mutation/promotion PR. This skeleton intentionally does not pretend that a running Actions log is a full editing UI.
