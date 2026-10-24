import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from independent_confirmation import predict_frozen,clustered_comparison,select_controls
from diverse_metric_analysis import weighted_predict
from diverse_structure_pilot import all_paths

class ConfirmationTests(unittest.TestCase):
    def test_saved_confirmation_contract(self):
        if not (ROOT/'research_runs/independent_confirmation/analysis_v1/SUMMARY.json').exists():
            self.skipTest('confirmation sampling not started; stored evidence check runs after completion')
        sys.path.insert(0,str(ROOT/'scripts'))
        from validate_independent_confirmation import validate
        validate()
    def test_relabelled_near_duplicate_structure_is_rejected(self):
        import networkx as nx
        sys.path.insert(0,str(ROOT/'scripts'))
        from prepare_independent_confirmation import near_same
        a=nx.DiGraph([('A','B'),('B','C'),('C','D')]);b=nx.DiGraph([('W','X'),('X','Y'),('Y','Z'),('W','Y')])
        self.assertTrue(near_same(a,b))
    def test_frozen_predictor_matches_original_and_cannot_read_outcomes(self):
        train=[dict(structure_id='S1',skeleton_f1=.1,scale_normalized_regret=1),dict(structure_id='S2',skeleton_f1=.9,scale_normalized_regret=0)]
        test=[dict(skeleton_f1=.4,scale_normalized_regret=-100)]
        p,m=weighted_predict(train,test,['skeleton_f1'],.01)
        self.assertAlmostEqual(p[0],predict_frozen(m,test)[0]);test[0]['scale_normalized_regret']=999
        self.assertAlmostEqual(p[0],predict_frozen(m,test)[0])
    def test_cluster_bootstrap_counts_structures_not_rows(self):
        rows=[dict(structure_id=s,graph_id=s,task_id='x',scale_normalized_regret=v) for s,v in [('C1',0),('C2',2),('C3',4)]]
        m=dict(features=[],feature_imputations=[],feature_means=[],feature_scales=[],coefficients_standardized=[],outcome_mean=0,outcome_scale=1)
        models={k:m for k in ['M0','M1','M2','M3','M4_incremental']}
        a=clustered_comparison(rows,models,b=100)
        b=clustered_comparison(rows+[rows[0]]*20,models,b=100)
        self.assertEqual(a['macro_mae'],b['macro_mae']);self.assertEqual(a['paired'],b['paired'])
        self.assertEqual(a['judgment'],'INCONCLUSIVE')
    def test_retained_path_error_pair_is_structural_not_learned(self):
        spec=dict(nodes=['A','B','C','Y','S','T'],edges=[dict(source=a,target=b,coefficient=1.) for a,b in [('A','B'),('B','Y'),('A','C'),('C','Y'),('S','T')]],tasks=[dict(task_id='path',action='A',target='Y')])
        variants,notes=select_controls(spec)
        for k in ['remove_key_path_retained','remove_peripheral_path_retained']:
            self.assertTrue(all_paths(set(map(tuple,variants[k])),'A','Y'))
        self.assertEqual(len(variants['remove_key_path_retained']),len(variants['remove_peripheral_path_retained']))
    def test_no_redundant_path_is_not_applicable_not_silent_exclusion(self):
        spec=dict(nodes=['A','B','Y'],edges=[dict(source=a,target=b,coefficient=1.) for a,b in [('A','B'),('B','Y')]],tasks=[dict(task_id='path',action='A',target='Y')])
        variants,notes=select_controls(spec)
        self.assertTrue(any(r.get('status')=='NOT_APPLICABLE' for r in notes))
if __name__=='__main__':unittest.main()
