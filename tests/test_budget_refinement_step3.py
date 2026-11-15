import pathlib
import sys
import unittest
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT))
from research.budget_aware_refinement.step3_adapter import prepare,evaluate
from integrated_pilot import fit_model
from decision_mvp import static_mean_response
from diverse_structure_pilot import analytic_response

class Step3(unittest.TestCase):
    def setUp(self):
        self.data=np.array([[0.,0.,1.],[1.,2.,3.],[2.,4.,7.],[3.,6.,9.]])
        self.spec={'nodes':['A','B','Y'],'edges':[{'source':'A','target':'B','coefficient':2.},{'source':'B','target':'Y','coefficient':3.}]}
        self.req=dict(node_ids=['A','B','Y'],initial_edges=[('A','B')],reference_edges=[('A','B'),('B','Y')],allowed_types=['FN'],policy_id='G-FN',budget=1,gamma=1,action='A',target='Y',seed=0)
    def prepare(self):return prepare(self.req,self.data,['A','B','Y'],['A','B','Y'],1,fit_model,static_mean_response)
    def test_independent_analytic(self):
        self.assertEqual(analytic_response(self.spec,'A',2)['Y'],12)
        graph,selection=self.prepare(); result=evaluate(selection,self.spec,analytic_response)
        self.assertGreaterEqual(result['regret'],0)
        row=next(x for x in result['truth'] if x['k']==selection['selected_k'])
        self.assertAlmostEqual(row['loss']-min(x['loss'] for x in result['truth']),result['regret'])
    def test_true_coefficients_cannot_affect_selection(self):
        graph,a=self.prepare(); altered=dict(self.spec,edges=[dict(e,coefficient=e['coefficient']*2) for e in self.spec['edges']])
        before=evaluate(a,self.spec,analytic_response); graph2,b=self.prepare(); after=evaluate(b,altered,analytic_response)
        self.assertEqual(graph,graph2);self.assertEqual(a,b);self.assertNotEqual(before['truth'],after['truth'])
    def test_schema_and_nonfinite(self):
        with self.assertRaises(ValueError):prepare(self.req,self.data,['Y','B','A'],['A','B','Y'],1,fit_model,static_mean_response)
        data=self.data.copy();data[0,0]=np.nan
        with self.assertRaises(ValueError):prepare(self.req,data,['A','B','Y'],['A','B','Y'],1,fit_model,static_mean_response)
    def test_no_path_and_tie(self):
        req=dict(self.req,initial_edges=[],reference_edges=[],policy_id='NO-EDIT')
        graph,s=prepare(req,self.data,['A','B','Y'],['A','B','Y'],1,fit_model,static_mean_response)
        self.assertEqual(s['selected_k'],0.0)
        self.assertEqual(len({r['predicted_loss'] for r in s['candidates']}),1)
    def test_boundary_rejects_truth_payload(self):
        req=dict(self.req,truth_spec=self.spec)
        with self.assertRaises(ValueError):prepare(req,self.data,['A','B','Y'],['A','B','Y'],1,fit_model,static_mean_response)
    def test_learner_receives_only_edges_and_data(self):
        def spy(data,names,edges,alpha):
            self.assertEqual(set(names),{'A','B','Y'});self.assertIsInstance(edges,set)
            self.assertTrue(all(isinstance(e,tuple) and len(e)==2 for e in edges))
            return fit_model(data,names,edges,alpha)
        prepare(self.req,self.data,['A','B','Y'],['A','B','Y'],1,spy,static_mean_response)
