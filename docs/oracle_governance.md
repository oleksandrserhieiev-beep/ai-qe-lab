# Oracle Governance

New governed cases should explicitly declare `Oracle = deterministic` or `Oracle = semantic_llm`. Missing values may use fallback for backward compatibility. Unsupported non-empty Oracle values should fail validation. Unknown cases must not be guessed deterministic because deterministic execution requires formal assertions.
