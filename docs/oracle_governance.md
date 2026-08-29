# Oracle Governance

New governed cases should explicitly declare `Oracle = deterministic` or `Oracle = semantic_llm`. Current Dataset Validation permits missing/null/empty Oracle only as a recoverable warning for fallback compatibility, rejects unsupported non-empty Oracle values, rejects missing/duplicate IDs, and requires non-empty deterministic assertions for a deterministic Oracle. Unknown cases are never guessed deterministic because deterministic execution requires formal assertions.

The dataset is authoritative. The next governance step is to generate/refresh the fallback mapper from validated approved dataset metadata rather than maintain it independently.
