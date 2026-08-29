from pathlib import Path

from evaluator import run_evaluator


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_FILE = BASE_DIR / "reports" / "pr_results.json"
EVALUATED_FILE = BASE_DIR / "reports" / "pr_evaluated.json"


if __name__ == "__main__":
    run_evaluator(RESULTS_FILE, EVALUATED_FILE)
