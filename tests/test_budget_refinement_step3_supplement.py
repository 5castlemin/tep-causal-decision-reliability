import unittest
from research.budget_aware_refinement.step3_supplement import validate
from research.budget_aware_refinement.step3_adapter import evaluate

class Supplement(unittest.TestCase):
    def test_prior_data_and_mixed_dags(self):
        self.assertEqual(len(validate()),4)
    def test_regret_sensitivity_independent_linear_formula(self):
        # E[Y|do(A=a)]=2a; target 2; candidate 0 is wrong, 1 optimal.
        sel=dict(action='A',target_node='Y',target=2.,sd_y=1.,candidates=[dict(k=0.,action=0.),dict(k=1.,action=1.)],selected_k=0.)
        result=evaluate(sel,{},lambda spec,action,value:{'Y':2*value})
        self.assertEqual(result['regret'],4.)
        sel['selected_k']=1.
        self.assertEqual(evaluate(sel,{},lambda spec,action,value:{'Y':2*value})['regret'],0.)
