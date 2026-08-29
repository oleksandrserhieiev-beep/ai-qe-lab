# AI QE Lab — Quick Start

This guide gets the Shopping RAG Assistant and AI evaluation framework running locally on Windows.

## Prerequisites

- Git
- Python 3.12 (matches CI)
- Anthropic API key

Verify:

```powershell
git --version
python --version
```

## 1. Clone the repository

```powershell
git clone https://github.com/oleksandrserhieiev-beep/ai-qe-lab.git
cd ai-qe-lab
```

## 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation, use Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

The first run may download the sentence-transformers embedding model used by the RAG pipeline.

## 4. Configure the environment

Copy the provided template to a local `.env` file:

```powershell
Copy-Item config\.env.example .env
```

At minimum, replace:

```text
LLM_API_KEY=replace_me
```

with your own Anthropic API key.

The current RAG defaults are already present in the template:

```text
RAG_TOP_K=5
RAG_MIN_CONTEXT_K=2
RAG_MAX_CONTEXT_K=5
RAG_MIN_SIMILARITY=0.30
```

Do not commit `.env` or API keys.

## 5. Run the lab

Use the repository's current CLI/evaluation entry points for the suite you want to exercise. The standard execution path is:

```text
Dataset Validation
→ Shopping RAG SUT
→ Retrieval + Adaptive Context Selection
→ Claude generation
→ Deterministic assertions or Semantic Judge
→ Evaluation summary
→ Quality Gate
```

The CI workflows in `.github/workflows/` are the canonical executable examples for PR Critical, Regression and Nightly evaluation commands.

## 6. What a healthy evaluation looks like

A successful PR Critical run should report the measured population explicitly, for example:

```text
Total cases: 10
Passed: 10
Failed: 0
Overall Pass Rate: 100.0% (10/10)
Retrieval Hit Rate: 100.0% (10/10)
Correctness Rate: 100.0% (4/4 judged)
Groundedness Rate: 100.0% (4/4 judged)
Constraint Adherence Rate: 100.0% (10/10)
Hallucination Rate: 0.0% (0/4 hallucinated; 4 judged)
```

Exact quality results can change as datasets, prompts, models and retrieval configuration evolve. The important rule is that each metric reports its actual applicable population.

## 7. Where to go next

- `README.md` — project overview and current architecture
- `docs/architecture.md` — implemented architecture and failure localization
- `docs/test_strategy.md` — test strategy
- `docs/metric_contract.md` — metric definitions and denominators
- `docs/automated_ai_evaluation.md` — Oracle routing and evaluation architecture

## Troubleshooting

- **Missing API key:** verify `LLM_API_KEY` in `.env`.
- **Import/package errors:** confirm the virtual environment is active and rerun `pip install -r requirements.txt`.
- **Slow first run:** the embedding model may be downloading/caching locally.
- **Different behavior from CI:** use Python 3.12 and compare your environment/model configuration with the relevant GitHub Actions workflow.
