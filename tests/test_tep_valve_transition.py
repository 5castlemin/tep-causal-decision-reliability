"""Normal equation arithmetic, fail-closed contexts, and actual stored evidence."""
from copy import deepcopy
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

from src.tep_valve_transition_contract import validate_transition
from scripts.validate_tep_valve_transition_contract import load, validate_records, reject_cases, check_source, BASE, PIN


class ValveTransitionTests(unittest.TestCase):
    def setUp(self):
        self.row=deepcopy(load(BASE/'run_v1/TRANSITIONS.json')[-1])

    def test_actual_record_and_hour_second_conversion(self):
        r=validate_transition(self.row)
        self.assertEqual(r['status'],'VERIFIED_NARROW_TRANSITION')
        expected=self.row['v_before_pp']+(self.row['applied_c_pp']-self.row['v_before_pp'])/5
        self.assertAlmostEqual(r['expected_next_v_pp'],expected,places=12)
        self.assertFalse(r['official_gt']);self.assertFalse(r['global_f1_allowed'])

    def test_t0_cache_branch_and_positive_time_change(self):
        rows=load(BASE/'run_v1/TRANSITIONS.json')
        self.assertTrue(all(r['comparison']['cache_refresh'] for r in rows if r['step']==0))
        normal=next(r for r in rows if r['arm']=='reference' and r['step']==1)
        change=next(r for r in rows if r['arm']=='command_change' and r['step']==1)
        self.assertFalse(normal['comparison']['cache_refresh'])
        self.assertTrue(change['comparison']['cache_refresh'])
        self.assertNotEqual(change['cache_before_pp'],change['applied_c_pp'])

    def test_mock_invalid_contexts_are_rejected(self):
        results=reject_cases(self.row)
        self.assertEqual(len(results),12)
        self.assertTrue(all(r['input_kind']=='MOCK_ONLY_NOT_SIMULATED' for r in results))

    def test_missing_applied_cache_is_not_inferred(self):
        del self.row['applied_c_pp']
        r=validate_transition(self.row)
        self.assertIn('CACHE_UNKNOWN',r['reasons'])
        self.assertIsNone(r['expected_next_v_pp'])

    def test_command_not_applied_cache(self):
        self.row['requested_u_pp']+=0.1
        r=validate_transition(self.row)
        self.assertIn('CONTROLLER_OVERWRITE_OR_UNKNOWN',r['reasons'])
        self.assertIsNone(r['expected_next_v_pp'])

    def test_mock_boundaries_and_invalid_time_scales(self):
        for field,value in [('requested_u_pp',100),('v_before_pp',0),('dt_hours',0),
                            ('tau_hours',-1),('ivst14',None),('finite_state',False)]:
            with self.subTest(field=field):
                row=deepcopy(self.row);row[field]=value
                self.assertEqual(validate_transition(row)['status'],'REJECTED')

    def test_wrong_derivative_and_euler_are_not_context_passes(self):
        for field,reason in [('derivative_pp_per_hour','DERIVATIVE_MISMATCH'),('v_after_pp','EULER_MISMATCH')]:
            row=deepcopy(self.row);row[field]+=0.01
            self.assertIn(reason,validate_transition(row)['reasons'])

    def test_saved_records_and_old_cache_missing_scope(self):
        r=validate_records()
        self.assertEqual(len(r['old_algebraic_rechecks']),24)
        self.assertTrue(all(x['full_contract']=='BLOCKED_CACHE_UNKNOWN' for x in r['old_algebraic_rechecks']))
        self.assertEqual(r['levels'],{'L1':'VERIFIED','L2':'PARTIAL','L3':'BLOCKED','L4':'BLOCKED'})

    def test_mock_commit_and_actual_file_hash_mismatch(self):
        module='scripts.validate_tep_valve_transition_contract.subprocess.check_output'
        with patch(module,return_value='0'*40):
            with self.assertRaisesRegex(ValueError,'SOURCE_COMMIT_MISMATCH'):check_source(Path('unused'))
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ['simulator.py','python_backend.py','controllers.py','constants.py']:
                p=root/'src/tep'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('mock tampered file')
            with patch(module,side_effect=[PIN+'\n','']):
                with self.assertRaisesRegex(ValueError,'SOURCE_HASH_MISMATCH'):check_source(root)


if __name__=='__main__':unittest.main()
