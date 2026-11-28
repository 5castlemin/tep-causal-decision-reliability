import unittest

from research.decision_oriented_verification.final_audit import replay_pending


class FinalAuditReplayTests(unittest.TestCase):
    def test_pending_that_was_cycle_blocked_remains_infeasible(self):
        # A->B and B->C make the expert-requested C->A direction cyclic.
        nodes = ("A", "B", "C")
        g0 = {("A", "B"): ("A", "B"), ("B", "C"): ("B", "C"), ("A", "C"): "NO_EDGE"}
        history = [{"pair": ["A", "C"], "answer": "V_TO_U"}]
        state, feasible = replay_pending(nodes, g0, history)
        self.assertEqual(state.pending, {("A", "C"): ("C", "A")})
        self.assertEqual(feasible, [])

    def test_saved_answer_replay_applies_when_dag_feasible(self):
        nodes = ("A", "B", "C")
        g0 = {("A", "B"): "NO_EDGE", ("A", "C"): "NO_EDGE", ("B", "C"): "NO_EDGE"}
        history = [{"pair": ["A", "B"], "answer": "U_TO_V"}]
        state, feasible = replay_pending(nodes, g0, history)
        self.assertEqual(state.relations[("A", "B")], ("A", "B"))
        self.assertEqual(state.pending, {})
        self.assertEqual(feasible, [])


if __name__ == "__main__":
    unittest.main()
