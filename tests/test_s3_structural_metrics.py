import unittest

from research.within_task_repair_prioritization.s3_analysis import GAIN_TOL, SETS, ancestors, path_edges, q_metrics, select_greedy_option, structural_sets
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

    def test_ancestor_closure_traverses_multiple_out_of_zone_nodes_and_parallel_paths(self):
        g = pe.state([("X", "U"), ("U", "V"), ("V", "Y"),
                      ("X", "W"), ("W", "Y"), ("Q", "R")])
        # Independent source-to-target traversal on the full DAG.
        def reachable(source, target):
            stack = [source]
            seen = set()
            while stack:
                node = stack.pop()
                if node == target:
                    return True
                if node in seen:
                    continue
                seen.add(node)
                stack.extend(v for u, v in g.values() if u == node)
            return False
        closure = ancestors(g, {"X", "Y"})
        self.assertEqual(closure["X"], {"U", "V", "W", "Y"})
        self.assertEqual(closure["Q"], {"R"})
        for a in {"X", "Y", "Q", "R"}:
            for b in {"X", "Y", "Q", "R"} - {a}:
                self.assertEqual(b in closure[a], reachable(a, b))

    def test_ancestor_closure_ignores_unresolved_and_does_not_invent_paths(self):
        g = pe.state([("X", "M"), ("N", "Y")], unresolved=[("M", "Y")])
        closure = ancestors(g, {"X", "Y", "ISOLATED"})
        self.assertEqual(closure["X"], {"M"})
        self.assertNotIn("Y", closure["X"])
        self.assertEqual(closure["ISOLATED"], set())

    def test_greedy_selector_uses_m4_secondary_then_canonical_order_with_tolerance(self):
        e_m1 = pe.Edit("M1", "FN", ("A", "B"), "add", ("A", "B"))
        e_m4 = pe.Edit("M4", "FN", ("C", "D"), "add", ("C", "D"))
        costs = {"add": 1.0}
        chosen, fallback = select_greedy_option([
            (e_m1, {}, 0.5, 0.1),
            (e_m4, {}, 0.5 + GAIN_TOL / 2, 0.8),
        ], costs)
        self.assertIs(chosen[0], e_m4)
        self.assertFalse(fallback)
        chosen, fallback = select_greedy_option([
            (e_m4, {}, 0.5, 0.2),
            (e_m1, {}, 0.5, 0.2),
        ], costs)
        self.assertIs(chosen[0], e_m1)
        self.assertFalse(fallback)
        chosen, fallback = select_greedy_option([(e_m1, {}, 0.0, 0.5)], costs)
        self.assertIs(chosen[0], e_m1)
        self.assertTrue(fallback)
        self.assertEqual(select_greedy_option([(e_m1, {}, 0.0, 0.0)], costs), (None, True))


if __name__ == "__main__":
    unittest.main()
