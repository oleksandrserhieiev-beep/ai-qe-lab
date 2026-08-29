import argparse
import json
from pathlib import Path

from vector_store import DEFAULT_TOP_K, build_documents, build_vector_store, search_with_metadata
from context_builder import build_context, build_retrieved_context, PROMPT_VERSION
from context_selector import build_context_selection_metadata, get_context_selection_config, select_context_results
from generation_policy import generate_grounded_answer

BASE_DIR = Path(__file__).resolve().parent.parent
POLICIES_DIR = BASE_DIR / "policies"
NIGHTLY_RISK_METADATA = BASE_DIR / "datasets" / "evaluation_risk_metadata.json"
NIGHTLY_ASSERTION_METADATA = BASE_DIR / "datasets" / "evaluation_assertion_metadata.json"

SEGMENT_ORACLE = {
    "normal": "deterministic",
    "ambiguous": "semantic_llm",
    "negative": "deterministic",
    "multi_constraint": "deterministic",
    "out_of_domain": "semantic_llm",
    "missing_info": "semantic_llm",
    "conflict": "deterministic",
    "adversarial": "semantic_llm",
    "paraphrase": "deterministic",
    "long_query": "deterministic",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run AI/RAG evaluation against a dataset.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _sidecar(dataset_file, path):
    if dataset_file.name != "evaluation_dataset.json":
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_case_documents(base_documents, fixture_files):
    documents = list(base_documents)
    existing = {item.get("id") for item in documents}
    for filename in fixture_files or []:
        if filename in existing:
            continue
        path = POLICIES_DIR / filename
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        documents.append({"id": filename, "type": "policy", "text": content, "metadata": {"document_id": filename, "source": str(path), "content": content, "test_fixture": True}})
    return documents


def run_evaluation(dataset_file, results_file, top_k=DEFAULT_TOP_K):
    dataset = load_dataset(dataset_file)
    risk_metadata = _sidecar(dataset_file, NIGHTLY_RISK_METADATA)
    assertion_metadata = _sidecar(dataset_file, NIGHTLY_ASSERTION_METADATA)
    selection_config = get_context_selection_config()
    print(f"Dataset: {dataset_file}")
    print(f"Cases loaded: {len(dataset)}")
    print(f"Adaptive context selection: retrieval_k={top_k}, target_min_k={selection_config['min_k']}, max_k={selection_config['max_k']}, min_similarity={selection_config['min_similarity']:.2f}")
    print("Initializing RAG...")

    base_documents = build_documents()
    base_model, base_index = build_vector_store(base_documents)
    fixture_rag_cache = {}
    results = []

    for number, case in enumerate(dataset, start=1):
        case_id = case.get("ID")
        query = case.get("Query")
        if not query:
            print(f"Skipping {case_id}: no query")
            continue
        print(f"\n[{number}/{len(dataset)}] Running {case_id}")

        fixture_files = tuple(case.get("Context Fixtures", []) or [])
        if fixture_files:
            if fixture_files not in fixture_rag_cache:
                docs = build_case_documents(base_documents, fixture_files)
                fixture_rag_cache[fixture_files] = (docs, *build_vector_store(docs))
            documents, model, index = fixture_rag_cache[fixture_files]
            print(f"Case-scoped context fixtures: {', '.join(fixture_files)}")
        else:
            documents, model, index = base_documents, base_model, base_index

        retrieved, retrieval_routing = search_with_metadata(query, model, index, documents, top_k)
        context_results = select_context_results(retrieved)
        selection_metadata = build_context_selection_metadata(retrieved, context_results, selection_config)
        evidence = build_retrieved_context(context_results)
        final_context = build_context(query=query, results=context_results)
        answer, telemetry = generate_grounded_answer(final_context, context_results, retrieval_metadata=retrieval_routing)

        segment = str(case.get("Segment") or "").strip().lower()
        explicit_risk = case.get("Risk") if case.get("Risk") is not None else risk_metadata.get(case_id)
        explicit_oracle = case.get("Oracle") or SEGMENT_ORACLE.get(segment)
        deterministic_assertions = case.get("Deterministic Assertions")
        if deterministic_assertions is None:
            deterministic_assertions = assertion_metadata.get(case_id, [])

        results.append({
            "case_id": case_id, "oracle": explicit_oracle, "deterministic_assertions": deterministic_assertions,
            "intent": case.get("Intent"), "query": query, "expected_product": case.get("Expected Product"),
            "expected_retrieved_product": case.get("Expected Retrieved Product"),
            "expected_facts_behavior": case.get("Expected Facts/Behavior", case.get("Expected Behavior")),
            "expected_source": case.get("Expected Source"), "expected_context_sources": case.get("Expected Context Sources", []),
            "context_fixtures": list(fixture_files), "criticality": case.get("Criticality"), "why_golden": case.get("Why Golden"),
            "risk": explicit_risk, "segment": segment, "actual_answer": answer, "retrieved_context": evidence,
            "final_context": final_context,
            "retrieval": [{"id": item["id"], "type": item["type"], "rank": item["rank"], "similarity_score": item["score"], "metadata": item.get("metadata", {})} for item in retrieved],
            "retrieval_strategy": retrieval_routing["strategy"],
            "retrieval_routing": retrieval_routing, "context_selection": selection_metadata, "prompt_version": PROMPT_VERSION,
            "top_k": top_k, "context_k": len(context_results), "telemetry": telemetry,
        })
        print(f"Context-K selected: {len(context_results)} / {len(retrieved)} candidate(s)")
        print(f"Retrieval strategy: {retrieval_routing['strategy']}")
        if telemetry.get("llm_call_skipped"):
            print(f"Generation path: {telemetry['generation_path']} (SUT call skipped)")
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
