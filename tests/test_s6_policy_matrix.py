import csv
import unittest
from pathlib import Path

from research.supplementary_validation.s6.analyze_s6_policy_matrix import best, frozen, guided, type_first


class S6PolicyMatrixTests(unittest.TestCase):
    def test_metric_tie_uses_m4_gain_even_when_secondary_is_negative(self):
        rows = [
            {"pair": ["a", "b"], "operation": "delete", "M4_gain": -0.5, "T5_gain": 0.2},
            {"pair": ["a", "c"], "operation": "delete", "M4_gain": -0.1, "T5_gain": 0.2},
        ]
        chosen, fallback = guided(rows, "T5_gain")
        self.assertFalse(fallback)
        self.assertEqual(chosen["pair"], ["a", "c"])

    def test_nonpositive_metric_falls_back_to_frozen_m4(self):
        rows = [
            {"pair": ["a", "b"], "operation": "delete", "M4_gain": 0.2, "T1_gain": 0.0},
            {"pair": ["a", "c"], "operation": "delete", "M4_gain": 0.1, "T1_gain": -0.1},
        ]
        chosen, fallback = guided(rows, "T1_gain")
        self.assertTrue(fallback)
        self.assertEqual(chosen, frozen(rows))

    def test_type_first_fallback_and_canonical_order(self):
        rows = [
            {"pair": ["a", "c"], "operation": "delete", "kind": "FN", "M4_gain": 0.4},
            {"pair": ["a", "b"], "operation": "delete", "kind": "FP", "M4_gain": 0.3},
        ]
        chosen, fallback = type_first(rows, "REV")
        self.assertTrue(fallback)
        self.assertEqual(chosen["pair"], ["a", "c"])
        tied = [dict(rows[0], M4_gain=0.5), dict(rows[1], M4_gain=0.5)]
        self.assertEqual(best(tied, lambda x: x["M4_gain"])["pair"], ["a", "b"])

    def test_saved_reaggregation_matches_frozen_and_t5_replay(self):
        path = Path(__file__).parents[1] / "research" / "supplementary_validation" / "s6" / "outputs" / "saved_candidates_v6" / "v4_replay_consistency.csv"
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["matches_within_1e-12"] == "True" for row in rows))
        self.assertTrue(all(float(row["absolute_difference"]) == 0.0 for row in rows))


if __name__ == "__main__":
    unittest.main()
