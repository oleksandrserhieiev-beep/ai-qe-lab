# Test Analysis & Design cache

The Test Analysis & Design stage uses the shared `agent_content_cache` primitive.

Fingerprint inputs include:
- agent identity;
- Jira issue key and Acceptance Criteria;
- reviewed risks;
- governed dataset snapshot identity/content marker;
- model;
- prompt;
- shared cache contract version.

A cache hit is valid only when all semantic inputs are unchanged. In particular, changing the governed dataset snapshot must invalidate the cache even if Jira content is unchanged, because existing coverage/duplicate/similarity conclusions may have changed.

Cache reuse is a cost optimization. Dataset health, human approval, and deterministic post-edit validation remain mandatory boundaries.
