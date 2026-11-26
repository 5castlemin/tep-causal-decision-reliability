import unittest
import numpy as np

from research.decision_oriented_verification.run_expert_noise_sensitivity import (
    NO_EDGE, U_TO_V, V_TO_U, noisy_answer, wrong_count,
)
from research.decision_oriented_verification.audit_expert_noise import bootstrap


class ExpertNoiseSensitivityTests(unittest.TestCase):
    def test_wrong_response_reconstruction_uses_pair_truth_and_direction(self):
        truth = {("A", "B"): ("A", "B"), ("A", "C"): ("C", "A")}
        history = [
            {"pair": ["A", "B"], "answer": U_TO_V},
            {"pair": ["A", "C"], "answer": U_TO_V},
            {"pair": ["B", "C"], "answer": NO_EDGE},
        ]
        self.assertEqual(wrong_count(history, truth), 1)

    def test_hypothetical_expert_response_is_seed_deterministic(self):
        truth = {("A", "B"): ("A", "B")}
        args = (truth, ("A", "B"), 0.8, 3, "C_DEVELOPMENT", "fixture-scm")
        self.assertEqual(noisy_answer(*args), noisy_answer(*args))
        self.assertIn(noisy_answer(*args), {NO_EDGE, U_TO_V, V_TO_U})

    def test_nested_bootstrap_preserves_paired_policy_sign(self):
        values = np.zeros((4, 16, 4), dtype=float)
        values[:, :, 0] = 1.0
        values[:, :, 3] = 4.0
        result = bootstrap(values, "fixture", 0.9, 0, 3)
        self.assertEqual(result["comparator_minus_proposed"], -3.0)
        self.assertEqual((result["ci95_low"], result["ci95_high"]), (-3.0, -3.0))


if __name__ == "__main__":
    unittest.main()
