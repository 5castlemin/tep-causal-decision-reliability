import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S4 = ROOT / "research" / "within_task_repair_prioritization" / "s4_completion"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from research.within_task_repair_prioritization.s4_completion import run_s4_pilot as pilot


class S4PilotContractTests(unittest.TestCase):
    def test_locked_pilot_is_exploratory_and_confirmation_is_not_authorized(self):
        lock = json.loads((S4 / "s4_pilot_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["contract_status"], "LOCKED_BEFORE_GENERATION")
        self.assertEqual(lock["classification"], "exploratory_development_pilot")
        self.assertEqual(lock["new_confirmation_scm"], 0)
        self.assertEqual(lock["research_d_replay"], "not authorized; requires existing private unit-level artifacts")
        self.assertEqual(sum(x["target_scm"] for x in lock["cohorts"].values()), 64)

    def test_cohort_seed_namespaces_are_distinct(self):
        lock = json.loads((S4 / "s4_pilot_lock.json").read_text(encoding="utf-8"))
        seeds = [x["master_seed"] for x in lock["cohorts"].values()]
        self.assertEqual(len(set(seeds)), 2)
        self.assertTrue(all(type(seed) is int and seed >= 0 for seed in seeds))

    def test_delta_assignment_is_stable_and_balanced_over_locked_ids(self):
        ids = [f"s4-general-{index:03d}" for index in range(32)]
        first = [pilot.delta_for("general", scm_id) for scm_id in ids]
        second = [pilot.delta_for("general", scm_id) for scm_id in ids]
        self.assertEqual(first, second)
        self.assertEqual(set(first), {-1, 1})
        self.assertGreaterEqual(first.count(-1), 8)
        self.assertGreaterEqual(first.count(1), 8)

    def test_fixed_repair_configuration_matches_contract(self):
        config = pilot.make_config()
        self.assertEqual(config.fp_rule, "A")
        self.assertEqual(config.normalization, "fixed_opportunity")
        self.assertEqual(set(dict(config.costs).values()), {1})

    def test_resource_monitor_reports_current_process_on_windows(self):
        value = pilot.process_rss_bytes()
        self.assertIs(type(value), int)
        self.assertGreater(value, 0)


if __name__ == "__main__":
    unittest.main()
