import unittest

from validate_qualification import dyad_counts, validate


class QualificationValidationTests(unittest.TestCase):
    def test_mk2_pair_denominators(self):
        self.assertEqual(dyad_counts(90, 142), (4005, 3863, 7726))

    def test_existing_audit_and_qualification_counts_agree(self):
        result = validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["constant_column_graph_overlap"], (67, 59, 31, 8))
        self.assertFalse(result["response_values_read"])


if __name__ == "__main__":
    unittest.main()
