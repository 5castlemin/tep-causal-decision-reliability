import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from decision_reliability_next import evaluate,match_pair,nested_cv,choose_response

class DecisionReliabilityTests(unittest.TestCase):
    def spec(self):return dict(nodes=['A','Y'],edges=[dict(source='A',target='Y',coefficient=2.)],noise_sd=dict(A=1.,Y=1.))
    def task(self):return dict(action='A',target='Y',target_value=.6,reference_action=0.,action_values=[-1.,-.5,0.,.5,1.],cost_weight=.2,loss_scale=1.)
    def test_improvement_and_regret_are_distinct(self):
        r=evaluate(self.spec(),self.task(),0.,0.,0.)
        self.assertEqual(r['improvement'],0);self.assertGreater(r['raw_regret'],0);self.assertTrue(r['effect_missed']);self.assertIsNone(r['direction_flip'])
    def test_zero_baseline_ratio_and_true_wrong_sign(self):
        r=evaluate(self.spec(),dict(self.task(),target_value=0.),.5,0.,-1.)
        self.assertIsNone(r['loss_ratio']);self.assertTrue(r['direction_flip']);self.assertTrue(r['worsened'])
    def test_skeleton_alone_does_not_match_direction_error(self):
        a=dict(dataset_id='a',task_id='t',policy='p',skeleton_f1=1.,strict_directed_f1=.8,added_pairs=0,missing_pairs=0,reversed_edges=1,unresolved_count=0,edge_count=5,shd=1)
        self.assertFalse(match_pair(a,dict(a,strict_directed_f1=1.,reversed_edges=0)))
    def test_outer_labels_cannot_select_inner_model(self):
        rows=[dict(structure_id=s,scale_normalized_regret=v) for s,v in [('a',1.),('b',2.),('c',3.)]]
        def dummy(train,test,features):return [sum(r['scale_normalized_regret'] for r in train)/len(train)]*len(test),{}
        with patch('decision_reliability_next.fit_predict',dummy):
            a=nested_cv(rows);b=nested_cv([dict(r,scale_normalized_regret=1000.) if r['structure_id']=='a' else r for r in rows])
        fa=next(f for f in a['folds'] if f['held_out']=='a');fb=next(f for f in b['folds'] if f['held_out']=='a')
        self.assertEqual(fa['inner_mae'],fb['inner_mae']);self.assertEqual(fa['selected'],fb['selected'])
    def test_actual_evidence_and_nested_replay(self):
        from validate_decision_reliability_next import validate
        validate()
if __name__=='__main__':unittest.main()
