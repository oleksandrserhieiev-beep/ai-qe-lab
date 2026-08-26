# Seed Requirements

## Epic SHOP — Shopping AI Assistant
### SHOP-001 Product search by constraints
As a shopper, I want to describe product constraints in natural language so that the assistant recommends matching catalogue items.
AC1: Recommendations must exist in the approved catalogue.
AC2: Explicit price, size, colour and waterproof constraints must be respected when supplied.
AC3: The response should identify the product and relevant attributes.

### SHOP-002 Policy Q&A
As a shopper, I want answers about returns, delivery, warranty and payment policies.
AC1: Policy answers must be grounded in approved policy sources.
AC2: If approved sources do not contain the answer, the assistant must not invent a policy.

### SHOP-003 Source transparency
The assistant should expose source identifiers used to support policy/product answers.

### SHOP-004 Safe payment assistance
The assistant must not request or expose full card numbers or CVV.

### SHOP-005 Ambiguous product request
As a shopper, I want useful help when my request is incomplete.
Note: acceptance criteria intentionally incomplete for requirements-review exercises.

## Epic AGENT — QA Agent
### AGENT-001 Requirements review
Read a Jira story and identify ambiguity, missing acceptance criteria, contradictions and testability gaps.
### AGENT-002 Risk analysis
Identify product, AI and integration risks grounded in the story and architecture.
### AGENT-003 Test generation
Generate positive, negative, edge and AI-specific tests linked to requirements/risks.
### AGENT-004 Defect creation
After failed execution, prepare a defect with evidence. Jira write requires Human approval initially.

## Epic TM — Test Management Lifecycle Agent
### TM-001 Test strategy
Generate one programme-level test strategy with stream-specific approaches.
### TM-002 Test plan
Generate and maintain a project test plan using a 29119-based documentation structure.
### TM-003 Monitoring
Consume execution, defect and AI evaluation metrics and produce status summaries.
### TM-004 Completion and recommendation
Produce completion report and release recommendation. Entry/Exit criteria are proposed by the agent but approved/changed by the Test Lead.
