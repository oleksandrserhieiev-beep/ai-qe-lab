import json
import tempfile
import unittest
from pathlib import Path

from src.risk_coverage import (
    build_coverage_matrix,
    canonicalize_case_risks,
)


class RiskCoverageTests(unittest.TestCase):
    def test_explicit_alias_maps_to_canonical_risks(self):
        case = {"Risk": "retrieval_and_constraints"}
        self.assertEqual(
            canonicalize_case_risks(case),
            ["retrieval_quality", "constraint_adherence"],
        )

    def test_segment_is_not_treated_as_risk(self):
        case = {"Segment": "adversarial"}
        self.assertEqual(canonicalize_case_risks(case), [])

    def test_explicit_multi_risk_is_preserved(self):
        case = {"Risk": ["policy_grounding", "robustness"]}
        self.assertEqual(
            canonicalize_case_risks(case),
            ["policy_grounding", "robustness"],
        )

    def test_matrix_counts_explicit_risk_coverage_and_unclassified(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            critical = base / "critical.json"
            regression = base / "regression.json"
            nightly = base / "nightly.json"

            critical.write_text(
                json.dumps([
                    {"ID": "C-1", "Risk": ["retrieval_quality"]},
                ]),
                encoding="utf-8",
            )
            regression.write_text(
                json.dumps([
                    {"ID": "R-1", "Risk": "retrieval_and_constraints"},
                    {"ID": "R-2"},
                ]),
                encoding="utf-8",
            )
            nightly.write_text(
                json.dumps([
                    {"ID": "N-1", "Segment": "multi_constraint"},
                ]),
                encoding="utf-8",
            )

            report = build_coverage_matrix(
                {
                    "critical": critical,
                    "regression": regression,
                    "nightly": nightly,
                }
            )

            rows = {row["risk"]: row for row in report["matrix"]}

            self.assertEqual(
                rows["retrieval_quality"]["coverage"],
                {"critical": 1, "regression": 1, "nightly": 0},
            )
            self.assertEqual(
                rows["constraint_adherence"]["coverage"],
                {"critical": 0, "regression": 1, "nightly": 0},
            )
            self.assertEqual(report["unclassified_count"], 2)
            self.assertEqual(report["unclassified"]["regression"], ["R-2"])
            self.assertEqual(report["unclassified"]["nightly"], ["N-1"])


if __name__ == "__main__":
    unittest.main()
