import argparse
import json
from pathlib import Path

from vector_store import build_documents, build_vector_store, search
from context_builder import build_context, build_retrieved_context, PROMPT_VERSION
from llm_client import generate_answer


BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Run AI/RAG evaluation against a dataset.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


def load_dataset(dataset_file):
    with open(dataset_file, "r", encoding="utf-8") as file:
        return json.load(file)


def run_evaluation(dataset_file, results_file, top_k=5):
    dataset = load_dataset(dataset_file)
    print(f"Dataset: {dataset_file}")
    print(f"Cases loaded: {len(dataset)}")
    print(f"Top-K: {top_k}")
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
        retrieved = search(query=query, model=model, index=index, documents=documents, top_k=top_k)
        evidence = build_retrieved_context(retrieved)
        final_context = build_context(query=query, results=retrieved)
        answer, telemetry = generate_answer(final_context)

        results.append({
            "case_id": case_id,
            "intent": case.get("Intent"),
            "query": query,
            "expected_product": case.get("Expected Product"),
            "expected_retrieved_product": case.get("Expected Retrieved Product"),
            "expected_facts_behavior": case.get("Expected Facts/Behavior", case.get("Expected Behavior")),
            "expected_source": case.get("Expected Source"),
            "criticality": case.get("Criticality"),
            "why_golden": case.get("Why Golden"),
            "risk": case.get("Risk") or case.get("Segment"),
            "actual_answer": answer,
            "retrieved_context": evidence,
            "final_context": final_context,
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
            "top_k": top_k,
            "telemetry": telemetry,
        })
        print("Answer:")
        print(answer)

    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("\nEvaluation complete.")
    print(f"Executed cases: {len(results)}")
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    args = parse_args()
    run_evaluation(resolve_path(args.dataset), resolve_path(args.output), args.top_k)
