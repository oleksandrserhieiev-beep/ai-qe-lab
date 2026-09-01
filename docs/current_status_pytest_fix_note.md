# Risk Analysis Agent workflow pytest fix

The Risk Analysis Agent Evaluation workflow requires test tooling in addition to runtime dependencies. `pytest` is now pinned in `requirements-dev.txt`, and workflows that execute Risk Agent contract tests install that development manifest before running `python -m pytest`.
