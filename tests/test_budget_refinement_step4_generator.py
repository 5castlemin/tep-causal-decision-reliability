import unittest

from research.budget_aware_refinement.step4_topology_generator import (
    TEMPLATES, classify_tasks, directed_paths, generate_topology, is_dag,
)
from research.budget_aware_refinement.step4_error_injection import (
    classify_errors, inject_condition, policy_opportunities,
)


class Step4TopologyGeneratorTests(unittest.TestCase):
    def test_reproducible_and_id_order_independent(self):
        a = generate_topology(8, "multiple_directed_paths", 41)
        b = generate_topology(8, "multiple_directed_paths", 41)
        self.assertEqual(a, b)
        self.assertEqual(a.nodes, tuple(sorted(a.nodes)))

    def test_all_templates_dag_parent_bound_and_tasks(self):
        for n in range(6, 11):
            for template in TEMPLATES:
                with self.subTest(n=n, template=template):
                    g = generate_topology(n, template, 2026)
                    self.assertTrue(is_dag(g.topological_order, g.edges))
                    self.assertLessEqual(max(sum(v == node for _, v in g.edges) for node in g.nodes), 3)
                    direct, indirect = classify_tasks(g.nodes, g.edges)
                    self.assertTrue(direct)
                    self.assertTrue(indirect)
                    self.assertTrue(all((t.action, t.target) in g.edges for t in direct))
                    self.assertTrue(all(any(len(p) >= 3 for p in directed_paths(g.nodes, g.edges, t.action, t.target)) for t in indirect))

    def test_density_is_lower_bound_when_motif_requires_more(self):
        g = generate_topology(6, "chain_mediation", 0, density=(.2, .2))
        self.assertGreaterEqual(len(g.edges), g.target_edge_count)
        self.assertEqual(g.target_edge_count, 5)  # scaffold has priority over rounded density 3

    def test_invalid_inputs_report_specific_error(self):
        for args, match in [((5, "chain_mediation", 1), "n_nodes"),
                            ((6, "unknown", 1), "unknown template"),
                            ((6, "chain_mediation", "1"), "seed")]:
            with self.subTest(args=args), self.assertRaisesRegex(ValueError, match):
                generate_topology(*args)


class Step4ErrorInjectionTests(unittest.TestCase):
    def setUp(self):
        self.g = generate_topology(8, "multiple_directed_paths", 19)
        self.x, self.y = self.g.topological_order[0], self.g.topological_order[-1]

    def test_A_disconnects_all_paths_with_fn_cut(self):
        r = inject_condition(self.g.nodes, self.g.edges, self.x, self.y, "A_path_disconnected")
        self.assertTrue(r.accepted, r.reason)
        self.assertFalse(r.remaining_paths)
        self.assertTrue(is_dag(self.g.nodes, r.initial_edges))
        self.assertTrue(r.errors)
        self.assertEqual({x[0] for x in r.errors}, {"FN"})

    def test_B_reports_path_preserving_recipe_infeasible_for_this_seed(self):
        r = inject_condition(self.g.nodes, self.g.edges, self.x, self.y, "B_path_survives")
        self.assertFalse(r.accepted)
        self.assertEqual(r.reason, "no_dag_path_preserving_fn_fp_rev_recipe")
        self.assertTrue(r.cycle_rejections)

    def test_classifier_does_not_double_count_reverse(self):
        truth = {("a", "b")}; initial = {("b", "a")}
        self.assertEqual(classify_errors(("a", "b"), truth, initial), (("REV", "b", "a"),))

    def test_impossible_path_preserving_case_is_explicit(self):
        g = generate_topology(6, "chain_mediation", 5)
        x, y = g.topological_order[0], g.topological_order[-1]
        r = inject_condition(g.nodes, g.edges, x, y, "B_path_survives")
        self.assertFalse(r.accepted)
        self.assertIn("no_dag_path_preserving", r.reason)


if __name__ == "__main__":
    unittest.main()
