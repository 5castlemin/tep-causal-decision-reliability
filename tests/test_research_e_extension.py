import unittest
import json
import tempfile
from pathlib import Path

from research.budget_adaptive_repair.extend_final_e import aggregate, frontier, marginal, read_s4


class ResearchEExtensionTests(unittest.TestCase):
    def test_budget_marginal_uses_actual_edits_and_leaves_zero_denominator_undefined(self):
        rows = [
            {"cohort": "C", "unit_id": "1", "policy": "M4", "budget": 0, "loss": 1.0, "cost": 0.0, "action": 0, "changed": False, "unused": 0.0},
            {"cohort": "C", "unit_id": "1", "policy": "M4", "budget": 1, "loss": 0.5, "cost": 1.0, "action": 1, "changed": True, "unused": 0.0},
            {"cohort": "C", "unit_id": "2", "policy": "M4", "budget": 0, "loss": 1.0, "cost": 0.0, "action": 0, "changed": False, "unused": 0.0},
            {"cohort": "C", "unit_id": "2", "policy": "M4", "budget": 1, "loss": 1.0, "cost": 0.0, "action": 0, "changed": False, "unused": 1.0},
        ]
        rows = aggregate(rows)
        result = marginal(rows)[0]
        self.assertEqual(result["marginal_benefit"], 0.25)
        self.assertEqual(result["additional_mean_edits"], 0.5)
        self.assertEqual(result["benefit_per_additional_edit"], 0.5)

    def test_identical_coordinates_are_retained_on_frontier(self):
        rows = [
            {"cohort": "S5", "policy": "M4", "budget": 2, "mean_edit_count": 1.0, "mean_loss": 0.5},
            {"cohort": "S5", "policy": "T5", "budget": 2, "mean_edit_count": 1.0, "mean_loss": 0.5},
        ]
        result = frontier(rows)
        fixed = [x for x in result if x["frontier_type"] == "fixed_budget"]
        self.assertEqual(len(fixed), 2)
        self.assertTrue(all(x["is_frontier"] for x in fixed))

    def test_cohorts_are_aggregated_separately(self):
        rows = [
            {"cohort": "C", "unit_id": "1", "policy": "S0", "budget": 0, "loss": 1.0, "cost": 0.0, "action": 0, "changed": False, "unused": 0.0},
            {"cohort": "S5", "unit_id": "1", "policy": "S0", "budget": 0, "loss": 10.0, "cost": 0.0, "action": 0, "changed": None, "unused": 0.0},
        ]
        result = aggregate(rows)
        self.assertEqual({x["cohort"] for x in result}, {"C", "S5"})
        self.assertEqual({x["mean_loss"] for x in result}, {1.0, 10.0})

    def test_duplicate_explicit_t5_alias_is_excluded(self):
        common = {"scm_id": "unit-1", "budget": 1, "regret": 0.25, "cost": 1,
                  "selected_k": 0.5, "action_changed_from_s0": True}
        rows = [dict(common, policy="T5_GUIDED_M4"), dict(common, policy="T_GREEDY_B1:T5")]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            result = read_s4(path, "S4_DEV")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["policy"], "T5_GUIDED_M4")


if __name__ == "__main__":
    unittest.main()
