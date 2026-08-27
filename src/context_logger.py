import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "context.jsonl"


def log_context(query, final_context, prompt_version):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "prompt_version": prompt_version,
        "final_context": final_context,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")