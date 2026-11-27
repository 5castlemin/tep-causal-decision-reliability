import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
S3 = ROOT / "research" / "within_task_repair_prioritization"


class S3PublicArtifactTests(unittest.TestCase):
    def test_public_tables_contain_cohort_aggregates_not_unit_rows(self):
        for path in (S3 / "tables").glob("*.csv"):
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                self.assertNotIn("scm_id", row)
                self.assertNotIn("scm", row)

    def test_summary_proves_no_new_cohort_or_response_data(self):
        summary = json.loads((S3 / "tables" / "s3_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["new_scm"], 0)
        self.assertEqual(summary["new_g0"], 0)
        self.assertEqual(summary["new_independent_observational_draws"], 0)
        self.assertEqual(summary["new_intervention_rows"], 0)
        self.assertEqual(summary["policy_count"], 63)
        self.assertEqual(summary["bootstrap_replicates"], 10_000)

    def test_manifest_labels_posthoc_scope_and_binds_all_source_databases(self):
        manifest = json.loads((S3 / "s3_integrity_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["classification"], "POST_HOC_S3_EXPLORATORY")
        self.assertEqual(len(manifest["data_hashes"]), 4)
        self.assertTrue(all(len(x) == 64 for x in manifest["data_hashes"].values()))
        self.assertIn("The first exploratory calculation preceded a committed analysis revision; this cannot be represented as preregistered.", manifest["limitations"])

    def test_corrected_outputs_are_versioned_and_limited(self):
        correction = S3 / "tables" / "correction_v1"
        summary = json.loads((correction / "corrected_s3_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["gate"], "S3_CORRECTION_RECOMPUTED_WITH_LIMITATIONS")
        self.assertEqual(summary["policy_count"], 63)
        self.assertEqual(len(summary["lookahead_sets"]), 63)
        self.assertEqual(summary["new_scm"], 0)
        self.assertEqual(summary["new_intervention_rows"], 0)
        self.assertTrue((S3 / "RESEARCH_S3_CORRECTION_AUDIT.md").exists())
        self.assertIn("not run", (S3 / "RESEARCH_S3_EX_POST_BENCHMARK.md").read_text(encoding="utf-8").lower())
        self.assertIn("not run", (S3 / "RESEARCH_S3_OBJECTIVE_SENSITIVITY.md").read_text(encoding="utf-8").lower())

    def test_public_correction_csvs_have_aggregate_rows_only(self):
        for path in (S3 / "tables" / "correction_v1").glob("*.csv"):
            with path.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                fields = reader.fieldnames or []
                self.assertNotIn("scm_id", fields)
                self.assertNotIn("scm", fields)
                for row in reader:
                    self.assertNotIn("scm_id", row)
                    self.assertNotIn("scm", row)


if __name__ == "__main__":
    unittest.main()
