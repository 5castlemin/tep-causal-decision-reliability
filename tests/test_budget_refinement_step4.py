import unittest
from research.budget_aware_refinement.step4_audit import audit

class Step4Audit(unittest.TestCase):
    def test_saved_records_and_cross_tab(self):
        a=audit();self.assertEqual(a['n'],456)
        self.assertEqual([(c['path'],c['positive_regret'],c['recommendation_changed'],c['prediction_changed'],c['n']) for c in a['cells']],[(False,True,False,False,248),(True,False,False,False,114),(True,False,True,True,94)])
        self.assertEqual((a['no_path_constant'],a['no_path_k0']),(248,248))
    def test_power_scenarios(self):
        t=audit()['normal_approximation']
        self.assertGreater(t[1]['bonferroni_two_sided_alpha_025_power'],.99)
        self.assertLess(t[3]['bonferroni_two_sided_alpha_025_power'],.42)
