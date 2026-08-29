import argparse
import json
import re
from pathlib import Path

from context_selector import build_context_selection_metadata, select_context_results
from vector_store import DEFAULT_TOP_K, build_documents, build_vector_store, search


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40]
PRODUCT_ID_PATTERN = re.compile(r"\bP-\d+\b", re.IGNORECASE)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare adaptive context-selection thresholds without calling the LLM."
    )
    parser.add_argument(
        "--dataset",
        default="datasets/evaluation_dataset.json",
        help="Dataset used to generate retrieval candidates.",
    )
    parser.add_argument(
        "--output",
        default="reports/context_selection_baseline.json",
        help="JSON report path.",
    )
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=DEFAULT_THRESHOLDS,
        help="Similarity thresholds to compare.",
    )
    return parser.parse_args()


def resolve_path(path_value):
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def expected_product_ids(case):
    values = [
        case.get("Expected Product"),
        case.get("Expected Retrieved Product"),
        case.get("Expected Behavior"),
        case.get("Expected Facts/Behavior"),
    ]
    joined = " ".join(str(value) for value in values if value)
    return sorted({match.upper() for match in PRODUCT_ID_PATTERN.findall(joined)})


def run_baseline(dataset_path, output_path, top_k, thresholds):
    dataset = load_dataset(dataset_path)
    documents = build_documents()
    model, index = build_vector_store(documents)

    retrieval_by_case = {}
    for number, case in enumerate(dataset, start=1):
        case_id = case.get("ID")
        query = case.get("Query")
        if not query:
            continue

        print(f"[{number}/{len(dataset)}] Retrieving {case_id}")
        retrieval_by_case[case_id] = {
            "case": case,
            "retrieved": search(
                query=query,
                model=model,
                index=index,
                documents=documents,
                top_k=top_k,
            ),
        }

    threshold_reports = []

    for threshold in thresholds:
        cases = []
        total_candidates = 0
        total_selected = 0
        explicit_expected_retrieved = 0
        explicit_expected_selected = 0
        explicit_expected_dropped = 0
        selection_invariant_failures = 0

        config = {
            "min_k": 2,
            "max_k": top_k,
            "min_similarity": threshold,
        }

        for case_id, payload in retrieval_by_case.items():
            case = payload["case"]
            retrieved = payload["retrieved"]
            selected = select_context_results(
                retrieved,
                min_k=2,
                max_k=top_k,
                min_similarity=threshold,
            )
            metadata = build_context_selection_metadata(retrieved, selected, config)

            qualifying_ids = [
                item.get("id")
                for item in retrieved[:top_k]
                if float(item.get("score", -1.0)) >= threshold
            ]
            invariant_ok = metadata["selected_ids"] == qualifying_ids
            if not invariant_ok:
                selection_invariant_failures += 1

            expected_ids = expected_product_ids(case)
            retrieved_ids = set(metadata["candidate_ids"])
            selected_ids = set(metadata["selected_ids"])
            expected_retrieved_ids = [item for item in expected_ids if item in retrieved_ids]
            expected_selected_ids = [item for item in expected_ids if item in selected_ids]
            expected_dropped_ids = [
                item for item in expected_retrieved_ids if item not in selected_ids
            ]

            if expected_ids:
                explicit_expected_retrieved += int(bool(expected_retrieved_ids))
                explicit_expected_selected += int(bool(expected_selected_ids))
                explicit_expected_dropped += int(bool(expected_dropped_ids))

            total_candidates += metadata["candidate_k"]
            total_selected += metadata["selected_k"]

            cases.append({
                "case_id": case_id,
                "query": case.get("Query"),
                "expected_product_ids": expected_ids,
                "expected_retrieved_ids": expected_retrieved_ids,
                "expected_selected_ids": expected_selected_ids,
                "expected_dropped_ids": expected_dropped_ids,
                "selection_invariant_ok": invariant_ok,
                "context_selection": metadata,
            })

        case_count = len(cases)
        avg_candidate_k = total_candidates / case_count if case_count else 0.0
        avg_selected_k = total_selected / case_count if case_count else 0.0
        reduction_pct = (
            ((total_candidates - total_selected) / total_candidates) * 100.0
            if total_candidates
            else 0.0
        )

        threshold_reports.append({
            "threshold": threshold,
            "cases": case_count,
            "avg_candidate_k": round(avg_candidate_k, 2),
            "avg_selected_k": round(avg_selected_k, 2),
            "context_reduction_pct": round(reduction_pct, 2),
            "selection_invariant_failures": selection_invariant_failures,
            "explicit_expected_retrieved_cases": explicit_expected_retrieved,
            "explicit_expected_selected_cases": explicit_expected_selected,
            "explicit_expected_dropped_cases": explicit_expected_dropped,
            "case_details": cases,
        })

    report = {
        "dataset": str(dataset_path),
        "retrieval_k": top_k,
        "thresholds": thresholds,
        "note": (
            "This is a deterministic retrieval/context-selection baseline. "
            "It does not call the SUT or semantic Judge."
        ),
        "results": threshold_reports,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print("\nAdaptive Context Selection Baseline")
    print(f"Dataset cases: {len(retrieval_by_case)}")
    print(f"Retrieval-K: {top_k}")
    print()
    print("Threshold | Avg Context-K | Reduction | Expected dropped | Invariant failures")
    for result in threshold_reports:
        print(
            f"{result['threshold']:.2f}      | "
            f"{result['avg_selected_k']:.2f}          | "
            f"{result['context_reduction_pct']:.2f}%    | "
            f"{result['explicit_expected_dropped_cases']}                | "
            f"{result['selection_invariant_failures']}"
        )

    print(f"\nReport saved to: {output_path}")

    if any(item["selection_invariant_failures"] for item in threshold_reports):
        raise SystemExit("Context selection invariant failed for one or more cases.")


if __name__ == "__main__":
    args = parse_args()
    run_baseline(
        resolve_path(args.dataset),
        resolve_path(args.output),
        args.top_k,
        args.thresholds,
    )
