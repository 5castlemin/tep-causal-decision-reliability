import itertools
import unittest

from research.original_objective import policy_engine as pe
from research.supplementary_validation.s7.task_zone_fast import task_zone_fast


class FastTaskZoneEquivalenceTests(unittest.TestCase):
    def test_exhaustive_all_four_node_dags(self):
        nodes=("A","B","C","D")
        pairs=list(itertools.combinations(nodes,2))
        checked=0
        for states in itertools.product((0,1,2),repeat=len(pairs)):
            directed=[]
            for (u,v),s in zip(pairs,states):
                if s==1:directed.append((u,v))
                elif s==2:directed.append((v,u))
            try:truth=pe.state(directed)
            except ValueError:continue
            for action,target in itertools.permutations(nodes,2):
                self.assertEqual(task_zone_fast(truth,action,target),pe.task_zone(truth,action,target))
                checked+=1
        self.assertGreater(checked,4000)

    def test_unresolved_estimate_classification_uses_same_zone(self):
        truth=pe.state([("A","B"),("C","B"),("B","D"),("A","E"),("E","D")])
        base,zone=pe.task_zone(truth,"A","D")
        fast,fast_nodes=task_zone_fast(truth,"A","D")
        self.assertEqual((fast,fast_nodes),(base,zone))
        g=pe.state([("A","B"),("B","D")],unresolved=[("C","D")])
        cfg=pe.Config()
        old=pe.task_zone
        try:
            before=pe.classify(truth,g,"A","D",cfg)
            pe.task_zone=task_zone_fast
            after=pe.classify(truth,g,"A","D",cfg)
        finally:
            pe.task_zone=old
        self.assertEqual(before,after)

    def test_disconnected_and_equal_task_edges(self):
        truth=pe.state([("A","B"),("C","D")])
        self.assertEqual(task_zone_fast(truth,"A","D"),pe.task_zone(truth,"A","D"))
        with self.assertRaises(ValueError):task_zone_fast(truth,"A","A")


if __name__=="__main__":unittest.main()
