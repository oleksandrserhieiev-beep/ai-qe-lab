import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from retrieval_metrics import (  # noqa: E402
    evaluate_constraint_retrieval,
    product_constraint_match_score,
)


class RetrievalMetricsTests(unittest.TestCase):
    def setUp(self):
        self.constraints = {
            "subcategory": "Jackets",
            "waterproof": True,
            "color": "black",
            "max_price": 150.0,
            "size": "L",
        }

        self.full_match = {
            "subcategory": "Jackets",
            "waterproof": True,
            "colors": ["black"],
            "price": 129.99,
            "sizes": ["S", "M", "L"],
        }

        self.four_of_five = {
            "subcategory": "Jackets",
            "waterproof": True,
            "colors": ["black"],
            "price": 129.99,
            "sizes": ["S", "M", "XL"],
        }

    def test_product_constraint_match_score_is_80_for_four_of_five(self):
        score = product_constraint_match_score(
            self.four_of_five,
            self.constraints,
        )

        self.assertEqual(score, 80.0)

    def test_constraint_metrics_report_best_match_and_precision(self):
        retrieval = [
            {
                "type": "product",
                "metadata": self.full_match,
            },
            {
                "type": "product",
                "metadata": self.four_of_five,
            },
        ]

        result = evaluate_constraint_retrieval(
            "Find a black waterproof jacket size L under $150",
            retrieval,
        )

        self.assertTrue(result["applicable"])
        self.assertEqual(result["constraint_match_score"], 100.0)
        self.assertEqual(result["constraint_precision_at_k"], 50.0)
        self.assertEqual(result["matching_products"], 1)
        self.assertEqual(result["retrieved_products"], 2)

    def test_no_detected_constraints_marks_metric_not_applicable(self):
        result = evaluate_constraint_retrieval(
            "What is the returns policy?",
            [],
        )

        self.assertFalse(result["applicable"])
        self.assertIsNone(result["constraint_match_score"])
        self.assertIsNone(result["constraint_precision_at_k"])

    def test_constraints_with_no_product_results_score_zero(self):
        result = evaluate_constraint_retrieval(
            "Find a black waterproof jacket size L under $150",
            [
                {
                    "type": "policy",
                    "metadata": {},
                }
            ],
        )

        self.assertTrue(result["applicable"])
        self.assertEqual(result["constraint_match_score"], 0.0)
        self.assertEqual(result["constraint_precision_at_k"], 0.0)


if __name__ == "__main__":
    unittest.main()
