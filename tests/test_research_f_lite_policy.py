import inspect
import unittest

import numpy as np

from research.decision_oriented_verification import policy as f


class ResearchFLitePolicyTests(unittest.TestCase):
    def test_all_pairs_and_bic(self):
        nodes = ("X", "M", "Y")
        self.assertEqual(f.pair_order(nodes), [("M", "X"), ("M", "Y"), ("X", "Y")])
        rng = np.random.default_rng(4)
        x = rng.normal(size=200)
        m = 0.7 * x + rng.normal(size=200) * .2
        y = .8 * m + rng.normal(size=200) * .2
        data = np.column_stack([x, m, y])
        no_parent = f.bic_for_target(data, nodes, "Y", ())
        with_parent = f.bic_for_target(data, nodes, "Y", ("M",))
        self.assertLess(with_parent, no_parent)

    def test_graph_cycle_and_unresolved_omission(self):
        nodes = ("X", "M", "Y")
        g = {("X", "M"): ("X", "M"), ("M", "Y"): ("M", "Y")}
        self.assertTrue(f.graph_dag(nodes, g))
        self.assertFalse(f.graph_dag(nodes, {**g, ("X", "Y"): ("Y", "X")}))
        self.assertEqual(f.effective_relations({("X", "M"): f.UNRESOLVED}), {})

    def test_correct_and_absent_query_costs_and_duplicate_guard(self):
        nodes = ("X", "M", "Y")
        s = f.VerificationState(nodes, {("M", "X"): ("X", "M")})
        s.apply_answer(("M", "X"), f.V_TO_U)
        s.apply_answer(("M", "Y"), f.NO_EDGE)
        self.assertEqual(s.query_count, 2)
        self.assertEqual(s.edits, 0)
        with self.assertRaises(ValueError):
            s.apply_answer(("M", "X"), f.V_TO_U)

    def test_nonedge_add_and_direction_correction(self):
        nodes = ("X", "M", "Y")
        s = f.VerificationState(nodes, {("M", "X"): ("M", "X")})
        s.apply_answer(("M", "X"), f.V_TO_U)
        s.apply_answer(("M", "Y"), f.U_TO_V)
        self.assertTrue(f.graph_dag(nodes, s.relations))
        self.assertEqual(s.relations[("M", "X")], ("X", "M"))
        self.assertEqual(s.relations[("M", "Y")], ("M", "Y"))
        self.assertEqual(s.edits, 2)

    def test_pending_cycle_is_applied_after_blocker_query(self):
        nodes = ("A", "B", "C")
        s = f.VerificationState(nodes, {("A", "B"): ("A", "B"), ("B", "C"): ("B", "C")})
        # Expert confirms C->A, which is temporarily cyclic.
        s.apply_answer(("A", "C"), f.V_TO_U)
        self.assertIn(("A", "C"), s.pending)
        # Verifying B->C as absent breaks the cycle; pending relation is retried.
        s.apply_answer(("B", "C"), f.NO_EDGE)
        self.assertNotIn(("A", "C"), s.pending)
        self.assertEqual(s.relations[("A", "C")], ("C", "A"))
        self.assertTrue(f.graph_dag(nodes, s.relations))

    def test_pending_does_not_delete_unqueried_blocker(self):
        nodes = ("A", "B", "C")
        s = f.VerificationState(nodes, {("A", "B"): ("A", "B"), ("B", "C"): ("B", "C")})
        s.apply_answer(("A", "C"), f.V_TO_U)
        self.assertEqual(s.relations[("A", "B")], ("A", "B"))
        self.assertEqual(s.relations[("B", "C")], ("B", "C"))
        self.assertIn(("A", "C"), s.pending)

    def test_bic_weights_are_relative_not_probability_api(self):
        # log-sum-exp weights are computed in scoring, and policy API has no truth args.
        params = inspect.signature(f.score_pairs).parameters
        self.assertNotIn("truth", params)
        self.assertNotIn("reference", params)
        self.assertNotIn("evaluator", params)

    def test_zero_score_still_queries_deterministically(self):
        nodes = ("X", "Y")
        s = f.VerificationState(nodes, {})
        answers = []
        trace = f.query_once(s, "RANDOM_VERIFICATION", 1,
                             lambda p: answers.append(p) or f.NO_EDGE,
                             rng=np.random.default_rng(1))
        self.assertEqual(s.query_count, 1)
        self.assertEqual(len(trace), 1)


if __name__ == "__main__":
    unittest.main()
