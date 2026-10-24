"""Guards against reversed equations, orientation invention and invalid research joins."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('mvp',Path(__file__).resolve().parents[1]/'src/decision_mvp.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    # Explicit synthetic software fixture, never TEP evidence.
    return dict(scaler_mean={'A':0,'B':0,'C':0},scaler_std={'A':1,'B':1,'C':1},equations=[
        dict(target='C',intercept_standardized=0,parents=[dict(source='B',lag=0,coefficient_standardized=3)]),
        dict(target='A',intercept_standardized=9,parents=[]),
        dict(target='B',intercept_standardized=1,parents=[dict(source='A',lag=0,coefficient_standardized=2)])])


class MVPTests(unittest.TestCase):
    def test_do_cuts_equation_and_respects_order(self):
        r=m.static_mean_response(fixture(),'A',2)
        self.assertEqual(r['C'],15)
        self.assertEqual(r['A'],2)

    def test_unresolved_or_missing_path_is_not_invented(self):
        t=dict(task_id='toy',action='A',target='C',gt_path=[['A','B','C']])
        r=m.task_metrics(t,{('A','B')},{('A','B'),('B','C')})
        self.assertEqual(r['gt_path_edge_recall'],0.5)
        self.assertFalse(r['confirmed_action_target_reachable'])

    def test_same_label_without_approvals_cannot_open_research_gate(self):
        with self.assertRaises(ValueError):m.require_research_environment('same','same',{})

    def test_unresolved_pair_is_not_a_correct_absence(self):
        t=dict(task_id='toy',action='A',target='C',gt_path=[['A','B','C']])
        r=m.task_metrics(t,{('A','B')},{('A','B'),('B','C')},{frozenset(('A','C'))})
        self.assertEqual(r['direct_xy_state'],'UNRESOLVED')
        self.assertIsNone(r['direct_xy_correct'])

    def test_different_environments_cannot_join_even_with_flags(self):
        flags={k:True for k in ['model_controller_identity','variable_intervention_alignment','reference_structure_valid','independent_evaluation_contract']}
        with self.assertRaises(ValueError):m.require_research_environment('benchmark','other',flags)

    def test_cycle_is_not_repaired(self):
        a=fixture();a['equations'][1]['parents']=[dict(source='C',lag=0,coefficient_standardized=1)]
        with self.assertRaises(ValueError):m.static_mean_response(a,'A',0)

    def test_action_bounds_are_enforced(self):
        with self.assertRaises(ValueError):m.recommend_grid(fixture(),'A','C',[1],0)
