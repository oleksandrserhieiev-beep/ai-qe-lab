# Test Analysis & Design — agreed decisions

1. Jira IDs are the intended workflow input; eligibility gates this stage before semantic work.
2. Requirements Review and Risk Analysis are upstream prerequisites.
3. Dataset health is checked before coverage proposals. Errors block; warnings are surfaced and may continue.
4. Coverage analysis compares Acceptance Criteria and risks with existing cases.
5. Exact duplicates, similar cases, existing coverage, and gaps are explicit outputs.
6. Similarity never auto-deletes a proposal. Human options include ADD, EXTEND_EXISTING, and SKIP.
7. EXTEND_EXISTING shows the existing case and proposed change for review.
8. Test Design proposes functional and AI-specific tests only where coverage is missing.
9. Evaluation proposals assign deterministic or semantic oracle strategy.
10. Target suite is proposed with rationale and approved by a human; Risk Score alone never routes a case.
11. Golden is a separate governed candidate path, not an ordinary execution tier.
12. Every proposal carries Requirement → AC → Risk → Test → Oracle → Target traceability.
13. Human Edit / Reject / Approve is the mutation boundary.
14. Approved JSON is deterministically validated before promotion.
15. The shared content-aware cache pattern is the default; dataset snapshot changes invalidate Test Analysis & Design cache entries.
