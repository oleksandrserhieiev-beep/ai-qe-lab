import os


DEFAULT_MIN_CONTEXT_K = 2
DEFAULT_MAX_CONTEXT_K = 5
DEFAULT_MIN_SIMILARITY = 0.30


def _env_int(name, default):
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _env_float(name, default):
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def get_context_selection_config():
    min_k = _env_int("RAG_MIN_CONTEXT_K", DEFAULT_MIN_CONTEXT_K)
    max_k = _env_int("RAG_MAX_CONTEXT_K", DEFAULT_MAX_CONTEXT_K)
    min_similarity = _env_float("RAG_MIN_SIMILARITY", DEFAULT_MIN_SIMILARITY)

    if min_k < 1:
        raise ValueError("RAG_MIN_CONTEXT_K must be >= 1")
    if max_k < min_k:
        raise ValueError("RAG_MAX_CONTEXT_K must be >= RAG_MIN_CONTEXT_K")
    if not -1.0 <= min_similarity <= 1.0:
        raise ValueError("RAG_MIN_SIMILARITY must be between -1.0 and 1.0")

    return {
        "min_k": min_k,
        "max_k": max_k,
        "min_similarity": min_similarity,
    }


def select_context_results(retrieved, min_k=None, max_k=None, min_similarity=None):
    """Select a dynamic context subset from ranked retrieval candidates.

    Similarity threshold is authoritative: low-confidence documents are never
    added only to satisfy min_k. min_k is therefore a target floor when enough
    qualifying evidence exists, not a reason to inject weak evidence.
    """
    config = get_context_selection_config()
    min_k = config["min_k"] if min_k is None else min_k
    max_k = config["max_k"] if max_k is None else max_k
    min_similarity = config["min_similarity"] if min_similarity is None else min_similarity

    if min_k < 1:
        raise ValueError("min_k must be >= 1")
    if max_k < min_k:
        raise ValueError("max_k must be >= min_k")

    candidates = list(retrieved or [])[:max_k]
    selected = [
        item for item in candidates
        if float(item.get("score", -1.0)) >= min_similarity
    ]

    return selected[:max_k]


def build_context_selection_metadata(retrieved, selected, config=None):
    config = config or get_context_selection_config()
    candidates = list(retrieved or [])
    selected = list(selected or [])

    selected_ids = [item.get("id") for item in selected]
    selected_id_set = set(selected_ids)
    dropped = [item for item in candidates if item.get("id") not in selected_id_set]

    candidate_k = len(candidates)
    selected_k = len(selected)
    reduction_pct = (
        ((candidate_k - selected_k) / candidate_k) * 100.0
        if candidate_k
        else 0.0
    )

    return {
        "candidate_k": candidate_k,
        "selected_k": selected_k,
        "context_reduction_pct": round(reduction_pct, 2),
        "target_min_k": config["min_k"],
        "max_k": config["max_k"],
        "min_similarity": config["min_similarity"],
        "candidate_ids": [item.get("id") for item in candidates],
        "candidate_scores": [float(item.get("score", 0.0)) for item in candidates],
        "selected_ids": selected_ids,
        "selected_scores": [float(item.get("score", 0.0)) for item in selected],
        "dropped_ids": [item.get("id") for item in dropped],
        "dropped_scores": [float(item.get("score", 0.0)) for item in dropped],
    }
