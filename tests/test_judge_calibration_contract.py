import pytest

from judge_calibration_runner import validate_judge_contract


def test_judge_calibration_requires_non_empty_reason():
    with pytest.raises(ValueError, match="non-empty reason"):
        validate_judge_contract({"correctness": True, "reason": None})

    with pytest.raises(ValueError, match="non-empty reason"):
        validate_judge_contract({"correctness": True, "reason": "   "})


def test_judge_calibration_normalizes_reason():
    result = validate_judge_contract(
        {
            "correctness": True,
            "groundedness": True,
            "hallucination": False,
            "constraint_adherence": True,
            "reason": "  Supported by the retrieved policy.  ",
        }
    )

    assert result["reason"] == "Supported by the retrieved policy."
