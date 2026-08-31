import argparse
import json
import re
from pathlib import Path

from vector_store import DEFAULT_TOP_K, build_documents, build_vector_store, search_with_metadata
from context_builder import build_context
from context_selector import get_context_selection_config, select_context_results
from generation_policy import generate_grounded_answer

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def _run_query(query, model, index, documents, top_k):
    retrieved, routing = search_with_metadata(query, model, index, documents, top_k)
    context_results = select_context_results(retrieved)
    final_context = build_context(query=query, results=context_results)
    answer, telemetry = generate_grounded_answer(final_context, context_results, retrieval_metadata=routing)
    return {
        "query": query,
        "answer": answer,
        "retrieved_ids": [item["id"] for item in retrieved],
        "context_ids": [item["id"] for item in context_results],
        "telemetry": telemetry,
    }


def _validate_relation(base, transformed, relation):
    relation_type = str(relation.get("type", "")).strip().lower()
    if relation_type == "same_regex":
        pattern = str(relation.get("pattern", ""))
        flags = re.IGNORECASE
        base_match = re.search(pattern, base["answer"], flags) if pattern else None
        transformed_match = re.search(pattern, transformed["answer"], flags) if pattern else None
        passed = bool(base_match and transformed_match)
        return {
            "type": relation_type,
            "passed": passed,
            "expected": pattern,
            "base_match": base_match.group(0) if base_match else None,
            "transformed_match": transformed_match.group(0) if transformed_match else None,
        }
    if relation_type == "retrieval_contains_same_id":
        expected_id = str(relation.get("value", ""))
        passed = expected_id in base["retrieved_ids"] and expected_id in transformed["retrieved_ids"]
        return {
            "type": relation_type,
            "passed": passed,
            "expected": expected_id,
            "base_retrieved": base["retrieved_ids"],
            "transformed_retrieved": transformed["retrieved_ids"],
        }
    return {"type": relation_type, "passed": False, "reason": "unsupported metamorphic relation"}


def main():
    parser = argparse.ArgumentParser(description="Run deterministic metamorphic relations from an AI QE dataset.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()

    dataset_path = resolve_path(args.dataset)
    output_path = resolve_path(args.output)
    with dataset_path.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)

    cases = [case for case in dataset if str(case.get("Type", "")).lower() == "metamorphic"]
    print(f"Metamorphic cases loaded: {len(cases)}")

    documents = build_documents()
    model, index = build_vector_store(documents)
    get_context_selection_config()
    results = []

    for case in cases:
        case_id = case["ID"]
        base_query = case["Query"]
        transformed_query = case["Transformed Query"]
        print(f"\nRunning {case_id}: base + transformed invocation")
        base = _run_query(base_query, model, index, documents, args.top_k)
        transformed = _run_query(transformed_query, model, index, documents, args.top_k)
        relation = _validate_relation(base, transformed, case.get("Metamorphic Relation", {}))
        results.append({
            "case_id": case_id,
            "criticality": case.get("Criticality"),
            "risk": case.get("Risk", []),
            "transformation": case.get("Transformation"),
            "base": base,
            "transformed": transformed,
            "relation": relation,
            "overall_pass": bool(relation.get("passed")),
        })
        print(f"Relation: {relation.get('type')} -> {'PASS' if relation.get('passed') else 'FAIL'}")

    summary = {
        "total": len(results),
        "passed": sum(item["overall_pass"] for item in results),
        "failed": sum(not item["overall_pass"] for item in results),
        "pass_rate": round(100.0 * sum(item["overall_pass"] for item in results) / len(results), 2) if results else None,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "cases": results}, handle, ensure_ascii=False, indent=2)
    print(f"\nMetamorphic summary: {summary}")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
