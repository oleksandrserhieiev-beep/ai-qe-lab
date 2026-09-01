import hashlib
import json
from pathlib import Path

CACHE_VERSION = 1


def fingerprint(*, agent: str, semantic_input: dict, model: str, prompt_text: str) -> str:
    """Hash only material that can change an agent's semantic result."""
    material = {
        "cache_version": CACHE_VERSION,
        "agent": agent,
        "model": model,
        "prompt": prompt_text,
        "semantic_input": semantic_input,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_cache(path: Path) -> dict:
    if not path.exists():
        return {"version": CACHE_VERSION, "entries": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": CACHE_VERSION, "entries": {}}
    if payload.get("version") != CACHE_VERSION or not isinstance(payload.get("entries"), dict):
        return {"version": CACHE_VERSION, "entries": {}}
    return payload


def save_cache(cache: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_cached(cache: dict, key: str, content_hash: str) -> dict | None:
    entry = (cache.get("entries") or {}).get(key)
    if not entry or entry.get("content_hash") != content_hash:
        return None
    return entry


def put_cached(cache: dict, key: str, content_hash: str, *, result: dict, model: str, created_at: str) -> None:
    cache.setdefault("entries", {})[key] = {
        "content_hash": content_hash,
        "model": model,
        "created_at": created_at,
        "result": result,
    }
