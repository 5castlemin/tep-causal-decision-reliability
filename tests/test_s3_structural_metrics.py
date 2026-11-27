import unittest

from research.within_task_repair_prioritization.s3_analysis import SETS, ancestors, path_edges, q_metrics, structural_sets
from research.original_objective import policy_engine as pe


class S3MetricTests(unittest.TestCase):
    def test_all_63_nonempty_subsets_are_unique_and_bounded(self):
        self.assertEqual(len(SETS), 63)
        self.assertEqual(len(set(SETS)), 63)
        self.assertTrue(all(1 <= len(s) <= 6 for s in SETS))

    def test_path_edges_and_indirect_reachability_through_intermediate_nodes(self):
        g = pe.state([("X", "M"), ("M", "Y")])
        self.assertEqual(path_edges(g, "X", "Y"), {("X", "M"), ("M", "Y")})
        self.assertIn("Y", ancestors(g, {"X", "Y"})["X"])

    def test_metrics_are_bounded_and_recover_complete_reference_path(self):
        truth = pe.state([("X", "M"), ("M", "Y")])
        partial = pe.state([("X", "M")])
        nodes, zone, p_edges, bd_edges = structural_sets(truth, "X", "Y", pe.Config())
        q = q_metrics(partial, (truth, "X", "Y", nodes, zone, p_edges, bd_edges))
        self.assertEqual(set(q), {"T1", "T2", "T3", "T4", "T5", "T6"})
        self.assertTrue(all(0.0 <= v <= 1.0 for v in q.values()))
        self.assertEqual(q["T3"], 0.5)
        self.assertEqual(q["T4"], 0.0)

    def test_zero_path_and_backdoor_support_are_finite_zero(self):
        truth = pe.state([("Z", "X"), ("Z", "Y")])
        g = dict(truth)
        nodes, zone, p_edges, bd_edges = structural_sets(truth, "X", "Y", pe.Config())
        q = q_metrics(g, (truth, "X", "Y", nodes, zone, p_edges, bd_edges))
        self.assertEqual(q["T3"], 0.0)
        self.assertEqual(q["T6"], 1.0)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in q.values()))


if __name__ == "__main__":
    unittest.main()
