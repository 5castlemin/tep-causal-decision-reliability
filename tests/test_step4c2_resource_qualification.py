from __future__ import annotations

import json
from pathlib import Path
import unittest


class ProductionIsolatedResourceQualificationTests(unittest.TestCase):
    def test_v2_fixture_report_is_production_isolated_and_denominators_match(self):
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        data = json.loads((root / "step4c2_resource_qualification_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 2)
        self.assertFalse(data["study_cohort_generated"])
        self.assertEqual(data["independent_scm_n"], 0)
        self.assertEqual(data["study_eligible_admissions"], 0)
        self.assertTrue(data["registry_rows_are_fixed_fixture_test_doubles"])
        self.assertFalse(data["decision_regret_analysis"])
        self.assertTrue(data["settings"]["isolate_stages"])
        self.assertEqual(data["settings"]["unit_timeout_seconds"], 2.0)
        self.assertEqual(data["settings"]["rss_sampled_kill_bytes"], 512 * 1024 * 1024)
        rows = [row for row in data["rows"] if row.get("strict_q_common")]
        runs = [run for row in rows for run in row["runs"]]
        self.assertEqual(len(rows), 14)
        self.assertEqual(len(runs), 14)
        self.assertEqual({row["template"] for row in rows}, {
            "chain_mediation", "fork_branch", "observed_common_cause", "multiple_directed_paths"})
        self.assertEqual({row["node_count"] for row in rows}, {6, 7, 8, 9, 10})
        self.assertEqual(len(data["rows"]), 20)
        unavailable = [row for row in data["rows"] if not row.get("strict_q_common")]
        self.assertEqual(len(unavailable), 6)
        self.assertEqual({run["status"] for run in runs}, {"OK"})
        self.assertTrue(all(run["isolate_stages"] and run["resume_replayed"] for run in runs))
        self.assertTrue(all(all(value is not None for value in run["stage_sampled_child_rss_bytes"].values())
                            for run in runs))
        self.assertEqual(data["registry_counts"]["registry_accepted"], 14)
        self.assertEqual(data["registry_counts"]["composite_available"], 14)
        proposal = json.loads((root / "step4c2_proposal_cost_benchmark_v1.json").read_text(encoding="utf-8"))
        self.assertFalse(proposal["study_cohort_generated"])
        self.assertEqual(len(proposal["rows"]), 20)
        self.assertEqual(sum(x["proposal_status"] == "accepted" for x in proposal["rows"]), 7)
        self.assertLess(data["whole_cohort_storage_bytes"], data["whole_cohort_storage_cap_bytes"])
        self.assertLessEqual(data["whole_cohort_storage_bytes"] + data["failure_reserve_bytes"],
                             data["whole_cohort_storage_cap_bytes"])


if __name__ == "__main__":
    unittest.main()
