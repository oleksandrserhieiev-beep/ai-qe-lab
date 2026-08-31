from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from back_to_back_report import comparison_status  # noqa: E402


def test_comparison_status_higher_is_better():
    assert comparison_status(90.0, 100.0, higher_is_better=True) == "better"
    assert comparison_status(100.0, 90.0, higher_is_better=True) == "worse"
    assert comparison_status(100.0, 100.0, higher_is_better=True) == "same"


def test_comparison_status_lower_is_better():
    assert comparison_status(1000.0, 900.0, higher_is_better=False) == "better"
    assert comparison_status(900.0, 1000.0, higher_is_better=False) == "worse"
    assert comparison_status(900.0, 900.0, higher_is_better=False) == "same"
