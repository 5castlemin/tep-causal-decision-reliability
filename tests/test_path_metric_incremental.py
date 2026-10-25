import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_metric_incremental import linear_moments,loss_contract,task_features,precision_gate,MODELS

class IncrementalTests(unittest.TestCase):
    def test_recorded_operational_analysis_and_actual_do_evidence(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from validate_path_metric_incremental import validate
        validate()
    def spec(self):return dict(nodes=['A','M','Y'],edges=[dict(source=a,target=b,coefficient=c) for a,b,c in [('A','M',2.),('M','Y',3.),('A','Y',-1.)]],noise_sd=dict(A=1.,M=1.,Y=1.))
    def task(self):return dict(action='A',target='Y',target_value=.65,reference_action=0.,action_values=[-1.,-.5,0.,.5,1.],cost_weight=.2,loss_scale=1.)
    def test_independent_matrix_mean_and_variance(self):
        m,v=linear_moments(self.spec(),'A',.5);self.assertAlmostEqual(m['Y'],2.5);self.assertAlmostEqual(v['Y'],10.)
    def test_failure_reference_is_real_loss_not_zero_imputation(self):
        c=loss_contract(self.spec(),self.task(),0.)
        self.assertAlmostEqual(c['analytic_loss'],.65**2);self.assertEqual(c['analytic_regret'],0.)
        self.assertAlmostEqual(loss_contract(self.spec(),self.task(),1.)['analytic_regret'],18.7)
    def test_features_forbid_oracle_and_ignore_variable_names(self):
        import pandas as pd
        x=pd.DataFrame(dict(A=[0.,1.,2.],M=[.1,.5,2.],Y=[1.,3.,2.]))
        graph=dict(confirmed_edges=[['A','M'],['M','Y']],unresolved_pairs=[])
        a=task_features(x,graph,None,self.task(),'confirmed_only',False)
        mapping=dict(A='other1',M='other2',Y='other3');b=task_features(x.rename(columns=mapping),dict(confirmed_edges=[[mapping[z] for z in e] for e in graph['confirmed_edges']],unresolved_pairs=[]),None,dict(self.task(),action='other1',target='other3'),'confirmed_only',False)
        self.assertEqual(a,b)
        with self.assertRaises(AssertionError):task_features(x,graph,None,dict(self.task(),oracle_total_effect=5.),'confirmed_only',False)
        self.assertFalse(any(k.startswith('oracle') or k in {'recommended_action','actual_loss','task_kind'} for k in a))
    def test_precision_can_block_computation(self):
        design=dict(planning=dict(desired_95_interval_halfwidth=.005,independent_structure_min=18,max_structures=30,replicates=3,algorithms=3,max_learning_calls=288,practical_increment=.01))
        scores=[]
        for i in range(20):
            for m in MODELS:scores.append(dict(structure_id='S'+str(i),model=m,mae=(1.+(-1)**i*.5 if m in {'M1','M5'} else 1.)))
        r=precision_gate(dict(structure_scores=scores),design)
        self.assertEqual(r['status'],'BLOCKED_PRECISION_RESOURCE');self.assertEqual(r['new_reference_structures_generated'],0)
if __name__=='__main__':unittest.main()
