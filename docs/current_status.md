# Current Evaluation Status

Current implementation includes: structured constraint filtering, FAISS Top-K retrieval, adaptive similarity-based context selection at the retained `0.30` threshold, Dataset/Oracle Validation in PR Critical/Regression/Nightly, reviewed Oracle routing with safe fallback, and structured deterministic assertions for all 61 deterministic cases (6 Critical, 7 Regression, 48 Nightly). The 44 semantic cases continue through the LLM Judge.

Adaptive Context Selection is now hardened for the zero-evidence path: when `Context-K=0`, the Claude SUT call is skipped and the system returns a deterministic abstention with zero SUT tokens and zero SUT latency. This prevents the model from answering from pretrained knowledge when no governed retrieval evidence survives selection.

Regression case `R-014` now exercises a real conflicting-policy scenario using a case-scoped test fixture. Approved production policy indexing remains unchanged; the conflicting fixture is injected only for the declared evaluation case.

For this hardening PR only, the PR workflow temporarily verifies PR Critical (10), Regression (15), and Nightly Evaluation (80) end to end. After all three are confirmed healthy, the extra Regression and Nightly PR checks should be removed.

Next after hardening is complete: final RAG evaluation review, then Jira integration and the Requirements Review / AI Risk Analysis / Test Design agent workflow.
