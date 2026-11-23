"""Independent hand-calculated counterexamples for the Research C engine.

These tests use only explicit graph states. They do not generate SCMs,
observations, interventions, or Decision Regret outcomes.
"""
import inspect
import unittest

from research.original_objective.policy_engine import (
    Config, UNRES, candidates, dag, graph_hash, metrics, run, state,
)


class IndependentPolicyEngineAuditTests(unittest.TestCase):
    def test_multiple_same_metric_candidates_choose_canonical_equal_score(self):
        truth = state([("A", "B"), ("C", "D")])
        estimate = state()
        result = run(truth, estimate, "X", "Y", 1, ("M1",))

        # Two M1 misses, two opportunities: either repair has gain 1/2.
        # The documented deterministic pair ordering selects A-B.
        self.assertEqual(len(candidates(truth, estimate, "X", "Y", Config())), 2)
        self.assertEqual(result["edits"][0]["pair"], ("A", "B"))
        self.assertAlmostEqual(result["edits"][0]["score"], 0.5)
        self.assertEqual(result["total_cost"], 1)
        self.assertTrue(dag(state([("A", "B")])) )

    def test_m4_all_four_active_components_have_equal_active_mass(self):
        truth = state([("X", "M"), ("M", "Y"), ("Z", "X"), ("Z", "Y")])
        estimate = state([("M", "X"), ("Z", "Y"), ("X", "Y")], unresolved=[("Z", "X")])
        before = metrics(truth, estimate, "X", "Y", Config())
        self.assertEqual(before["counts"]["M4"], {"FN": 1, "FP": 1, "REV": 1, "UNRES": 1})

        result = run(truth, estimate, "X", "Y", 1, ("M4",))
        # Active components are equally re-normalized. REV has support 2,
        # so its event repair gains (1/2)/4 = 1/8; FN support is 4 and gains
        # (1/4)/4 = 1/16. Thus the score must choose REV despite its pair order.
        self.assertEqual(result["edits"][0]["error_type"], "REV")
        self.assertAlmostEqual(result["edits"][0]["score"], 1 / 8)

    def test_normalization_counterexample_reverses_selected_metric(self):
        off = [(f"O{i}", f"P{i}") for i in range(10)]
        task = [("X", "M"), ("M", "Y"), ("X", "Y")]
        truth = state(off + task)
        estimate = state(off[1:] + [("X", "Y")])

        error_count = run(truth, estimate, "X", "Y", 1, ("M1", "M4"),
                          Config(normalization="initial_error_count"))
        fixed = run(truth, estimate, "X", "Y", 1, ("M1", "M4"),
                    Config(normalization="fixed_opportunity"))

        # Hand arithmetic: M1 1/1 vs M4 1/2 => M1; fixed opportunities
        # M1 1/10 vs M4 1/3 => M4.
        self.assertEqual(error_count["edits"][0]["metric"], "M1")
        self.assertAlmostEqual(error_count["edits"][0]["score"], 0.5)
        self.assertEqual(fixed["edits"][0]["metric"], "M4")
        self.assertAlmostEqual(fixed["edits"][0]["score"], 1 / 6)

    def test_high_gain_candidate_over_budget_is_not_charged_or_applied(self):
        truth = state([("A", "B")])
        estimate = state()
        result = run(truth, estimate, "X", "Y", 1, ("M1",),
                     Config(costs=(("add", 2), ("delete", 1), ("orient", 1),
                                   ("resolve", 1), ("delete_unresolved", 1))))
        self.assertEqual(result["edits"], [])
        self.assertEqual(result["total_cost"], 0)
        self.assertEqual(result["unused_budget"], 1)
        self.assertEqual(result["stop_reason"], "no_feasible_candidate")

    def test_cycle_candidate_is_rejected_without_cost_then_safe_candidate_runs(self):
        truth = state([("Y", "X"), ("A", "B")])
        estimate = state([("X", "C"), ("C", "Y")])
        result = run(truth, estimate, "Q", "R", 2, ("M1",))

        # Adding Y->X closes X->C->Y->X. The A->B repair remains feasible.
        # The same still-feasible-to-consider candidate is rechecked on the
        # next scheduling pass, so the diagnostic is a rejection-attempt count.
        self.assertEqual(result["dag_rejects"], 2)
        self.assertEqual(result["edits"][0]["pair"], ("A", "B"))
        self.assertEqual(result["total_cost"], 1)
        self.assertEqual(result["stop_reason"], "dag_invalid_candidate")
        final = state(result["final_edges"])
        self.assertTrue(dag(final))

    def test_distinct_metric_subsets_can_have_same_final_graph(self):
        truth = state([("X", "M"), ("M", "Y"), ("T", "U")])
        estimate = state([("X", "M"), ("M", "Y")])
        m1 = run(truth, estimate, "X", "Y", 1, ("M1",))
        all_metrics = run(truth, estimate, "X", "Y", 1, ("M1", "M2", "M3", "M4"))
        self.assertEqual(m1["final_hash"], all_metrics["final_hash"])
        self.assertEqual(m1["final_hash"], graph_hash(state([("X", "M"), ("M", "Y"), ("T", "U")])) )

    def test_policy_api_has_no_gt_outcome_input_and_keeps_outcome_fields_empty(self):
        signature = inspect.signature(run)
        self.assertEqual(set(signature.parameters),
                         {"truth", "estimate", "action", "target", "budget", "subset", "config", "canonical"})
        truth = state([("X", "M"), ("M", "Y"), ("T", "U")])
        estimate = state([("X", "M"), ("M", "Y")])
        result = run(truth, estimate, "X", "Y", 1, ("M1",))
        self.assertTrue(all(result["evaluation"][key] is None for key in
                            ("gt_selected_loss", "gt_best_loss", "decision_regret", "regret_vs_s0")))

    def test_s0_and_canonical_baseline_share_start_and_budget_but_are_distinct_labels(self):
        truth = state([("X", "M"), ("M", "Y"), ("T", "U")])
        estimate = state([("X", "M"), ("M", "Y")])
        s0 = run(truth, estimate, "X", "Y", 1, ())
        canonical = run(truth, estimate, "X", "Y", 1, ("M1", "M2", "M3", "M4"), canonical=True)
        self.assertEqual(s0["initial_hash"], canonical["initial_hash"])
        self.assertEqual(s0["budget"], canonical["budget"])
        self.assertEqual(s0["final_hash"], graph_hash(estimate))
        self.assertNotEqual(s0["policy_id"], canonical["policy_id"])
        self.assertEqual(canonical["total_cost"], 1)

    def test_nonfinite_budget_and_zero_active_m4_beta_fail_closed(self):
        truth = state([("X", "M"), ("M", "Y")])
        estimate = state()
        with self.assertRaisesRegex(ValueError, "Invalid budget"):
            run(truth, estimate, "X", "Y", float("inf"), ("M4",))
        with self.assertRaisesRegex(ValueError, "positive beta mass"):
            run(truth, estimate, "X", "Y", 1, ("M4",),
                Config(beta=(0, 1, 1, 1)))


if __name__ == "__main__":
    unittest.main()
