import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "research" / "within_task_repair_prioritization" / "s4_completion" / "tables" / "completion_v3"


class S3CompletionPublicArtifactTests(unittest.TestCase):
    def test_public_tables_are_aggregate_only(self):
        forbidden = {"scm", "scm_id", "unit_id", "graph_hash", "proposal_id"}
        for path in TABLES.glob("*.csv"):
            with self.subTest(path=path.name), path.open(encoding="utf-8", newline="") as stream:
                columns = {column.lower() for column in next(csv.reader(stream))}
                self.assertTrue(columns.isdisjoint(forbidden), path.name)

    def test_candidate_ranking_covers_all_63_subsets_and_three_objectives(self):
        with (TABLES / "single_edit_ranking_aggregate.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        scores = {row["candidate_score"] for row in rows if row["candidate_score"] != "M4"}
        self.assertEqual(len(scores), 63)
        self.assertEqual({row["gamma"] for row in rows}, {"0.0", "0.2", "0.5"})

    def test_summary_records_existing_cohorts_and_no_new_samples(self):
        summary = json.loads((TABLES / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["cohort_n"], {"C_DEVELOPMENT": 64, "C_HELDOUT": 200})
        self.assertEqual(summary["new_scm"], 0)
        self.assertEqual(summary["new_g0"], 0)
        self.assertEqual(summary["new_observations"], 0)
        self.assertEqual(summary["new_interventions"], 0)
        self.assertTrue(summary["public_aggregate_only"])

    def test_result_manifest_binds_public_files_and_keeps_s4_proposed(self):
        folder = ROOT / "research" / "within_task_repair_prioritization" / "s4_completion"
        manifest = json.loads((folder / "S3_COMPLETION_RESULT_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["public_outputs_aggregate_only"])
        self.assertFalse(manifest["private_row_level_output_committed"])
        self.assertFalse(any("outputs_" in path for path in manifest["files"]))
        self.assertEqual(manifest["file_hash_basis"], "UTF-8 text bytes with CRLF normalized to LF")
        for relative, expected in manifest["files"].items():
            raw = (ROOT / relative).read_bytes()
            actual = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
            self.assertEqual(actual, expected, relative)
        contract = json.loads((folder / "research_s4_contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["status"], "PROPOSED_NOT_EXECUTED")
        self.assertFalse(contract["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
