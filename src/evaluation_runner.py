import argparse
import json
from pathlib import Path

from vector_store import (
    build_documents,
    build_vector_store,
    search,
)
from context_builder import build_context, PROMPT_VERSION
from llm_client import generate_answer


BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run AI/RAG evaluation against a dataset."
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to dataset JSON file.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to results JSON file.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of retrieved documents. Default: 5.",
    )

    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)

    if not path.is_absolute():
        path = BASE_DIR / path

    return path


def load_dataset(dataset_file):
    with open(
        dataset_file,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def run_evaluation(
    dataset_file,
    results_file,
    top_k=5,
):
    dataset = load_dataset(dataset_file)

    print(f"Dataset: {dataset_file}")
    print(f"Cases loaded: {len(dataset)}")
    print(f"Top-K: {top_k}")
    print("Initializing RAG...")

    documents = build_documents()
    model, index = build_vector_store(documents)

    results = []

    for number, case in enumerate(
        dataset,
        start=1,
    ):
        case_id = case.get("ID")
        query = case.get("Query")

        if not query:
            print(
                f"Skipping {case_id}: "
                "no query"
            )
            continue

        print(
            f"\n[{number}/{len(dataset)}] "
            f"Running {case_id}"
        )
        print(f"Query: {query}")

        # 1. Retrieval
        retrieved = search(
            query=query,
            model=model,
            index=index,
            documents=documents,
            top_k=top_k,
        )

        # 2. Augmentation
        final_context = build_context(
            query=query,
            results=retrieved,
        )

        # 3. Generation
        answer, telemetry = generate_answer(
            final_context
        )

        # 4. Save complete case-level evidence
        result = {
            "case_id": case_id,
            "intent": case.get("Intent"),
            "query": query,

            "expected_product": case.get(
                "Expected Product"
            ),

            "expected_retrieved_product": case.get(
                "Expected Retrieved Product"
            ),

            "expected_facts_behavior": case.get(
                "Expected Facts/Behavior"
            ),

            "expected_source": case.get(
                "Expected Source"
            ),

            "criticality": case.get(
                "Criticality"
            ),

            "why_golden": case.get(
                "Why Golden"
            ),

            "risk": case.get(
                "Risk"
            ),

            "actual_answer": answer,

            # Exact augmented context supplied to Claude.
            # Needed later for groundedness /
            # hallucination evaluation.
            "final_context": final_context,

            "retrieval": [
                {
                    "id": item["id"],
                    "type": item["type"],
                    "rank": item["rank"],
                    "similarity_score": item["score"],
                }
                for item in retrieved
            ],

            "prompt_version": PROMPT_VERSION,
            "top_k": top_k,
            "telemetry": telemetry,
        }

        results.append(result)

        print("Answer:")
        print(answer)

    # 5. Save all case-level results
    results_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        results_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\nEvaluation complete.")
    print(f"Executed cases: {len(results)}")
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    args = parse_args()

    dataset_file = resolve_path(
        args.dataset
    )

    results_file = resolve_path(
        args.output
    )

    run_evaluation(
        dataset_file=dataset_file,
        results_file=results_file,
        top_k=args.top_k,
    )