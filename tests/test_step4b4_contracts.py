import unittest
import gzip, json
from pathlib import Path
from research.budget_aware_refinement.step4b4_design import (
    clopper_pearson, minimum_attempt_cap, student_t_critical, paired_t_interval,
)
from research.budget_aware_refinement.step4_rng import RNGKey, derive_seed
from research.budget_aware_refinement.step4b4_failure_rules import (
    classify_status, fallback_rule, infra_retry_rule, scm_composite, confirmation_action,
)

class Step4B4ContractTests(unittest.TestCase):
    def test_exact_interval_and_cap(self):
        lo, hi = clopper_pearson(637, 2000)
        self.assertAlmostEqual(lo, 0.29811006, places=7)
        self.assertAlmostEqual(hi, 0.33942335, places=7)
        cap, prob = minimum_attempt_cap(64, .2, .95)
        self.assertEqual(cap, 381)
        self.assertGreaterEqual(prob, .95)

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
