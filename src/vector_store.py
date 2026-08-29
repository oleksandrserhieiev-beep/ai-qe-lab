import os

from context_builder import build_context, PROMPT_VERSION
from context_logger import log_context
from context_selector import select_context_results
from retrieval_logger import log_retrieval
from llm_client import generate_answer
from llm_logger import log_llm_call

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from data_loader import load_products, load_policies
from constraint_filter import (
    extract_constraints,
    product_matches_constraints,
)


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))


def product_to_text(product):
    return (
        f"Product ID: {product['product_id']}. "
        f"Name: {product['name']}. "
        f"Category: {product['category']}. "
        f"Subcategory: {product['subcategory']}. "
        f"Price: {product['price']} {product['currency']}. "
        f"Colors: {', '.join(product['colors'])}. "
        f"Sizes: {', '.join(product['sizes'])}. "
        f"Waterproof: {product['waterproof']}. "
        f"Stock: {product['stock']}. "
        f"Rating: {product['rating']}. "
        f"Description: {product['description']}"
    )


def build_documents():
    documents = []

    products = load_products()
    policies = load_policies()

    for product in products:
        documents.append(
            {
                "id": product["product_id"],
                "type": "product",
                "text": product_to_text(product),
                "metadata": product,
            }
        )

    for policy in policies:
        documents.append(
            {
                "id": policy["document_id"],
                "type": "policy",
                "text": policy["content"],
                "metadata": policy,
            }
        )

    return documents


def build_vector_store(documents):
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [doc["text"] for doc in documents]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(
        embeddings.astype(np.float32)
    )

    return model, index


def semantic_search(query, model, documents, top_k=DEFAULT_TOP_K):
    if not documents:
        return []

    texts = [document["text"] for document in documents]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    dimension = embeddings.shape[1]
    temp_index = faiss.IndexFlatIP(dimension)
    temp_index.add(embeddings.astype(np.float32))

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    result_count = min(top_k, len(documents))

    scores, indices = temp_index.search(
        query_embedding.astype(np.float32),
        result_count,
    )

    results = []

    for rank, (score, idx) in enumerate(
        zip(scores[0], indices[0]),
        start=1,
    ):
        document = documents[idx]

        results.append(
            {
                "rank": rank,
                "score": float(score),
                "id": document["id"],
                "type": document["type"],
                "text": document["text"],
                "metadata": document["metadata"],
            }
        )

    return results


def search(query, model, index, documents, top_k=DEFAULT_TOP_K):
    """Return ranked retrieval candidates before adaptive context selection."""
    constraints = extract_constraints(query)

    has_product_constraints = any(
        value is not None
        for value in constraints.values()
    )

    if has_product_constraints:
        filtered_products = []

        for document in documents:
            if document["type"] != "product":
                continue

            product = document["metadata"]

            if product_matches_constraints(product, constraints):
                filtered_products.append(document)

        if filtered_products:
            print(
                f"Structured filter matched: "
                f"{len(filtered_products)} product(s)"
            )

            return semantic_search(
                query=query,
                model=model,
                documents=filtered_products,
                top_k=top_k,
            )

    # Fallback when no structured constraints were detected or no product matched.
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    result_count = min(top_k, len(documents))
    scores, indices = index.search(
        query_embedding.astype(np.float32),
        result_count,
    )

    results = []

    for rank, (score, idx) in enumerate(
        zip(scores[0], indices[0]),
        start=1,
    ):
        document = documents[idx]

        results.append(
            {
                "rank": rank,
                "score": float(score),
                "id": document["id"],
                "type": document["type"],
                "text": document["text"],
                "metadata": document["metadata"],
            }
        )

    return results


if __name__ == "__main__":
    # 1. Load product catalogue and approved policies.
    documents = build_documents()
    print(f"Documents loaded: {len(documents)}")

    # 2. Build embeddings and FAISS vector index.
    model, index = build_vector_store(documents)

    # 3. Test query.
    query = "Find me a waterproof black jacket under $150 in size L"

    # 4. Retrieve ranked Top-K candidates.
    retrieved = search(
        query=query,
        model=model,
        index=index,
        documents=documents,
        top_k=DEFAULT_TOP_K,
    )

    # 5. Apply adaptive context selection.
    context_results = select_context_results(retrieved)

    # 6. Log retrieval candidates.
    log_retrieval(
        query=query,
        results=retrieved,
    )

    # 7. Build augmented RAG context from selected evidence only.
    final_context = build_context(
        query=query,
        results=context_results,
    )

    # 8. Log exact context supplied to LLM.
    log_context(
        query=query,
        final_context=final_context,
        prompt_version=PROMPT_VERSION,
    )

    # 9. Call Claude.
    answer, telemetry = generate_answer(final_context)

    # 10. Log LLM call.
    log_llm_call(
        query=query,
        answer=answer,
        telemetry=telemetry,
        prompt_version=PROMPT_VERSION,
    )

    # 11. Print retrieval candidates and selection size.
    print(f"\nQuery: {query}\n")

    for result in retrieved:
        print(
            f"Rank: {result['rank']} | "
            f"ID: {result['id']} | "
            f"Type: {result['type']} | "
            f"Score: {result['score']:.4f}"
        )

    print(
        f"\nAdaptive context selected: "
        f"{len(context_results)} / {len(retrieved)} candidate(s)"
    )

    # 12. Print context.
    print("\nFINAL CONTEXT:\n")
    print(final_context)

    # 13. Print answer and telemetry.
    print("\nCLAUDE ANSWER:\n")
    print(answer)

    print("\nLLM TELEMETRY:\n")
    print(telemetry)
