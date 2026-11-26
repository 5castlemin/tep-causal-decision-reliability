import unittest

import numpy as np

from research.final_supplementary_validation.analyze_supplementary import (
    K, apply_saved_edits, choose, gamma_loss, grouped_folds, pe, structural_features,
)


class SupplementaryValidationTests(unittest.TestCase):
    def test_gamma_zero_reproduces_original_tracking_loss(self):
        actual = gamma_loss([0.0, 0.5, 1.0, 1.5, 2.0], 1.0, 2.0, 0.0)
        expected = np.array([((x - 1.0) / 2.0) ** 2 for x in [0.0, .5, 1.0, 1.5, 2.0]])
        np.testing.assert_array_equal(actual, expected)

    def test_positive_gamma_penalizes_stronger_action_and_can_choose_zero(self):
        base = gamma_loss([0, 0, 0, 0, 0], 0, 1, 0)
        penalized = gamma_loss([0, 0, 0, 0, 0], 0, 1, 1)
        self.assertEqual(K[choose(base)], 0)
        self.assertEqual(K[choose(penalized)], 0)
        self.assertGreater(penalized[-1], base[-1])

    def test_tie_break_prefers_zero_then_negative_k(self):
        self.assertEqual(K[choose([1, 1, 0, 1, 1])], 0)
        # Symmetric losses at -0.5 and +0.5: smaller |k| is preferred; if tied
        # also on |k|, the negative k canonical order wins.
        self.assertEqual(K[choose([9, 1, 9, 1, 9])], -0.5)

    def test_saved_edit_replay_verifies_hash_and_dag(self):
        truth = pe.state([("X", "Y")])
        initial = pe.state((), ())
        after = pe.state([("X", "Y")])
        log = [{"pair": ["X", "Y"], "error_type": "FN", "operation": "add", "after_hash": pe.graph_hash(after)}]
        self.assertEqual(apply_saved_edits(initial, truth, log), truth)

    def test_structural_metrics_distinguish_skeleton_and_direction(self):
        truth = pe.state([("X", "Y")])
        reversed_graph = pe.state([("Y", "X")])
        stats = structural_features(truth, reversed_graph, "X", "Y", pe.Config(), ["X", "Y"])
        self.assertEqual(stats["skeleton_f1"], 1.0)
        self.assertEqual(stats["directed_f1"], 0.0)
        self.assertEqual(stats["directed_shd"], 1)

    def test_grouped_folds_never_split_same_scm(self):
        rows = [{"scm_id": f"s{i}", "regret": float(i)} for i in range(10) for _ in range(i % 3 + 1)]
        for train, valid in grouped_folds(rows, 5):
            train_ids = {r["scm_id"] for r in train}
            valid_ids = {r["scm_id"] for r in valid}
            self.assertFalse(train_ids & valid_ids)


if __name__ == "__main__":
    unittest.main()
