# Oracle Routing Notes

Primary route: explicit dataset/runtime Oracle. Fallback route: normalize `case_id` / `id` / `ID` and use the manually reviewed mapping in `judge_routing.py`. Final safe fallback for an unknown ID: `semantic_llm`. The Judge then evaluates PASS/FAIL; it does not decide the Oracle classification.
