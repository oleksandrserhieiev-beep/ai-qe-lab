import argparse
import json
from pathlib import Path

from context_builder import build_context, build_retrieved_context, PROMPT_VERSION
from context_selector import build_context_selection_metadata, get_context_selection_config, select_context_results
from model_gateway import generate_with_model
from vector_store import DEFAULT_TOP_K, build_documents, build_vector_store, search_with_metadata

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET = BASE_DIR / "datasets" / "pr_critical_dataset.json"


def _run_model(model_name, dataset, documents, embedding_model, index, top_k):
    selection_config = get_context_selection_config()
    results = []
    for case in dataset:
        if str(case.get("Type", "")).lower() == "metamorphic":
            continue
        query = case.get("Query")
        if not query:
            continue
        retrieved, routing = search_with_metadata(query, embedding_model, index, documents, top_k)
        context_results = select_context_results(retrieved)
        final_context = build_context(query=query, results=context_results)
        answer, telemetry = generate_with_model(model_name, final_context)
        results.append({
            "case_id": case.get("ID"),
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
            "actual_answer": answer,
            "retrieved_context": build_retrieved_context(context_results),
            "final_context": final_context,
            "retrieval": [{"id": item["id"], "type": item["type"], "rank": item["rank"], "similarity_score": item["score"], "metadata": item.get("metadata", {})} for item in retrieved],
            "retrieval_strategy": routing["strategy"],
            "retrieval_routing": routing,
            "context_selection": build_context_selection_metadata(retrieved, context_results, selection_config),
            "prompt_version": PROMPT_VERSION,
            "top_k": top_k,
            "context_k": len(context_results),
            "telemetry": telemetry,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Run the PR Critical suite against two models for back-to-back evaluation.")
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-b", required=True)
    parser.add_argument("--output-dir", default="reports/back_to_back")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()

    with DATASET.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)
    documents = build_documents()
    embedding_model, index = build_vector_store(documents)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = BASE_DIR / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for label, model_name in (("a", args.model_a), ("b", args.model_b)):
        print(f"Running PR Critical suite with Model {label.upper()}: {model_name}")
        results = _run_model(model_name, dataset, documents, embedding_model, index, args.top_k)
        path = output_dir / f"model_{label}_raw.json"
        path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Model {label.upper()} raw report: {path}")


if __name__ == "__main__":
    main()
