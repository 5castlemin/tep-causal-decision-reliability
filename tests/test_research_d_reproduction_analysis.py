from __future__ import annotations

import unittest

import numpy as np

from research.external_validation.semisynthetic_evaluation.analyze_development_reproduction_v2 import (
    _loss_and_bootstrap,
)


class ResearchDReproductionAnalysisTests(unittest.TestCase):
    def test_shared_action_loss_bootstrap_keeps_g0_and_mc_axes_aligned(self):
        actions = [0.1, 0.9]
        vectors = [np.asarray([0.0, 0.2, 0.4, 0.6]),
                   np.asarray([0.4, 0.6, 0.8, 1.0])]
        recommendations = {"recommendations": []}
        for seed, s0_action, greedy_action in ((11, 0.1, 0.9), (12, 0.9, 0.1)):
            recommendations["recommendations"].extend([
                {"g0_seed_id": seed, "budget": 2, "policy_id": "S0",
                 "recommended_action": s0_action},
                {"g0_seed_id": seed, "budget": 2, "policy_id": "M1+M2+M3+M4",
                 "recommended_action": greedy_action},
            ])
        lock = {"target_scale": {"target": 0.5, "scale": 1.0},
            "evaluation": {"rows_per_action": 4, "bootstrap_replicates": 30,
                "bootstrap_seed": 73}, "g0": {"seed_ids": [11, 12]}}

        primary, summaries, losses, intervals = _loss_and_bootstrap(
            actions, vectors, recommendations, lock)

        expected = (losses["0.1"]["bias_corrected_loss"] -
                    losses["0.9"]["bias_corrected_loss"] +
                    losses["0.9"]["bias_corrected_loss"] -
                    losses["0.1"]["bias_corrected_loss"]) / 2
        self.assertEqual(primary, expected)
        self.assertEqual(summaries["0.1"]["n"], 4)
        self.assertEqual(set(intervals), {"g0_only_percentile_95",
            "action_mc_only_percentile_95", "two_source_percentile_95"})
        self.assertTrue(all(len(bounds) == 2 and np.isfinite(bounds).all()
                            for bounds in intervals.values()))


if __name__ == "__main__":
    unittest.main()
