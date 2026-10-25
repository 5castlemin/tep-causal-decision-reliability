import itertools
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from integrated_pilot import fit_model
from repeated_metric_pilot import consistent_extensions,colliders,acyclic,recommend_policy,quality,spearman


class RepeatedMetricTests(unittest.TestCase):
    def test_chain_extensions_exclude_new_collider(self):
        unknown={frozenset(('A','B')),frozenset(('B','C'))}
        result=consistent_extensions(['A','B','C'],set(),unknown,{})
        self.assertEqual(len(result),3)
        self.assertNotIn({('A','B'),('C','B')},result)
        self.assertTrue(all(acyclic(['A','B','C'],e) for e in result))

    def test_given_collider_cannot_be_reoriented(self):
        edges={('A','B'),('C','B')};out=consistent_extensions(['A','B','C'],edges,set(),{})
        self.assertEqual(out,[edges])

    def test_extensions_match_independent_permutation_enumeration(self):
        nodes=['R','A','M','Y'];fixed={('R','Y'),('M','Y')};unknown={frozenset(('R','A')),frozenset(('A','M'))}
        pairs={frozenset(e) for e in fixed}|unknown;expected=set()
        for order in itertools.permutations(nodes):
            index={v:i for i,v in enumerate(order)}
            edges={tuple(sorted(p,key=index.get)) for p in pairs}
            if fixed<=edges and colliders(edges,pairs)==colliders(fixed,pairs):expected.add(frozenset(edges))
        actual=consistent_extensions(nodes,fixed,unknown,{})
        self.assertEqual({frozenset(e) for e in actual},expected)

    def test_invalid_endpoint_and_cycle_fail(self):
        with self.assertRaises(ValueError):consistent_extensions(['A','B'],set(),{frozenset(('A','B'))},{'native_edges':[dict(endpoint1='ARROW',endpoint2='ARROW')]})
        with self.assertRaises(ValueError):consistent_extensions(['A','B'],{('A','B'),('B','A')},set(),{})

    def test_abstention_and_computed_baseline_differ(self):
        rng=np.random.default_rng(10);a=rng.normal(size=500);b=2*a+rng.normal(size=500)*.1;x=np.column_stack([a,b])
        edges=[{('A','B')},{('B','A')}];models=[fit_model(x,['A','B'],e,.0001) for e in edges]
        task=dict(action='A',target='B',target_value=1)
        p=dict(action_values=[0.,.5,1.],reference_action=0.,cost_weight=.2)
        abstain=recommend_policy(models,edges,task,p,'abstain_on_disagreement')
        self.assertEqual(abstain['status'],'AMBIGUITY_ABSTENTION')
        self.assertEqual(abstain['selected']['action'],0)
        computed=recommend_policy([models[0]],[edges[0]],dict(task,target_value=0),p,'confirmed_only')
        self.assertEqual(computed['status'],'COMPUTED_BASELINE')

    def test_direct_edge_not_indirect_reachability_and_f1_denominators(self):
        task=dict(task_id='A_Y',action='A',target='Y',key_paths=[['A','M','Y']])
        ref=[['R','A'],['A','M'],['M','Y'],['R','Y']]
        result=quality({('M','Y'),('R','Y')},{frozenset(('R','A')),frozenset(('A','M'))},ref,task)
        self.assertEqual(result['strict_directed_f1'],.5)
        self.assertAlmostEqual(result['confirmed_directed_f1'],2/3)
        self.assertEqual(result['orientation_rate'],.5)
        self.assertEqual(result['direct_xy_state'],'ABSENT')
        self.assertFalse(result['action_target_reachable'])

    def test_rank_ties_and_constant(self):
        self.assertAlmostEqual(spearman([1,2,2,3],[4,2,2,1]),-1)
        self.assertIsNone(spearman([1,1],[0,1]))

    def test_saved_raw_and_policies(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from validate_repeated_metric_pilot import validate
        validate()


if __name__=='__main__':unittest.main()
