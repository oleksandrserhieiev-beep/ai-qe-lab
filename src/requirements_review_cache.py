import hashlib
import json
import os
from pathlib import Path

CACHE_VERSION = 1
DEFAULT_CACHE_PATH = Path(".cache/requirements-review/cache.json")


def build_review_payload(requirement: dict) -> dict:
    """Keep only fields that can materially affect semantic requirements quality review."""
    return {
        "issue_key": requirement.get("issue_key"),
        "summary": requirement.get("summary") or "",
        "description": requirement.get("description") or "",
        "acceptance_criteria": requirement.get("acceptance_criteria") or "",
        "issue_type": requirement.get("issue_type"),
        "parent_key": requirement.get("parent_key"),
    }


def content_hash(review_payload: dict, *, model: str, prompt_text: str) -> str:
    """Fingerprint semantic input plus review configuration so prompt/model changes invalidate cache."""
    material = {
        "cache_version": CACHE_VERSION,
        "model": model,
        "prompt": prompt_text,
        "requirement": review_payload,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_path() -> Path:
    configured = (os.getenv("REQUIREMENTS_REVIEW_CACHE_PATH") or "").strip()
    return Path(configured) if configured else DEFAULT_CACHE_PATH


def load_cache(path: Path | None = None) -> dict:
    path = path or cache_path()
    if not path.exists():
        return {"version": CACHE_VERSION, "issues": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": CACHE_VERSION, "issues": {}}
    if payload.get("version") != CACHE_VERSION or not isinstance(payload.get("issues"), dict):
        return {"version": CACHE_VERSION, "issues": {}}
    return payload


def save_cache(cache: dict, path: Path | None = None):
    path = path or cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_cached_review(cache: dict, issue_key: str, fingerprint: str) -> dict | None:
    entry = (cache.get("issues") or {}).get(issue_key)
    if not entry or entry.get("content_hash") != fingerprint:
        return None
    return entry


def put_cached_review(
    cache: dict,
    issue_key: str,
    fingerprint: str,
    *,
    review: dict,
    model: str,
    reviewed_at: str,
):
    cache.setdefault("issues", {})[issue_key] = {
        "content_hash": fingerprint,
        "reviewed_at": reviewed_at,
        "model": model,
        "review": review,
    }
