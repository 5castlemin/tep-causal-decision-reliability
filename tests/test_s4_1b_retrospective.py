"""Integrity checks for public aggregate-only S4-1B artifacts."""
import csv
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/within_task_repair_prioritization/s4_completion/s4_1b_retrospective"
OUT = BASE / "outputs_attempt7"

class S4RetrospectiveArtifactTests(unittest.TestCase):
    def test_public_output_hashes_match_manifest(self):
        manifest = json.loads((BASE / "retrospective_manifest.json").read_text(encoding="utf-8"))
        for name, expected in manifest["public_outputs_sha256"].items():
            actual = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_b1_has_all_63_subsets_for_both_cohorts(self):
        with (OUT / "b1_all_63_policy_aggregates.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 126)
        for cohort in ("general", "opportunity_rich_diagnostic"):
            subset = [r for r in rows if r["cohort"] == cohort]
            self.assertEqual(len(subset), 63)
            self.assertEqual({int(r["n_scm"]) for r in subset}, {32})

    def test_analysis_records_no_new_samples_and_private_units(self):
        summary = json.loads((OUT / "retrospective_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["B1_policy_rows"], 64 * 63)
        self.assertEqual(summary["new_scm"], 0)
        self.assertEqual(summary["new_g0"], 0)
        self.assertEqual(summary["new_observation_rows"], 0)
        self.assertEqual(summary["new_intervention_rows"], 0)
        self.assertTrue(summary["private_unit_outputs_retained_outside_repository"])
        self.assertFalse((OUT / "b1_all_63_unit_recommendations.csv").exists())
        self.assertFalse((OUT / "opportunity_budget_unit_diagnostics.csv").exists())

    def test_k_stratified_aggregate_is_hashed_and_contains_no_unit_ids(self):
        manifest = json.loads((BASE / "retrospective_manifest.json").read_text(encoding="utf-8"))
        info = manifest["k_stratified_analysis"]
        stratified = BASE / "k_stratified_outputs"
        for name, expected in info["public_outputs_sha256"].items():
            self.assertEqual(hashlib.sha256((stratified / name).read_bytes()).hexdigest(), expected)
        with (stratified / "b1_policy_differences_by_initial_K.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 567)
        self.assertEqual({r["cohort"] for r in rows}, {"general", "opportunity_rich_diagnostic"})
        self.assertNotIn("scm_id", rows[0])
        self.assertEqual(info["generated_counts"], {"SCM": 0, "G0": 0, "observations": 0, "intervention_rows": 0})

if __name__ == "__main__":
    unittest.main()
