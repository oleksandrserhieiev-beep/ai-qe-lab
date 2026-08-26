# Dataset Design

## Golden Dataset
Purpose: small, trusted reference set for canonical business-critical behaviour. Expected source/facts are manually controlled. Use for baseline quality, smoke evaluation and evaluator calibration. Do not fill it with every edge case.

Selection focus: critical multi-constraint product search, canonical policy facts, sensitive-data behaviour, abstention, exact product facts, policy paraphrases.

## Evaluation Dataset
Purpose: broader measurement of model/system quality. Segmented by normal, ambiguous, negative/no-match, multi-constraint, out-of-domain, missing-information, conflicting-source, adversarial, paraphrase and long-query cases.

Selection focus: representative distribution + known AI failure modes. Use to calculate correctness, groundedness, hallucination rate, retrieval quality and segment-level quality.

## Regression Dataset
Purpose: stable, repeatable subset run after prompt/model/embedding/RAG/config/application changes. Contains critical golden cases plus representative evaluation cases.

Selection focus: high business impact, previously failed cases, critical AI risks, stable expected behaviour. Add every confirmed escaped defect as a regression candidate.

## Versioning rule
Version datasets independently (e.g. golden-v1.0, eval-v1.1, regression-v1.3). Record dataset version with every evaluation run. Never compare two runs without knowing model, prompt, KB and dataset versions.
