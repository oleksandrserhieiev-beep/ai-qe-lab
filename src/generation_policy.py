from llm_client import generate_answer


NO_CONTEXT_ANSWER = (
    "I don't have enough information in the available context to answer that question."
)


def generate_grounded_answer(final_context, context_results):
    """Generate only when selected grounding evidence exists.

    When Adaptive Context Selection returns no evidence, do not call the SUT LLM.
    Return a deterministic abstention and zero-cost telemetry instead.
    """
    if context_results:
        answer, telemetry = generate_answer(final_context)
        telemetry = {**telemetry, "generation_path": "llm"}
        return answer, telemetry

    return NO_CONTEXT_ANSWER, {
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "latency_ms": 0.0,
        "stop_reason": "no_context_abstention",
        "generation_path": "deterministic_no_context",
        "llm_call_skipped": True,
    }
