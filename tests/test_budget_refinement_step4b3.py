import gzip
import json
import unittest
from pathlib import Path

from research.budget_aware_refinement.step4_rng import (
    RNGKey, RNG_PROTOCOL_VERSION, derive_seed,
)


ROOT = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"


class Step4B3Tests(unittest.TestCase):
    def test_context_key_covers_cohort_scm_and_baseline_replicate(self):
        base = RNGKey(RNG_PROTOCOL_VERSION, "development", 11, "scm-11",
                      "chain_mediation", 6, 0, "random_baseline", 0)
        keys = [base,
                RNGKey(RNG_PROTOCOL_VERSION, "confirmation", 11, "scm-11", "chain_mediation", 6, 0, "random_baseline", 0),
                RNGKey(RNG_PROTOCOL_VERSION, "development", 11, "scm-12", "chain_mediation", 6, 0, "random_baseline", 0),
                RNGKey(RNG_PROTOCOL_VERSION, "development", 11, "scm-11", "chain_mediation", 6, 0, "random_baseline", 1)]
        self.assertEqual(len({derive_seed(k) for k in keys}), len(keys))

    def test_primary_random_audit_preserves_pairs_and_raw_findings(self):
        raw = json.loads(gzip.decompress((ROOT / "step4b3_p_b4_random_audit_v1.json.gz").read_bytes()))
        report = (ROOT / "STEP4B3_PRIMARY_ESTIMAND_DECISION.md").read_text(encoding="utf-8")
        self.assertEqual(raw["planned_pairs"], 34370)
        self.assertEqual(raw["actual_pairs"], 34370)
        self.assertEqual(raw["settings"]["random_seeds"], [0, 6, 12, 18, 24])
        self.assertTrue(all(row["type_schedule"] == ["FN", "FP", "REV"]
                            for row in raw["pairs"] if row["allowed_types"] == ["FN", "FP", "REV"]))
        self.assertTrue(all(v["same_final_graph"] == v["pairs"]
                            for v in raw["summary_by_policy"].values()))
        self.assertTrue(all(row["policy_remaining_allowed_dag_valid"] == 0 and
                            row["random_remaining_allowed_dag_valid"] == 0
                            for row in raw["pairs"]))
        self.assertIn("34,370/34,370", report)
        self.assertIn("100%", report)

    def test_new_rng_feasibility_report_matches_full_denominators(self):
        raw = json.loads(gzip.decompress((ROOT / "step4b3_rng_feasibility_v1.json.gz").read_bytes()))
        report = (ROOT / "STEP4B3_RNG_FEASIBILITY_REPORT.md").read_text(encoding="utf-8")
        summary = raw["summary"]
        q = summary["Q"]
        self.assertEqual((raw["planned_topology_grid"], raw["planned_P_task_condition_rows"],
                          raw["planned_Q_task_type_cells"]), (100, 1000, 600))
        self.assertEqual(summary["task_selection_failure_slots"], 3)
        self.assertEqual(summary["relabel_equal_pairs_same_seed_nodecount_across_templates"], 0)
        self.assertEqual(summary["relabel_pair_count_same_seed_nodecount_across_templates"], 150)
        self.assertEqual(q["accepted_by_type"], {"FN": 34, "FP": 197, "REV": 55})
        self.assertEqual(q["failed_by_type"], {"FN": 166, "FP": 3, "REV": 145})
        self.assertEqual(q["common_support_scm_ids_all_types"], 34)
        self.assertEqual(sum(q["final_graph_diffs_by_type_budget"][f"{kind}|1"]
                             for kind in ("FN", "FP", "REV")), 121)
        self.assertEqual(sum(q["final_graph_diffs_by_type_budget"][f"{kind}|2"]
                             for kind in ("FN", "FP", "REV")), 0)
        self.assertIn("34/100", report)
        self.assertIn("121/286", report)
        self.assertIn("15 condition rows", report)


if __name__ == "__main__":
    unittest.main()
