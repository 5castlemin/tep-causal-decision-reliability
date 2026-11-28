import unittest
import csv
import tempfile
from pathlib import Path

import numpy as np

from research.final_supplementary_validation.analyze_supplementary import (
    K, apply_saved_edits, choose, gamma_loss, grouped_folds, pe, save_csv, structural_features, summarize_s1,
)
from research.final_supplementary_validation.audit_supplementary import classification_metrics


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

    def test_csv_writer_preserves_union_of_heterogeneous_audit_fields(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "audit.csv"
            save_csv(path, [{"cohort": "dev", "metric": "a"}, {"cohort": "held", "analysis": "G0"}])
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["analysis"], "")
            self.assertEqual(rows[1]["analysis"], "G0")

    def test_weighted_auc_is_a_probability_and_handles_ties(self):
        perfect = classification_metrics([0, 1], [0.1, 0.9], [1, 1])
        reversed_order = classification_metrics([0, 1], [0.9, 0.1], [1, 1])
        tied = classification_metrics([0, 1], [0.5, 0.5], [1, 1])
        self.assertEqual(perfect["auroc"], 1.0)
        self.assertEqual(reversed_order["auroc"], 0.0)
        self.assertEqual(tied["auroc"], 0.5)
        self.assertTrue(0.0 <= tied["auroc"] <= 1.0)

    def test_average_precision_is_invariant_to_permutation_inside_score_ties(self):
        a = classification_metrics([1, 0, 1, 0], [.8, .8, .2, .2], [3, 1, 2, 4])
        b = classification_metrics([0, 1, 0, 1], [.8, .8, .2, .2], [1, 3, 4, 2])
        self.assertEqual(a["average_precision"], b["average_precision"])
        self.assertTrue(0 <= a["average_precision"] <= 1)

    def test_average_precision_perfect_reversed_all_tied_and_weighted(self):
        perfect = classification_metrics([1, 1, 0, 0], [.9, .8, .2, .1], [3, 2, 7, 1])
        reversed_scores = classification_metrics([1, 1, 0, 0], [.1, .2, .8, .9], [3, 2, 7, 1])
        all_tied = classification_metrics([1, 0, 1, 0], [.5, .5, .5, .5], [3, 1, 2, 4])
        self.assertEqual(perfect["average_precision"], 1.0)
        self.assertAlmostEqual(reversed_scores["average_precision"], .4 * (2 / 10) + .6 * (5 / 13))
        self.assertAlmostEqual(all_tied["average_precision"], 5 / 10)

    def test_primary_policy_mapping_uses_full_greedy_not_canonical_oracle(self):
        rows = []
        values = {
            "S0": [0.30, 0.20, 0.10],
            "M1+M2+M3+M4": [0.20, 0.10, 0.00],
            "M4": [0.10, 0.10, 0.10],
            "CANONICAL_ORACLE": [0.00, 0.20, 0.30],
        }
        for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
            for policy, regrets in values.items():
                for i, regret in enumerate(regrets):
                    rows.append({"cohort": cohort, "scm_id": f"s{i}", "policy": policy,
                                 "budget": 2, "target_delta": "original", "gamma": .2, "regret": regret,
                                 "true_optimal_k": 0.0, "predicted_k": 0.0, "edit_count": 0,
                                 "estimated_slope": 0.0, "true_slope": 0.0})
        out = summarize_s1(rows)[1]
        by = {r["contrast"]: r for r in out}
        self.assertEqual(by["FullGreedy-S0"]["source_policy_a"], "M1+M2+M3+M4")
        self.assertEqual(by["FullGreedy-S0"]["source_policy_b"], "S0")
        self.assertAlmostEqual(by["FullGreedy-S0"]["mean_difference"], -.10)
        self.assertEqual(by["M4-FullGreedy"]["source_policy_b"], "M1+M2+M3+M4")
        self.assertAlmostEqual(by["CanonicalOracle-S0"]["mean_difference"], -.03333333333333333)

    def test_gamma_zero_policy_means_match_frozen_c_heldout_aggregate(self):
        path = Path(__file__).resolve().parents[1] / "research/final_supplementary_validation/outputs/s1_aggregate.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        expected = {"S0": .0934389768, "M1+M2+M3+M4": .0186026193,
                    "M4": .0039877460, "M2+M4": .0126739700}
        observed = {r["policy"]: float(r["mean_regret"]) for r in rows
                    if r["cohort"] == "C_HELDOUT" and r["target_delta"] == "original"
                    and float(r["gamma"]) == 0.0 and int(r["budget"]) == 2
                    and r["policy"] in expected}
        self.assertEqual(set(observed), set(expected))
        for policy, value in expected.items():
            self.assertAlmostEqual(observed[policy], value, places=7)


if __name__ == "__main__":
    unittest.main()
