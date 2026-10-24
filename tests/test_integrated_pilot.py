import json
import sys
import unittest
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from integrated_pilot import fit_model,recommend,structure_metrics


class IntegratedPilotTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/'research_runs/first_integrated_pilot/PLAN_v1.json').read_text(encoding='utf-8'))

    def test_unresolved_path_is_not_oriented_by_truth(self):
        m=structure_metrics({('R','Y'),('M','Y')},{frozenset(('R','A')),frozenset(('A','M'))},self.plan)
        self.assertEqual(m['skeleton_f1'],1)
        self.assertEqual(m['strict_directed_f1'],0.5)
        self.assertFalse(m['action_target_reachable'])
        self.assertEqual(m['unresolved_gt_pairs'],2)
        self.assertEqual(m['shd'],2)

    def test_direct_relation_is_distinct_from_reachability(self):
        m=structure_metrics({tuple(e) for e in self.plan['reference_edges']},set(),self.plan)
        self.assertTrue(m['action_target_reachable'])
        self.assertFalse(m['direct_xy_prediction'])
        self.assertTrue(m['direct_xy_correct'])

    def test_cycle_rejected_without_repair(self):
        data=np.random.default_rng(10).normal(size=(50,4))
        with self.assertRaises(ValueError):fit_model(data,['R','A','M','Y'],{('A','M'),('M','A')},0.001)

    def test_no_path_fallback_and_real_path_optimization(self):
        rng=np.random.default_rng(11);r=rng.normal(size=1000);a=2*r+rng.normal(size=1000)*.5
        m=3*a+rng.normal(size=1000);y=m+r+rng.normal(size=1000)*.25
        x=np.column_stack([r,a,m,y]);names=['R','A','M','Y']
        edges={tuple(e) for e in self.plan['reference_edges']}
        informative=recommend(fit_model(x,names,edges,.0001),edges,self.plan)
        fallback=recommend(fit_model(x,names,set(),.0001),set(),self.plan)
        self.assertEqual(informative['selected']['action'],.5)
        self.assertEqual(fallback['selected']['action'],0)
        self.assertEqual(fallback['status'],'NO_CONFIRMED_PATH_BASELINE_FALLBACK')

    def test_stored_experiment_raw_validation(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from validate_first_integrated_pilot import validate
        validate()


if __name__=='__main__':unittest.main()
