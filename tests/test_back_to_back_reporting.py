from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from back_to_back_report import build_verdict, comparison_status  # noqa: E402


def test_comparison_status_higher_is_better():
    assert comparison_status(90.0, 100.0, higher_is_better=True) == "better"
    assert comparison_status(100.0, 90.0, higher_is_better=True) == "worse"
    assert comparison_status(100.0, 100.0, higher_is_better=True) == "same"


def test_comparison_status_lower_is_better():
    assert comparison_status(1000.0, 900.0, higher_is_better=False) == "better"
    assert comparison_status(900.0, 1000.0, higher_is_better=False) == "worse"
    assert comparison_status(900.0, 900.0, higher_is_better=False) == "same"


def _comparison(a_pass=100.0, b_pass=100.0, a_latency=1000.0, b_latency=1200.0, a_tokens=500, b_tokens=700):
    return {
        "quality_comparison": {
            "overall_pass_rate": {"model_a": a_pass, "model_b": b_pass},
            "correctness_rate": {"model_a": 100.0, "model_b": 100.0},
            "groundedness_rate": {"model_a": 100.0, "model_b": 100.0},
            "constraint_adherence_rate": {"model_a": 100.0, "model_b": 100.0},
            "hallucination_rate": {"model_a": 0.0, "model_b": 0.0},
        },
        "operational_comparison": {
            "avg_latency_ms": {"model_a": a_latency, "model_b": b_latency},
            "p95_latency_ms": {"model_a": a_latency, "model_b": b_latency},
            "total_tokens": {"model_a": a_tokens, "model_b": b_tokens},
            "avg_tokens_per_case": {"model_a": a_tokens / 10, "model_b": b_tokens / 10},
        },
        "decision_signals": {"critical_regressions": []},
    }


def test_verdict_prefers_quality_over_efficiency():
    comparison = _comparison(a_pass=90.0, b_pass=100.0, a_latency=900.0, b_latency=2000.0)
    verdict = build_verdict(comparison, "model-a", "model-b")
    assert verdict["winner"] == "model-b"
    assert verdict["basis"] == "quality"


def test_verdict_uses_efficiency_when_quality_is_tied():
    comparison = _comparison(a_pass=100.0, b_pass=100.0, a_latency=900.0, b_latency=2000.0, a_tokens=500, b_tokens=800)
    verdict = build_verdict(comparison, "model-a", "model-b")
    assert verdict["winner"] == "model-a"
    assert verdict["basis"] == "operational efficiency"


def test_verdict_blocks_candidate_on_critical_regression():
    comparison = _comparison()
    comparison["decision_signals"]["critical_regressions"] = ["G-001"]
    verdict = build_verdict(comparison, "model-a", "model-b")
    assert verdict["winner"] == "model-a"
    assert verdict["basis"] == "quality"
