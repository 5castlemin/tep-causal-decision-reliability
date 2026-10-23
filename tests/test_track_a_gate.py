"""Prevent promotion of documentation/static metadata into execution evidence."""
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/track_a_gate.py'
spec=importlib.util.spec_from_file_location('track_a_gate',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def blocked():
    return dict(raw_data={k:False for k in ['acquired','timestamp_acquired','seed_acquired','export_reproduced','configuration_matched']},
                execution_environment={k:False for k in ['matlab_invocable','simulink_available','license_available','model_load_verified','mex_compatible']},
                normal_runs=[],repeatability_verified=False,intervention_interface_verified=False)


class GateTests(unittest.TestCase):
    def test_documented_filename_is_not_acquired_data(self):
        e=blocked();e['documented_files']=['SIMOUT.xlsx','TOUT.xlsx','random_seed.txt']
        self.assertEqual(module.evaluate(e)['A1'],'BLOCKED')

    def test_run_claim_requires_execution_gate(self):
        e=blocked();e['normal_runs']=['log1','log2'];e['repeatability_verified']=True
        with self.assertRaises(ValueError):module.evaluate(e)

    def test_matching_normal_runs_do_not_establish_effect_interface(self):
        e=blocked();e['raw_data']={k:True for k in e['raw_data']};e['execution_environment']={k:True for k in e['execution_environment']}
        e['normal_runs']=['log1','log2'];e['repeatability_verified']=True
        self.assertEqual(module.evaluate(e)['A4'],'NO-GO')
