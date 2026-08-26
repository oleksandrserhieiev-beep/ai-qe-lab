# AI QE Lab — Prerequisites Pack

Purpose: build and test three AI workstreams: (1) Shopping RAG Assistant, (2) QA Agent, (3) Test Management Lifecycle Agent.

## Start here
1. Read `AI_QE_Lab_Prerequisites_and_Build_Guide.docx`.
2. Review diagrams in `docs/`.
3. Open `AI_QE_Lab_Datasets_and_Governance.xlsx`.
4. Inspect `data/products.json` and `policies/`.
5. Do **not** load files containing `DO_NOT_APPROVE` or `TEST_FIXTURE` into the approved knowledge base until the controlled-failure exercises.
6. Create a local repository named `ai-qe-lab`.
7. Follow Phase 0 → Phase 7 from the guide.

## Safety / cost
- Keep API keys in `.env`; never commit them.
- Start with low API spend limits.
- Keep Jira agents read-only until Human-in-the-loop is working.
- Enable writes only for a dedicated lab Jira project.
