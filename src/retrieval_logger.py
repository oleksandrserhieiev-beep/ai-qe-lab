import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "retrieval.jsonl"


def log_retrieval(query, results):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "results": [
            {
                "id": result["id"],
                "type": result["type"],
                "rank": result["rank"],
                "similarity_score": result["score"],
            }
            for result in results
        ],
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")