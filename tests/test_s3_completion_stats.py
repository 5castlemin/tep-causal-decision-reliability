import unittest

from research.within_task_repair_prioritization.s4_completion.finalize_saved_s3 import holm, paired_t_pvalue


class S3CompletionStatsTests(unittest.TestCase):
    def test_paired_t_probability_known_df2_case(self):
        # [1, 2, 3] has t=sqrt(12), df=2, two-sided p=0.0741799002.
        self.assertAlmostEqual(paired_t_pvalue([1.0, 2.0, 3.0]), 0.0741799002, places=8)

    def test_paired_t_zero_variance(self):
        self.assertEqual(paired_t_pvalue([0.0, 0.0, 0.0]), 1.0)
        self.assertEqual(paired_t_pvalue([1.0, 1.0, 1.0]), 0.0)

    def test_holm_is_monotone_in_sorted_order_and_bounded(self):
        adjusted = holm([0.04, 0.001, 0.02])
        self.assertEqual(adjusted[1], 0.003)
        self.assertTrue(all(0.0 <= value <= 1.0 for value in adjusted))
        self.assertGreaterEqual(adjusted[0], adjusted[2])


if __name__ == "__main__":
    unittest.main()
