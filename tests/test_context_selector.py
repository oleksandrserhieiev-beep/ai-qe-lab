import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from context_selector import select_context_results  # noqa: E402


def _item(item_id, score):
    return {"id": item_id, "score": score}


def test_selects_only_candidates_above_similarity_threshold():
    retrieved = [
        _item("A", 0.70),
        _item("B", 0.45),
        _item("C", 0.29),
    ]

    selected = select_context_results(
        retrieved,
        min_k=2,
        max_k=5,
        min_similarity=0.30,
    )

    assert [item["id"] for item in selected] == ["A", "B"]


def test_does_not_pad_with_low_similarity_to_reach_min_k():
    retrieved = [
        _item("A", 0.70),
        _item("B", 0.20),
        _item("C", 0.10),
    ]

    selected = select_context_results(
        retrieved,
        min_k=2,
        max_k=5,
        min_similarity=0.30,
    )

    assert [item["id"] for item in selected] == ["A"]


def test_caps_selected_context_at_max_k():
    retrieved = [
        _item("A", 0.90),
        _item("B", 0.80),
        _item("C", 0.70),
        _item("D", 0.60),
    ]

    selected = select_context_results(
        retrieved,
        min_k=2,
        max_k=3,
        min_similarity=0.30,
    )

    assert [item["id"] for item in selected] == ["A", "B", "C"]


def test_returns_empty_context_when_no_candidate_meets_threshold():
    retrieved = [_item("A", 0.20), _item("B", 0.10)]

    selected = select_context_results(
        retrieved,
        min_k=2,
        max_k=5,
        min_similarity=0.30,
    )

    assert selected == []
