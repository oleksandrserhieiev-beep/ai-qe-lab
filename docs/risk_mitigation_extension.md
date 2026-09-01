# Risk Analysis — Mitigation extension

Risk Analysis now separates three concepts per risk:

- `risk_statement`: what can go wrong;
- `mitigation`: proposed controls/actions that could reduce likelihood and/or impact;
- `recommended_test_focus`: what testing should focus on to verify the risk and/or controls.

Likelihood and Impact remain semantic 1–5 assessments. Risk Score and Priority remain deterministic Python calculations. Mitigation and test focus are advisory and require human review.

The Prioritized Risk Register surfaces both Mitigation and Recommended Test Focus alongside Issue, Risk Type, Category, Risk, Likelihood, Impact, Score, and Priority.
