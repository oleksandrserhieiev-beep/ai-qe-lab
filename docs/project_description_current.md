# AI QE Lab — Project Description

AI QE Lab demonstrates practical Quality Engineering for AI-enabled systems using a Shopping RAG Assistant as the current SUT. Evaluation combines governed datasets, deterministic Python oracles, semantic LLM-as-a-Judge evaluation, AI-risk metadata, observability, CI/CD gates, telemetry and failure localization.

Oracle metadata defines how a case is evaluated. Explicit `deterministic` or `semantic_llm` metadata is primary; missing metadata uses the reviewed-ID fallback in `judge_routing.py`; an unknown ID safely defaults to `semantic_llm`. The LLM Judge evaluates semantic PASS/FAIL and does not classify the Oracle type.

The reviewed inventory is 6/4 deterministic/semantic for PR Critical, 7/8 for Regression, and 48/32 for Nightly: 61 deterministic and 44 semantic routes across 105 cases.

The next hardening layer is explicit deterministic atomic assertion coverage plus stricter Oracle metadata validation.
