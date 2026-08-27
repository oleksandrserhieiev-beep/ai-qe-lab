import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "llm.jsonl"


def log_llm_call(query, answer, telemetry, prompt_version):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "prompt_version": prompt_version,
        "model": telemetry["model"],
        "input_tokens": telemetry["input_tokens"],
        "output_tokens": telemetry["output_tokens"],
        "latency_ms": telemetry["latency_ms"],
        "stop_reason": telemetry["stop_reason"],
        "answer": answer,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")