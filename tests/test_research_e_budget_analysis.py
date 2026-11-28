import unittest

from research.budget_adaptive_repair.summarize_e2_e3 import pareto


class ResearchEBudgetAnalysisTests(unittest.TestCase):
    def test_pareto_removes_dominated_candidate(self):
        points = [
            {"cost": 0.0, "loss": 1.0, "policy": "base"},
            {"cost": 1.0, "loss": 0.5, "policy": "efficient"},
            {"cost": 2.0, "loss": 0.75, "policy": "dominated"},
        ]
        result = pareto(points)
        self.assertEqual({x["policy"] for x in result}, {"base", "efficient"})

    def test_pareto_retains_exact_coordinate_ties(self):
        points = [
            {"cost": 1.0, "loss": 0.5, "policy": "a"},
            {"cost": 1.0, "loss": 0.5, "policy": "b"},
        ]
        self.assertEqual(len(pareto(points)), 2)

    def test_more_cost_and_same_loss_is_dominated(self):
        points = [
            {"cost": 1.0, "loss": 0.5, "policy": "less"},
            {"cost": 2.0, "loss": 0.5, "policy": "more"},
        ]
        self.assertEqual([x["policy"] for x in pareto(points)], ["less"])


if __name__ == "__main__":
    unittest.main()
