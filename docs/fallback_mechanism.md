# Fallback Mechanism

When Oracle metadata is absent, the evaluator uses the case identifier as a key into the reviewed routing mapping. Supported identifier field names are `case_id`, `id`, and `ID`. A known mapping returns deterministic or semantic routing. An unknown mapping defaults to semantic LLM evaluation to avoid an unsupported deterministic PASS.
