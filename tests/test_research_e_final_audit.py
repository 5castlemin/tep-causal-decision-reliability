import unittest
from research.budget_adaptive_repair.final_audit import frontier, lower_envelope

class FinalAuditPureFunctionsTests(unittest.TestCase):
    def test_frontier_retains_coordinate_ties_and_drops_strictly_dominated(self):
        pts=[{'label':'a','cost':0.0,'loss':2.0},{'label':'b','cost':1.0,'loss':1.0},{'label':'b-tie','cost':1.0,'loss':1.0},{'label':'dominated','cost':2.0,'loss':2.0}]
        self.assertEqual({x['label'] for x in frontier(pts)},{'a','b','b-tie'})

    def test_lower_envelope_switches_only_at_actual_winner_transitions(self):
        pts=[{'label':'low-cost','cost':0.0,'loss':2.0},{'label':'mid','cost':1.0,'loss':1.0},{'label':'high-cost','cost':2.0,'loss':0.0},{'label':'dominated','cost':3.0,'loss':3.0}]
        intervals,winners,breaks=lower_envelope(pts)
        self.assertEqual([r['optimal_candidates'] for r in intervals],['high-cost','low-cost'])
        self.assertEqual([r['lambda_lo_inclusive'] for r in intervals],[0.0,1.0])
        self.assertEqual(breaks[0]['lambda_value'],1.0)
        self.assertEqual(set(breaks[0]['tied_optimal_candidates'].split(';')),{'high-cost','mid','low-cost'})
        self.assertEqual(winners,{'low-cost','mid','high-cost'})

if __name__=='__main__':unittest.main()
