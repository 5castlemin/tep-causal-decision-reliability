import unittest
import numpy as np
from research.budget_aware_refinement.run_step4b4_statistical_calibration_v2 import _summarize, ALPHA, SHIFT
from research.budget_aware_refinement.step4b4_design import student_t_critical

class V2NumericCalibrationTests(unittest.TestCase):
    def test_null_and_alternative_ci_cover_their_own_true_mean(self):
        critical=student_t_critical(ALPHA,199)
        null=np.zeros((10,200))
        alt=null+SHIFT
        a=_summarize(null,0.,critical)
        b=_summarize(alt,SHIFT,critical)
        self.assertEqual(a['true_mean_ci_coverage'],1.)
        self.assertEqual(a['type1_or_power_rejects_zero'],0.)
        self.assertEqual(b['true_mean_ci_coverage'],1.)
        self.assertEqual(b['type1_or_power_rejects_zero'],1.)

    def test_nonzero_constant_is_explicitly_degenerate_and_not_zero_coverage(self):
        critical=student_t_critical(ALPHA,199)
        values=np.full((1,200),.1)
        self.assertEqual(_summarize(values,0.,critical)['true_mean_ci_coverage'],0.)
        self.assertEqual(_summarize(values,.1,critical)['true_mean_ci_coverage'],1.)
        self.assertEqual(_summarize(values,0.,critical)['zero_sample_sd_rate'],1.)

    def test_numpy_rounding_does_not_turn_exact_constant_into_tiny_variance(self):
        critical=student_t_critical(ALPHA,199)
        values=np.full((1,200),1e-14)
        result=_summarize(values,1e-14,critical)
        self.assertEqual(result['zero_sample_sd_rate'],1.)
        self.assertEqual(result['true_mean_ci_coverage'],1.)
        self.assertEqual(result['numeric_failure_rate'],0.)

if __name__=='__main__':unittest.main()
