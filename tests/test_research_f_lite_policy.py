import inspect
from pathlib import Path
import sys
import unittest

import numpy as np

from research.decision_oriented_verification import policy as f
from research.decision_oriented_verification.run_f_lite import make_policy_view
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from integrated_pilot import fit_model
from decision_mvp import static_mean_response


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

    def test_score_components_and_decision_weighted_ablation(self):
        rng = np.random.default_rng(19)
        x = rng.normal(size=160)
        m = .8 * x + rng.normal(size=160) * .2
        y = .9 * m + rng.normal(size=160) * .2
        data = np.column_stack((x, m, y))
        nodes = ("X", "M", "Y")
        relations = {("M", "X"): ("X", "M")}
        kwargs = dict(data=data, nodes=nodes, action="X", target="Y",
                      action_values=(-1., -.5, 0., .5, 1.), target_value=1., scale=1.,
                      fit_model=fit_model, response=static_mean_response)
        rows = f.score_pairs("DECISION_WEIGHTED_VERIFICATION", relations=relations, **kwargs)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertGreaterEqual(row["suspicion"], 0.)
            self.assertLessEqual(row["suspicion"], 1.)
            self.assertGreaterEqual(row["decision_impact"], 0.)
            self.assertAlmostEqual(row["score"], row["suspicion"] * row["decision_impact"])

    def test_two_edge_path_synergy_is_missed_by_single_edge_impact(self):
        rng = np.random.default_rng(123)
        x = rng.normal(size=500)
        m = .8 * x + .1 * rng.normal(size=500)
        y = .9 * m + .1 * rng.normal(size=500)
        data = np.column_stack((x, m, y))
        args = (data, ("X", "M", "Y"), "X", "Y", (-1., 0., 1.), 0., 1., fit_model, static_mean_response)
        _, _, empty = f.predict_loss(*args[:2], {}, *args[2:])
        _, _, x_to_m = f.predict_loss(*args[:2], {("X", "M"): ("X", "M")}, *args[2:])
        _, _, m_to_y = f.predict_loss(*args[:2], {("M", "Y"): ("M", "Y")}, *args[2:])
        _, _, complete = f.predict_loss(*args[:2], {("X", "M"): ("X", "M"), ("M", "Y"): ("M", "Y")}, *args[2:])
        self.assertEqual(len(set(empty.values())), 1)
        self.assertEqual(empty, x_to_m)
        self.assertEqual(empty, m_to_y)
        self.assertGreater(max(complete.values()) - min(complete.values()), .01)

    def test_zero_impact_tie_still_queries_same_lexical_pair(self):
        rng = np.random.default_rng(222)
        x = rng.normal(size=120)
        m = rng.normal(size=120)
        y = rng.normal(size=120)
        data = np.column_stack((x, m, y))
        context = dict(data=data, nodes=("X", "M", "Y"), action="X", target="Y",
                       action_values=(-1., 0., 1.), target_value=0., scale=1.,
                       fit_model=fit_model, response=static_mean_response)
        first=[]
        for _ in range(2):
            state=f.VerificationState(("X","M","Y"),{})
            trace=f.query_once(state,"DECISION_IMPACT_ONLY",1,lambda p:f.NO_EDGE,score_context=context)
            first.append(trace[0]["pair"])
        self.assertEqual(first[0], ("M","X"))
        self.assertEqual(first[0], first[1])

    def test_policy_api_excludes_hidden_reference_and_outcomes(self):
        params = inspect.signature(f.query_once).parameters
        self.assertEqual(set(params), {"state", "policy", "budget", "expert", "score_context", "rng"})
        self.assertNotIn("truth", params)
        self.assertNotIn("gt_loss", params)
        self.assertNotIn("reference_graph", params)

    def test_same_visible_input_and_expert_transcript_ignore_hidden_truth(self):
        rng = np.random.default_rng(25)
        x = rng.normal(size=100)
        m = .5 * x + rng.normal(size=100)
        y = .7 * m + rng.normal(size=100)
        data = np.column_stack((x, m, y))
        nodes = ("X", "M", "Y")
        context = dict(data=data, nodes=nodes, action="X", target="Y",
                       action_values=(-1., 0., 1.), target_value=0., scale=1.,
                       fit_model=fit_model, response=static_mean_response)
        visible = {"nodes": nodes, "initial": {("M", "X"): ("M", "X")}}
        hidden_truth_a = {("M", "X"): ("M", "X")}
        hidden_truth_b = {("M", "X"): ("X", "M"), ("X", "Y"): ("X", "Y")}
        selected = []
        for hidden_truth in (hidden_truth_a, hidden_truth_b):
            state = f.VerificationState(visible["nodes"], dict(visible["initial"]))
            # The callback transcript is fixed and reveals only the queried pair's answer.
            trace = f.query_once(state, "SUSPICION_ONLY", 1,
                                 lambda pair: f.NO_EDGE, score_context=context)
            selected.append(trace[0]["pair"])
        self.assertEqual(selected[0], selected[1])

    def test_policy_view_is_allow_listed(self):
        record = {k: k for k in ("cohort", "scm_id", "nodes", "data", "initial", "action", "target",
                                  "actions", "target_value", "scale", "delta")}
        record.update({"truth": "secret", "truth_spec": "secret", "payload": "secret",
                       "reference": "secret", "gt_loss": 123, "corruption_log": "secret"})
        view = make_policy_view(record)
        self.assertEqual(set(view), {"cohort", "scm_id", "nodes", "data", "initial", "action", "target",
                                     "actions", "target_value", "scale", "delta"})
        self.assertNotIn("truth", view)
        self.assertNotIn("gt_loss", view)

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
