import os
import re

from context_builder import build_context, PROMPT_VERSION
from context_logger import log_context
from context_selector import select_context_results
from retrieval_logger import log_retrieval
from generation_policy import generate_grounded_answer
from llm_logger import log_llm_call

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from data_loader import load_products, load_policies
from constraint_filter import extract_constraints, product_matches_constraints
from constraint_validator import validate_constraints


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
CHEAPEST_PATTERN = re.compile(r"\b(?:cheapest|least expensive|lowest[- ]priced?)\b", re.IGNORECASE)


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
        documents.append({"id": product["product_id"], "type": "product", "text": product_to_text(product), "metadata": product})
    for policy in policies:
        documents.append({"id": policy["document_id"], "type": "policy", "text": policy["content"], "metadata": policy})
    return documents


def build_vector_store(documents):
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [doc["text"] for doc in documents]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype(np.float32))
    return model, index


def semantic_search(query, model, documents, top_k=DEFAULT_TOP_K):
    if not documents:
        return []
    texts = [document["text"] for document in documents]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    temp_index = faiss.IndexFlatIP(embeddings.shape[1])
    temp_index.add(embeddings.astype(np.float32))
    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    result_count = min(top_k, len(documents))
    scores, indices = temp_index.search(query_embedding.astype(np.float32), result_count)
    return [
        {"rank": rank, "score": float(score), "id": documents[idx]["id"], "type": documents[idx]["type"], "text": documents[idx]["text"], "metadata": documents[idx]["metadata"]}
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1)
    ]


def _rank_documents_deterministically(documents):
    return [
        {"rank": rank, "score": 1.0, "id": document["id"], "type": document["type"], "text": document["text"], "metadata": document["metadata"]}
        for rank, document in enumerate(documents, start=1)
    ]


def _cheapest_products(product_documents):
    priced = [document for document in product_documents if document.get("metadata", {}).get("price") is not None]
    if not priced:
        return []
    minimum_price = min(float(document["metadata"]["price"]) for document in priced)
    return [document for document in priced if float(document["metadata"]["price"]) == minimum_price]


def search_with_metadata(query, model, index, documents, top_k=DEFAULT_TOP_K):
    """Return ranked candidates plus deterministic input/retrieval routing evidence."""
    constraints = extract_constraints(query)
    validation = validate_constraints(query, constraints)
    cheapest_requested = bool(CHEAPEST_PATTERN.search(query or ""))

    if not validation["is_resolved"]:
        return [], {
            "strategy": "clarification_required",
            "structured_constraints_detected": any(value is not None for value in constraints.values()),
            "structured_match_count": None,
            "no_product_match": False,
            "cheapest_requested": cheapest_requested,
            "clarification_required": True,
            "constraint_validation": validation,
        }

    has_product_constraints = any(value is not None for value in constraints.values())
    product_documents = [document for document in documents if document["type"] == "product"]
    candidate_products = product_documents

    if has_product_constraints:
        candidate_products = [document for document in product_documents if product_matches_constraints(document["metadata"], constraints)]
        if not candidate_products:
            print("Structured filter matched: 0 product(s) — deterministic no-match path")
            return [], {
                "strategy": "structured_no_match", "structured_constraints_detected": True,
                "structured_match_count": 0, "no_product_match": True,
                "cheapest_requested": cheapest_requested, "clarification_required": False,
                "constraint_validation": validation,
            }
        print(f"Structured filter matched: {len(candidate_products)} product(s)")

    if cheapest_requested:
        cheapest = _cheapest_products(candidate_products)
        return _rank_documents_deterministically(cheapest[:top_k]), {
            "strategy": "catalogue_min_price", "structured_constraints_detected": has_product_constraints,
            "structured_match_count": len(candidate_products) if has_product_constraints else None,
            "no_product_match": False, "cheapest_requested": True, "clarification_required": False,
            "constraint_validation": validation,
        }

    if has_product_constraints:
        return semantic_search(query, model, candidate_products, top_k), {
            "strategy": "structured_filter_then_semantic", "structured_constraints_detected": True,
            "structured_match_count": len(candidate_products), "no_product_match": False,
            "cheapest_requested": False, "clarification_required": False,
            "constraint_validation": validation,
        }

    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    result_count = min(top_k, len(documents))
    scores, indices = index.search(query_embedding.astype(np.float32), result_count)
    results = [
        {"rank": rank, "score": float(score), "id": documents[idx]["id"], "type": documents[idx]["type"], "text": documents[idx]["text"], "metadata": documents[idx]["metadata"]}
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1)
    ]
    return results, {
        "strategy": "semantic_faiss", "structured_constraints_detected": False,
        "structured_match_count": None, "no_product_match": False,
        "cheapest_requested": False, "clarification_required": False,
        "constraint_validation": validation,
    }


def search(query, model, index, documents, top_k=DEFAULT_TOP_K):
    results, _ = search_with_metadata(query=query, model=model, index=index, documents=documents, top_k=top_k)
    return results


if __name__ == "__main__":
    documents = build_documents()
    model, index = build_vector_store(documents)
    query = "Find me a waterproof black jacket under $150 in size L"
    retrieved, retrieval_metadata = search_with_metadata(query, model, index, documents, DEFAULT_TOP_K)
    context_results = select_context_results(retrieved)
    log_retrieval(query=query, results=retrieved)
    final_context = build_context(query=query, results=context_results)
    log_context(query=query, final_context=final_context, prompt_version=PROMPT_VERSION)
    answer, telemetry = generate_grounded_answer(final_context, context_results, retrieval_metadata=retrieval_metadata)
    log_llm_call(query=query, answer=answer, telemetry=telemetry, prompt_version=PROMPT_VERSION)
    print(answer)
