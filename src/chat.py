from vector_store import (
    build_documents,
    build_vector_store,
    search,
)
from context_builder import build_context, PROMPT_VERSION
from retrieval_logger import log_retrieval
from context_logger import log_context
from llm_client import generate_answer
from llm_logger import log_llm_call


def main():
    print("Initializing Shopping AI Assistant...")

    documents = build_documents()
    model, index = build_vector_store(documents)

    print("Ready.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Bye.")
            break

        if not query:
            continue

        results = search(
            query=query,
            model=model,
            index=index,
            documents=documents,
            top_k=5,
        )

        log_retrieval(
            query=query,
            results=results,
        )

        final_context = build_context(
            query=query,
            results=results,
        )

        log_context(
            query=query,
            final_context=final_context,
            prompt_version=PROMPT_VERSION,
        )

        answer, telemetry = generate_answer(
            final_context
        )

        log_llm_call(
            query=query,
            answer=answer,
            telemetry=telemetry,
            prompt_version=PROMPT_VERSION,
        )

        print("\nAssistant:")
        print(answer)

        print("\nTelemetry:")
        print(telemetry)

        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()