import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from evaluator import evaluate_retrieval


class EvaluateRetrievalTests(unittest.TestCase):
    def test_expected_product_matches_product_id(self):
        case = {
            "expected_retrieved_product": "P-1001",
            "expected_source": "products.json",
            "retrieval": [
                {"id": "P-1001", "type": "product"},
            ],
        }

        self.assertTrue(evaluate_retrieval(case))

    def test_products_source_matches_product_document_type(self):
        case = {
            "expected_source": "products.json",
            "retrieval": [
                {"id": "P-1154", "type": "product"},
            ],
        }

        self.assertTrue(evaluate_retrieval(case))

    def test_products_source_fails_without_product_document(self):
        case = {
            "expected_source": "products.json",
            "retrieval": [
                {"id": "returns_policy.md", "type": "policy"},
            ],
        }

        self.assertFalse(evaluate_retrieval(case))

    def test_policy_source_still_requires_exact_policy_id(self):
        case = {
            "expected_source": "warranty_policy.md",
            "retrieval": [
                {"id": "warranty_policy.md", "type": "policy"},
            ],
        }

        self.assertTrue(evaluate_retrieval(case))

    def test_none_source_has_no_retrieval_oracle(self):
        case = {
            "expected_source": "none",
            "retrieval": [],
        }

        self.assertTrue(evaluate_retrieval(case))


if __name__ == "__main__":
    unittest.main()