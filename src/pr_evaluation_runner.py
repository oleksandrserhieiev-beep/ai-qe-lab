import json
from pathlib import Path

from vector_store import build_documents, build_vector_store, search
from context_builder import build_context, build_retrieved_context, PROMPT_VERSION
from llm_client import generate_answer


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_FILE = BASE_DIR / "datasets" / "pr_critical_dataset.json"
RESULTS_FILE = BASE_DIR / "reports" / "pr_results.json"
RETRIEVAL_K = 5
DEFAULT_CONTEXT_K = 3


def load_dataset():
    with open(DATASET_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def select_context_results(retrieved):
    if len(retrieved) <= 1:
        return retrieved
    return retrieved[:DEFAULT_CONTEXT_K]


def run_evaluation():
    dataset = load_dataset()
    print(f"Critical cases loaded: {len(dataset)}")
    print(f"Retrieval-K: {RETRIEVAL_K}; max Context-K: {DEFAULT_CONTEXT_K}")
    print("Initializing RAG...")

    documents = build_documents()
    model, index = build_vector_store(documents)
    results = []

    for number, case in enumerate(dataset, start=1):
        case_id = case.get("ID")
        query = case.get("Query")
        if not query:
            print(f"Skipping {case_id}: no query")
            continue

        print(f"\n[{number}/{len(dataset)}] Running {case_id}")
        print(f"Query: {query}")

        retrieved = search(query=query, model=model, index=index, documents=documents, top_k=RETRIEVAL_K)
        context_results = select_context_results(retrieved)
        retrieved_context = build_retrieved_context(context_results)
        final_context = build_context(query=query, results=context_results)
        answer, telemetry = generate_answer(final_context)

        result = {
            "case_id": case_id,
            "oracle": case.get("Oracle"),
            "deterministic_assertions": case.get("Deterministic Assertions", []),
            "intent": case.get("Intent"),
            "query": query,
            "expected_product": case.get("Expected Product"),
            "expected_retrieved_product": case.get("Expected Retrieved Product"),
            "expected_facts_behavior": case.get("Expected Facts/Behavior"),
            "expected_source": case.get("Expected Source"),
            "criticality": case.get("Criticality"),
            "risk": case.get("Risk"),
            "why_golden": case.get("Why Golden"),
            "actual_answer": answer,
            "final_context": final_context,
            "retrieved_context": retrieved_context,
            "retrieval": [
                {
                    "id": item["id"],
                    "type": item["type"],
                    "rank": item["rank"],
                    "similarity_score": item["score"],
                    "metadata": item.get("metadata", {}),
                }
                for item in retrieved
            ],
            "prompt_version": PROMPT_VERSION,
            "retrieval_k": RETRIEVAL_K,
            "context_k": len(context_results),
            "telemetry": telemetry,
        }
        results.append(result)
        print(f"Context-K used: {len(context_results)}")
        print("Answer:")
        print(answer)

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("\nEvaluation complete.")
    print(f"Executed cases: {len(results)}")
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    run_evaluation()
