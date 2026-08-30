from llm_client import generate_answer
from constraint_validator import clarification_answer


NO_CONTEXT_ANSWER = (
    "I don't have enough information in the available context to answer that question."
)
NO_PRODUCT_MATCH_ANSWER = (
    "No matching products were found for all requested constraints."
)


def _skipped_telemetry(path, stop_reason):
    return {
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "latency_ms": 0.0,
        "stop_reason": stop_reason,
        "generation_path": path,
        "llm_call_skipped": True,
    }


def generate_grounded_answer(final_context, context_results, retrieval_metadata=None):
    """Generate only when input is resolved and governed evidence exists."""
    retrieval_metadata = retrieval_metadata or {}

    if retrieval_metadata.get("clarification_required"):
        validation = retrieval_metadata.get("constraint_validation", {})
        return clarification_answer(validation), _skipped_telemetry(
            "deterministic_clarification",
            "unresolved_constraint",
        )

    if retrieval_metadata.get("no_product_match"):
        return NO_PRODUCT_MATCH_ANSWER, _skipped_telemetry(
            "deterministic_no_product_match",
            "structured_no_match",
        )

    if context_results:
        answer, telemetry = generate_answer(final_context)
        telemetry = {**telemetry, "generation_path": "llm", "llm_call_skipped": False}
        return answer, telemetry

    return NO_CONTEXT_ANSWER, _skipped_telemetry(
        "deterministic_no_context",
        "no_context_abstention",
    )
