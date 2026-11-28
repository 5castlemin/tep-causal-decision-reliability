import unittest
import gzip, json
from pathlib import Path
from research.budget_aware_refinement.step4b4_design import (
    clopper_pearson, minimum_attempt_cap, student_t_critical, paired_t_interval,
    paired_t_summary, stratified_yield_interval, stratified_yield_variance, stratified_yield_variance_upper,
)
from research.budget_aware_refinement.step4_rng import RNGKey, derive_seed
from research.budget_aware_refinement.step4b4_failure_rules import (
    classify_status, fallback_rule, infra_retry_rule, scm_composite, confirmation_action, probability_complete,
)

class Step4B4ContractTests(unittest.TestCase):
    def test_exact_interval_and_cap(self):
        lo, hi = clopper_pearson(637, 2000)
        self.assertAlmostEqual(lo, 0.29811006, places=7)
        self.assertAlmostEqual(hi, 0.33942335, places=7)
        cap, prob = minimum_attempt_cap(64, .2, .95)
        self.assertEqual(cap, 381)
        self.assertGreaterEqual(prob, .95)

    def test_truth_specific_interval_coverage_and_degenerate_samples(self):
        constant_zero=paired_t_summary([0.0]*200,true_mean=0.0)
        self.assertTrue(constant_zero['ci_covers_true_mean'])
        self.assertFalse(constant_zero['rejects_zero'])
        self.assertTrue(constant_zero['zero_sample_sd'])
        self.assertEqual(constant_zero['inference_status'],'degenerate_zero_variance')
        constant_alt=paired_t_summary([0.1]*200,true_mean=0.1)
        self.assertTrue(constant_alt['ci_covers_true_mean'])
        self.assertTrue(constant_alt['rejects_zero'])
        misspecified_truth=paired_t_summary([0.1]*200,true_mean=0.0)
        self.assertFalse(misspecified_truth['ci_covers_true_mean'])
        near=paired_t_summary([1e-14,1.0000001e-14,0.9999999e-14]*67,true_mean=1e-14)
        self.assertTrue(near['near_zero_sd'])
        self.assertFalse(near['numeric_failure'])

    def test_stratified_interval_and_variance_keep_boundary_strata(self):
        lo,hi=stratified_yield_interval([0,100],[100,100])
        self.assertGreater(lo,0)
        self.assertLess(hi,1)
        self.assertEqual(stratified_yield_variance([0,100],[100,100]),0)
        self.assertGreater(stratified_yield_variance_upper([0,100],[100,100]),0)
        self.assertAlmostEqual(stratified_yield_variance([25,75],[100,100]),.0009375)

    def test_mcar_completion_probabilities_are_scm_or_type_cell_level(self):
        self.assertAlmostEqual(probability_complete(200,.001),.818649,places=5)
        self.assertAlmostEqual(probability_complete(200,.001,3),.548647,places=5)
        with self.assertRaises(ValueError):probability_complete(200,1.1)

    def test_t_helpers_and_zero_vector(self):
        self.assertAlmostEqual(student_t_critical(.05, 199), 1.9719565, places=5)
        lo, hi = paired_t_interval([0.0, 0.0, 0.0])
        self.assertEqual((lo, hi), (0.0, 0.0))

    def test_rng_context_keys_separate_cohort_id_attempt_and_stream(self):
        common=dict(protocol_version='step4-rng-v1', master_seed=87,
                    scm_id='confirmation-0001', topology_template='chain_mediation',
                    node_count=8, topology_attempt=2)
        def seed(**kw):
            return derive_seed(RNGKey(stream_name='task_selection', **(common|kw)))
        a=seed(cohort='development')
        self.assertEqual(a,seed(cohort='development'))
        self.assertNotEqual(a,seed(cohort='confirmation'))
        self.assertNotEqual(a,seed(cohort='development',scm_id='confirmation-0002'))
        self.assertNotEqual(a,seed(cohort='development',topology_attempt=3))
        self.assertNotEqual(a,derive_seed(RNGKey('step4-rng-v1','development',87,
            'confirmation-0001','chain_mediation',8,2,'policy_schedule')))

    def test_status_and_fallback_contract(self):
        self.assertEqual(classify_status('UNUSED_BUDGET'), 'normal_result')
        self.assertFalse(fallback_rule('GT_EVAL_FAIL', training_valid=True, truth_valid=False, k0_in_common_action_grid=True)['fallback'])
        r=fallback_rule('RIDGE_FAIL', training_valid=True, truth_valid=True, k0_in_common_action_grid=True)
        self.assertTrue(r['fallback']); self.assertEqual(r['original_status'], 'RIDGE_FAIL')
        self.assertFalse(fallback_rule('RECOMMEND_FAIL', training_valid=True, truth_valid=True, k0_in_common_action_grid=False)['fallback'])

    def test_retry_is_same_key_once_and_composite_requires_three_types(self):
        self.assertTrue(infra_retry_rule('IO_FAIL', 1)['same_input_and_rng_key'])
        self.assertFalse(infra_retry_rule('IO_FAIL', 2)['retry'])
        self.assertFalse(scm_composite({'FN': 1., 'FP': 2., 'REV': None})['complete'])
        self.assertEqual(scm_composite({'FN': 1., 'FP': 2., 'REV': 3.})['D_i'], 2.)

    def test_v2_stratified_yield_artifact_and_document_agree(self):
        root=Path(__file__).resolve().parents[1]/'research'/'budget_aware_refinement'
        import json
        raw=json.loads((root/'step4b4_stratified_yield_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(raw['total_attempts'],2000)
        self.assertEqual(raw['total_successes'],637)
        self.assertEqual(raw['zero_success_strata'],5)
        self.assertEqual(raw['all_success_strata'],1)
        self.assertAlmostEqual(raw['weighted_stratified_point_estimate'],.3185)
        report=(root/'STEP4B4_STRATIFIED_YIELD_REVIEW.md').read_text(encoding='utf-8')
        self.assertIn(raw['settings_sha256'],report)
        self.assertIn('362',report);self.assertIn('1,036',report)

    def test_v2_stats_failure_and_resource_artifacts_match_reports(self):
        root=Path(__file__).resolve().parents[1]/'research'/'budget_aware_refinement'
        import json
        stats=json.loads((root/'step4b4_statistical_calibration_v2.json').read_text(encoding='utf-8'))
        x=stats['results_by_seed']['4042026']['zero_heavy_skewed']['200']['null']
        self.assertAlmostEqual(x['type1_or_power_rejects_zero'],.13635)
        self.assertAlmostEqual(x['true_mean_ci_coverage'],.86365)
        stat_report=(root/'STEP4B4_STATISTICAL_CALIBRATION_V2.md').read_text(encoding='utf-8')
        self.assertIn(stats['settings_sha256'],stat_report)
        failure=json.loads((root/'step4b4_failure_feasibility_v2.json').read_text(encoding='utf-8'))
        self.assertAlmostEqual(failure['missing_rates']['0.001']['complete_if_each_of_three_type_cells_is_event'],.5486469)
        resources=json.loads((root/'step4b4_resource_bench_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(resources['fixture']['shape'],[512,10])
        self.assertTrue(resources['measurements']['resume_idempotence_mock']['reopened_duplicate_blocked'])
        self.assertEqual(resources['measurements']['process_peak_rss_after'] > 0,True)

    def test_q_yield_raw_summary_and_report_denominator_match(self):
        root=Path(__file__).resolve().parents[1]/'research'/'budget_aware_refinement'
        raw=json.loads(gzip.decompress((root/'step4b4_q_yield_v1.json.gz').read_bytes()))
        summary=json.loads((root/'step4b4_q_yield_summary_v1.json').read_text(encoding='utf-8'))
        accepted=sum(bool(row['accepted_q_common']) for row in raw['rows'])
        self.assertEqual((len(raw['rows']),accepted),(summary['total_attempts'],summary['accepted']))
        self.assertAlmostEqual(accepted/len(raw['rows']),summary['acceptance_rate'])
        report=(root/'STEP4B4_SAMPLING_AND_ESTIMAND_CONTRACT.md').read_text(encoding='utf-8')
        self.assertIn(f'{accepted}/{len(raw["rows"])}',report)
        self.assertIn(raw['settings_sha256'],report)

    def test_shortfall_and_missing_stop_inference(self):
        a=confirmation_action(q_eligible_target=200, q_eligible_observed=199, candidate_attempts=700, attempt_cap=738, missing_primary_scm_rows=0)
        self.assertFalse(a['inferential_start'])
        b=confirmation_action(q_eligible_target=200, q_eligible_observed=200, candidate_attempts=700, attempt_cap=738, missing_primary_scm_rows=1)
        self.assertEqual(b['state'], 'inconclusive')

if __name__ == '__main__': unittest.main()
