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

DATASET_FILE = BASE_DIR / "datasets" / "evaluation_dataset.json"
RESULTS_FILE = BASE_DIR / "reports" / "evaluation_results.json"


def load_dataset():
    with open(DATASET_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def run_evaluation():
    dataset = load_dataset()

    print(f"Evaluation cases loaded: {len(dataset)}")
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
        print(f"Segment: {case.get('Segment')}")
        print(f"Query: {query}")

        # 1. Retrieval
        retrieved = search(
            query=query,
            model=model,
            index=index,
            documents=documents,
            top_k=5,
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

        # 4. Store case-level evidence
        result = {
            "case_id": case_id,
            "segment": case.get("Segment"),
            "query": query,

            "expected_behavior": case.get(
                "Expected Behavior"
            ),
            "expected_source": case.get(
                "Expected Source"
            ),
            "criticality": case.get(
                "Criticality"
            ),
            "design_note": case.get(
                "Design Note"
            ),

            "actual_answer": answer,
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
            "telemetry": telemetry,
        }

        results.append(result)

        print("Answer:")
        print(answer)

    RESULTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\nEvaluation Dataset run complete.")
    print(f"Executed cases: {len(results)}")
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    run_evaluation()