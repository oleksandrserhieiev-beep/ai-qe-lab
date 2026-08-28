import unittest

from src.risk_reporting import build_risk_summary, normalize_risks


class RiskReportingTests(unittest.TestCase):
    def test_normalize_risks_supports_string_and_list(self):
        self.assertEqual(
            normalize_risks("retrieval_quality"),
            ["retrieval_quality"],
        )
        self.assertEqual(
            normalize_risks([
                "retrieval_quality",
                "constraint_adherence",
                "retrieval_quality",
            ]),
            ["retrieval_quality", "constraint_adherence"],
        )

    def test_build_risk_summary_counts_multi_risk_case(self):
        cases = [
            {
                "case_id": "G-001",
                "risk": [
                    "retrieval_quality",
                    "constraint_adherence",
                ],
                "evaluation": {
                    "overall_pass": True,
                    "retrieval_pass": True,
                    "correctness": True,
                    "groundedness": True,
                    "constraint_adherence": True,
                    "hallucination": False,
                },
            }
        ]

        report = build_risk_summary(cases)

        self.assertEqual(report["risk_count"], 2)
        self.assertEqual(report["unclassified_count"], 0)
        self.assertEqual(
            report["risk_summary"]["retrieval_quality"]["pass_rate"],
            100.0,
        )
        self.assertEqual(
            report["risk_summary"]["constraint_adherence"]["total_cases"],
            1,
        )

    def test_build_risk_summary_reports_failures(self):
        cases = [
            {
                "case_id": "G-002",
                "risk": "policy_grounding",
                "evaluation": {
                    "overall_pass": False,
                    "retrieval_pass": True,
                    "correctness": False,
                    "groundedness": False,
                    "constraint_adherence": True,
                    "hallucination": True,
                },
            }
        ]

        summary = build_risk_summary(cases)["risk_summary"]["policy_grounding"]

        self.assertEqual(summary["passed"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["pass_rate"], 0.0)
        self.assertEqual(summary["hallucination_rate"], 100.0)

    def test_build_risk_summary_tracks_unclassified_cases(self):
        cases = [
            {
                "case_id": "E-999",
                "risk": None,
                "evaluation": {
                    "overall_pass": True,
                },
            }
        ]

        report = build_risk_summary(cases)

        self.assertEqual(report["unclassified_count"], 1)
        self.assertEqual(report["unclassified_cases"], ["E-999"])


if __name__ == "__main__":
    unittest.main()
