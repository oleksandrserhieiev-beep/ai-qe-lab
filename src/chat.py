from vector_store import DEFAULT_TOP_K, build_documents, build_vector_store, search_with_metadata
from context_builder import build_context, PROMPT_VERSION
from context_selector import get_context_selection_config, select_context_results
from retrieval_logger import log_retrieval
from context_logger import log_context
from generation_policy import generate_grounded_answer
from llm_logger import log_llm_call


RETRIEVAL_K = DEFAULT_TOP_K


def main():
    print("Initializing Shopping AI Assistant...")

    documents = build_documents()
    model, index = build_vector_store(documents)
    selection_config = get_context_selection_config()

    print(
        "Adaptive context selection: "
        f"retrieval_k={RETRIEVAL_K}, "
        f"target_min_k={selection_config['min_k']}, "
        f"max_k={selection_config['max_k']}, "
        f"min_similarity={selection_config['min_similarity']:.2f}"
    )
    print("Ready.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("Bye.")
            break
        if not query:
            continue

        retrieved, retrieval_routing = search_with_metadata(
            query=query,
            model=model,
            index=index,
            documents=documents,
            top_k=RETRIEVAL_K,
        )
        context_results = select_context_results(retrieved)
        log_retrieval(query=query, results=retrieved)

        final_context = build_context(query=query, results=context_results)
        log_context(query=query, final_context=final_context, prompt_version=PROMPT_VERSION)

        answer, telemetry = generate_grounded_answer(
            final_context,
            context_results,
            retrieval_metadata=retrieval_routing,
        )
        log_llm_call(query=query, answer=answer, telemetry=telemetry, prompt_version=PROMPT_VERSION)

        print(f"\nContext selected: {len(context_results)} / {len(retrieved)} candidate(s)")
        print(f"Retrieval strategy: {retrieval_routing['strategy']}")
        if telemetry.get("llm_call_skipped"):
            print(f"Generation path: {telemetry['generation_path']} (SUT call skipped)")
        print("\nAssistant:")
        print(answer)
        print("\nTelemetry:")
        print(telemetry)
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
