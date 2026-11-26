import unittest

from research.budget_adaptive_repair.adaptive_m4 import run
from research.original_objective import policy_engine as pe


class AdaptiveM4Tests(unittest.TestCase):
    def setUp(self):
        self.truth = pe.state([("X", "M"), ("M", "Y"), ("M", "Z")])
        self.action, self.target = "X", "Y"
        self.config = pe.Config()

    def test_matches_m4_when_no_blocker(self):
        initial = pe.state([("M", "Y"), ("M", "Z")])
        got = run(self.truth, initial, self.action, self.target, 2, self.config)
        expected = pe.run(self.truth, initial, self.action, self.target, 2, ("M4",), self.config)
        self.assertEqual(got["final_graph"], pe.state(expected["final_edges"], unresolved=expected["final_unresolved"]))
        self.assertEqual(got["cost"], expected["total_cost"])

    def test_task_error_absent_stops(self):
        got = run(self.truth, self.truth, self.action, self.target, 4, self.config)
        self.assertEqual(got["edits"], [])

    def test_off_task_fp_blocker_is_removed_then_task_edit_applied(self):
        initial = pe.state([("M", "Y"), ("M", "Z"), ("Z", "X")])
        got = run(self.truth, initial, self.action, self.target, 2, self.config)
        self.assertEqual([x["metric"] for x in got["edits"]], ["M2_BLOCKER", "M4"])
        self.assertEqual(got["final_graph"], self.truth)

    def test_off_task_fp_that_is_not_a_blocker_is_not_removed(self):
        initial = pe.state([("M", "Y"), ("M", "Z"), ("Y", "Z")])
        got = run(self.truth, initial, self.action, self.target, 2, self.config)
        self.assertEqual([x["metric"] for x in got["edits"]], ["M4"])

    def test_one_remaining_edit_does_not_spend_as_blocker(self):
        initial = pe.state([("M", "Y"), ("M", "Z"), ("Z", "X")])
        got = run(self.truth, initial, self.action, self.target, 1, self.config)
        self.assertEqual(got["edits"], [])
        self.assertEqual(got["cost"], 0)

    def test_never_accepts_outcomes_as_inputs(self):
        self.assertNotIn("loss", run.__code__.co_varnames)
        self.assertNotIn("evaluator", run.__code__.co_varnames)


if __name__ == "__main__":
    unittest.main()
