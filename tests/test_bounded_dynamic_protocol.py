"""Minimal schema regression checks, not tests of physical/causal validity."""
from copy import deepcopy
import unittest
from scripts.validate_bounded_dynamic_protocol import BASE,load,validate_proposal


class BoundedProtocolTests(unittest.TestCase):
    def setUp(self):
        self.p=load(BASE/'PROTOCOL.json');self.d=load(BASE/'DECISION.json')

    def test_current_review_proposal_is_not_execution_or_gt(self):
        r=validate_proposal(self.p,self.d)
        self.assertEqual(r['scientific_judgment'],2)
        self.assertFalse(r['execution_allowed'])

    def test_cherry_picked_or_duplicate_pair_universe_rejected(self):
        for pairs in [self.p['finite_comparison_design']['universe'][:2],
                      self.p['finite_comparison_design']['universe']+[self.p['finite_comparison_design']['universe'][0]]]:
            p=deepcopy(self.p);p['finite_comparison_design']['universe']=pairs
            with self.assertRaises(AssertionError):validate_proposal(p,self.d)

    def test_conditional_exclusion_cannot_be_promoted_to_negative(self):
        self.p['finite_comparison_design']['justified_negative_pairs_for_discovery']=[['E','v',1]]
        with self.assertRaises(AssertionError):validate_proposal(self.p,self.d)

    def test_endogenous_boundary_cannot_be_silently_exogenous(self):
        self.p['boundaries'][0]['exogenous']=True
        with self.assertRaises(AssertionError):validate_proposal(self.p,self.d)

    def test_scoring_execution_or_adoption_promotion_rejected(self):
        for section,key in [('authorization','execution_allowed'),('authorization','environment_adopted'),
                            ('scoring_gate','structure_scoring_allowed'),('scoring_gate','parent_closure_verified')]:
            p=deepcopy(self.p);p[section][key]=True
            with self.assertRaises(AssertionError):validate_proposal(p,self.d)

    def test_alternative_judgment_or_ready_task_cannot_hide_blockers(self):
        d=deepcopy(self.d);d['requested_judgment']=1
        with self.assertRaises(AssertionError):validate_proposal(self.p,d)
        self.p['decision_task']['status']='READY'
        with self.assertRaises(AssertionError):validate_proposal(self.p,self.d)


if __name__=='__main__':unittest.main()
