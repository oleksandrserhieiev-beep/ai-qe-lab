# CI test dependencies

Test-only Python dependencies are declared in `requirements-dev.txt`.

GitHub Actions jobs that execute `pytest` should install `requirements-dev.txt`, which includes the runtime dependencies from `requirements.txt` plus the pinned test runner.

This keeps runtime dependencies separate from CI/test tooling while preventing workflows from assuming `pytest` is preinstalled on the runner.
