# AI QE Lab — Quick Start

This guide reproduces the AI QE Lab in two places:

1. **locally on Windows** for debugging and experiments;
2. **in GitHub** with the same GitHub Actions workflows used by the project.

The repository contains the code, datasets and workflow definitions. Local secrets and GitHub repository secrets/variables are intentionally not stored in Git.

## What you will have at the end

```text
Your GitHub repository
├─ .github/workflows/ai-evaluation.yml   -> PR Critical evaluation
├─ .github/workflows/ai-regression.yml   -> Regression on main + manual run
├─ .github/workflows/ai-nightly.yml      -> Nightly + manual run
├─ src/
├─ datasets/
└─ reports/                              -> generated at runtime

Your Windows machine
├─ cloned repository
├─ .venv
└─ .env                                  -> local Anthropic configuration
```

Both local execution and GitHub Actions run the same Python implementation.

---

## Prerequisites

Install:

- Git
- Python 3.12
- GitHub CLI (`gh`)
- an Anthropic API key
- a GitHub account

Verify:

```powershell
git --version
python --version
gh --version
```

Python should report `3.12.x` to match CI.

If GitHub CLI is not installed on Windows:

```powershell
winget install --id GitHub.cli
```

Close and reopen the terminal after installation if `gh` is not immediately available.

---

## 1. Authenticate with GitHub

```powershell
gh auth login
```

Choose GitHub.com and HTTPS when prompted, then complete browser authentication.

Verify:

```powershell
gh auth status
```

---

## 2. Get your own GitHub copy with Actions workflows

### Recommended: fork the lab

This gives you your own repository while preserving the code, datasets and `.github/workflows` files.

```powershell
gh repo fork oleksandrserhieiev-beep/ai-qe-lab --clone=true --remote=true
cd ai-qe-lab
```

Verify that the three workflows exist:

```powershell
Get-ChildItem .github\workflows
```

Expected files:

```text
ai-evaluation.yml
ai-regression.yml
ai-nightly.yml
```

If you are already a collaborator working directly in the original repository, clone it instead:

```powershell
git clone https://github.com/oleksandrserhieiev-beep/ai-qe-lab.git
cd ai-qe-lab
```

> Forks copy workflow files, but **GitHub Secrets and repository Variables are not copied**. Configure them in Step 7.

---

## 3. Create and activate the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

The first RAG run can download the `all-MiniLM-L6-v2` sentence-transformers model.

---

## 4. Configure local execution

Create `.env` from the repository template:

```powershell
Copy-Item config\.env.example .env
```

Open it:

```powershell
notepad .env
```

At minimum configure:

```text
LLM_PROVIDER=anthropic
LLM_API_KEY=<YOUR_ANTHROPIC_API_KEY>
SUT_MODEL=claude-sonnet-5
JUDGE_MODEL=claude-opus-5

RAG_TOP_K=5
RAG_MIN_CONTEXT_K=2
RAG_MAX_CONTEXT_K=5
RAG_MIN_SIMILARITY=0.30
```

Jira values in the template are not required for the current RAG evaluation pipelines.

Never commit `.env` or API keys.

Check that Git ignores it:

```powershell
git status
```

`.env` must not appear as a tracked change.

---

## 5. Reproduce PR Critical locally

This is the local equivalent of `.github/workflows/ai-evaluation.yml`.

Run the commands in this order:

```powershell
python src/dataset_validator.py datasets/pr_critical_dataset.json
python src/risk_coverage.py --output reports/risk_coverage.json
python src/pr_evaluation_runner.py
python src/pr_evaluator.py
python src/hallucination_retry.py
python src/quality_gate.py --report reports/pr_evaluated.json
```

The flow is:

```text
Validate PR Critical Dataset
-> Build AI Risk Coverage Matrix
-> Run Shopping RAG SUT
-> Evaluate deterministic/semantic Oracles
-> Apply Hallucination Retry Policy
-> Apply Quality Gate
```

A healthy run ends with the quality gate passing and creates reports under `reports/`.

Typical population-aware summary:

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

Exact scores can change as datasets, prompts, models and retrieval configuration evolve. The denominator must always represent the population actually measured.

---

## 6. Reproduce Regression and Nightly locally

### Regression

```powershell
python src/dataset_validator.py datasets/regression_dataset.json
python src/evaluation_runner.py --dataset datasets/regression_dataset.json --output reports/regression_results.json
python src/evaluator.py --input reports/regression_results.json --output reports/regression_evaluated.json
python src/quality_gate.py --report reports/regression_evaluated.json
```

### Nightly Evaluation

```powershell
python src/dataset_validator.py datasets/evaluation_dataset.json
python src/evaluation_runner.py --dataset datasets/evaluation_dataset.json --output reports/evaluation_results.json
python src/evaluator.py --input reports/evaluation_results.json --output reports/evaluation_evaluated.json
python src/quality_gate.py --report reports/evaluation_evaluated.json
```

These commands mirror the Python execution in `ai-regression.yml` and `ai-nightly.yml`.

---

## 7. Configure GitHub Actions for your fork/new repository

Your local `.env` is **not used by GitHub Actions**.

GitHub Actions reads:

```text
Secret:
LLM_API_KEY

Repository Variables:
SUT_MODEL
JUDGE_MODEL
```

From inside your cloned fork, set them with GitHub CLI.

### Set the Anthropic API key secret

Run:

```powershell
gh secret set LLM_API_KEY
```

Paste your Anthropic API key when prompted. The value is stored as a GitHub Actions secret, not committed to the repository.

### Set model variables

```powershell
gh variable set SUT_MODEL --body "claude-sonnet-5"
gh variable set JUDGE_MODEL --body "claude-opus-5"
```

Verify the names exist:

```powershell
gh secret list
gh variable list
```

Expected configuration:

```text
Secret:
LLM_API_KEY

Variables:
SUT_MODEL      claude-sonnet-5
JUDGE_MODEL    claude-opus-5
```

If GitHub shows an Actions enablement banner for a fork, open the repository **Actions** tab and enable workflows for that fork.

---

## 8. Verify GitHub Actions manually

All three workflows support manual execution with `workflow_dispatch`.

### PR Critical workflow

```powershell
gh workflow run ai-evaluation.yml
```

### Regression workflow

```powershell
gh workflow run ai-regression.yml
```

### Nightly workflow

```powershell
gh workflow run ai-nightly.yml
```

List runs:

```powershell
gh run list --limit 10
```

Watch the newest run:

```powershell
gh run watch
```

If `gh run watch` asks you to choose a run, select the workflow you just started.

---

## 9. Verify the real PR pipeline

Create a branch:

```powershell
git checkout -b test/verify-ai-qe-pipeline
```

The PR workflow is path-filtered. It runs automatically when a PR to `main` changes one of these areas:

```text
src/**
data/**
datasets/**
tests/**
.github/workflows/ai-evaluation.yml
requirements.txt
```

A docs-only PR intentionally does not trigger PR Critical evaluation.

After making a legitimate test/code change in one of the monitored paths:

```powershell
git add .
git commit -m "test: verify AI QE pipeline"
git push -u origin test/verify-ai-qe-pipeline
gh pr create --base main --fill
```

Then inspect the run:

```powershell
gh run list --limit 5
gh run watch
```

The PR Critical workflow should execute:

```text
Checkout
-> Python 3.12 + pip cache
-> Hugging Face model cache
-> Install dependencies
-> Validate PR Critical Dataset
-> Build AI Risk Coverage Matrix
-> Run PR Critical Dataset
-> Evaluate PR Critical Dataset
-> Hallucination Retry Policy
-> Quality Gate
-> Upload evaluation reports
```

---

## 10. Understand automatic GitHub execution

Once configured, no local machine is required for CI runs.

| Event | Workflow | Behavior |
|---|---|---|
| PR to `main` affecting monitored paths | `ai-evaluation.yml` | PR Critical evaluation |
| Push/merge to `main` | `ai-regression.yml` | Regression evaluation |
| Daily at `01:00 UTC` | `ai-nightly.yml` | Full Nightly evaluation |
| Manual dispatch | all three | On-demand execution |

GitHub runners use Python 3.12 and execute the same repository Python code that you can run locally.

---

## 11. Download GitHub evaluation reports

Each workflow uploads report artifacts.

List recent runs:

```powershell
gh run list --limit 10
```

Download artifacts from a run:

```powershell
gh run download <RUN_ID>
```

Replace `<RUN_ID>` with the run ID shown by `gh run list`.

---

## Final verification checklist

You have reproduced the project correctly when all of the following are true:

- repository exists under your GitHub account or you have collaborator access;
- `.github/workflows/ai-evaluation.yml` exists;
- `.github/workflows/ai-regression.yml` exists;
- `.github/workflows/ai-nightly.yml` exists;
- Python 3.12 virtual environment works locally;
- `.env` contains your local Anthropic configuration and is not committed;
- PR Critical runs locally;
- Regression runs locally;
- Nightly runs locally;
- GitHub Secret `LLM_API_KEY` exists;
- GitHub Variables `SUT_MODEL` and `JUDGE_MODEL` exist;
- manual GitHub workflow dispatch succeeds;
- PR Critical triggers on an eligible PR;
- Regression triggers after merge/push to `main`;
- Nightly is available on schedule and manually;
- workflow artifacts contain generated evaluation reports.

At that point you have the same core AI QE Lab execution model in both environments:

```text
LOCAL
Python scripts + .env
        |
        +---- same source code / datasets ----+
                                               |
GITHUB                                         v
GitHub Actions + Secret/Variables -> SUT -> Evaluation -> Quality Gate -> Reports
```

## Troubleshooting

- **`LLM_API_KEY` missing locally:** verify `.env`.
- **`LLM_API_KEY` missing in Actions:** run `gh secret list` and configure the repository secret.
- **Model variable empty in Actions:** run `gh variable list` and set `SUT_MODEL` / `JUDGE_MODEL`.
- **PR workflow did not start:** confirm the PR targets `main` and changes at least one path monitored by `ai-evaluation.yml`.
- **Workflow is disabled in a fork:** open the GitHub Actions tab and enable workflows.
- **Import/package errors:** activate `.venv` and rerun `pip install -r requirements.txt`.
- **Slow first local run:** the embedding model may be downloading.
- **Different local vs CI behavior:** confirm Python 3.12, model variables, dataset revision and current branch/commit are the same.

## Reference documentation

- `README.md` — project overview and architecture
- `.github/workflows/ai-evaluation.yml` — canonical PR Critical CI flow
- `.github/workflows/ai-regression.yml` — canonical Regression CI flow
- `.github/workflows/ai-nightly.yml` — canonical Nightly CI flow
- `docs/architecture.md` — implemented architecture and failure localization
- `docs/test_strategy.md` — test strategy
- `docs/metric_contract.md` — metric definitions and denominators
- `docs/automated_ai_evaluation.md` — Oracle routing and evaluation architecture
