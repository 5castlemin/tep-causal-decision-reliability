"""Deterministic TEST_ONLY coverage for structural pilot and cohort ledger."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from research.original_objective.cohort_ledger_test_only import (
    FixtureCohortLedger, LedgerConflict,
)
from research.original_objective.structural_pilot import run_structural_pilot


EXPECTED = ["S0", "M1", "CANONICAL"]


def fixture_worker(context):
    return {"test_only": True, "input_sha256": "fixture-input-sha256",
            "policy_results": [{"policy_id": policy, "status": "OK", "value": 0}
                               for policy in EXPECTED]}


fixture_worker.__test_only_fixture_worker__ = True


def make_ledger(root, *, config=None, active=30, storage=500000, rss=None):
    return FixtureCohortLedger(Path(root), run_id="fixture-run-v1", cohort="development",
                               master_seed=12345, config=config or {"version": "fixture-v1"},
                               expected_policy_ids=EXPECTED, max_active_seconds=active,
                               max_storage_bytes=storage, max_rss_bytes=rss,
                               failure_reserve_bytes=1024)


class StructuralPilotTests(unittest.TestCase):
    def test_small_design_is_reproducible_and_structure_only(self):
        a = run_structural_pilot(replicates_per_stratum=1)
        b = run_structural_pilot(replicates_per_stratum=1)
        self.assertEqual(a, b)
        self.assertEqual(a["summary"]["topology_proposals"], 20)
        self.assertFalse(a["research_cohort_generated"])
        self.assertFalse(a["study_regret_generated"])
        self.assertEqual(a["summary"]["template_case_counts"], {
            "chain_mediation": 5, "fork_branch": 5,
            "observed_common_cause": 5, "multiple_directed_paths": 5})
        self.assertIn("error_type_zone_counts", a["summary"])
        self.assertIn("budget_diagnostics", a["summary"])
        for case in a["cases"]:
            self.assertNotIn("coefficients", case)
            self.assertNotIn("observations", case)
            self.assertNotIn("regret", case)


class FixtureCohortLedgerTests(unittest.TestCase):
    def test_atomic_resume_duplicate_replay_and_independent_seed_streams(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = make_ledger(temp)
            first = ledger.run_fixture(["scm-1", "scm-2"], fixture_worker, max_new_scms=1)
            self.assertEqual(first["status"], "PAUSED_FIXTURE_TEST")
            self.assertEqual(first["scm_result_count"], 1)
            record1 = json.loads((Path(temp) / "scm-scm-1.json").read_text(encoding="utf-8"))["payload"]
            self.assertEqual(len(set(record1["seeds"].values())), 3)
            second = ledger.run_fixture(["scm-1", "scm-2"], fixture_worker)
            self.assertEqual(second["status"], "COMPLETE_TEST_ONLY")
            self.assertEqual(second["complete_test_only_scm_count"], 2)
            third = ledger.run_fixture(["scm-1", "scm-2"], fixture_worker)
            self.assertEqual(third["scm_result_count"], 2)
            with self.assertRaises(ValueError):
                ledger.run_fixture(["scm-1", "scm-1"], fixture_worker)
            with self.assertRaises(LedgerConflict):
                make_ledger(temp, config={"version": "changed"}).run_fixture(["scm-1"], fixture_worker)

    def test_incomplete_policy_vector_is_not_a_paired_result(self):
        with tempfile.TemporaryDirectory() as temp:
            def worker(_context):
                return {"test_only": True, "input_sha256": "fixture",
                        "policy_results": [{"policy_id": "S0", "status": "OK"},
                                           {"policy_id": "M1", "status": "FAILED"}]}
            worker.__test_only_fixture_worker__ = True
            result = make_ledger(temp).run_fixture(["scm-1"], worker)
            row = result["records"][0]
            self.assertEqual(row["status"], "INCOMPLETE_TEST_ONLY")
            self.assertFalse(row["paired_comparison_allowed"])
            self.assertEqual(result["failed_or_incomplete_scm_count"], 1)

    def test_checksum_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            make_ledger(temp).run_fixture(["scm-1"], fixture_worker)
            path = Path(temp) / "scm-scm-1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["payload"]["status"] = "TAMPERED"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(LedgerConflict, "checksum"):
                make_ledger(temp).run_fixture(["scm-1"], fixture_worker)

    def test_rss_cap_stops_before_worker_and_records_terminal_state(self):
        with tempfile.TemporaryDirectory() as temp:
            result = make_ledger(temp, rss=1).run_fixture(["scm-1"], fixture_worker)
            self.assertEqual(result["status"], "RESOURCE_STOP")
            state = json.loads((Path(temp) / "run_state.json").read_text(encoding="utf-8"))["payload"]
            self.assertEqual(state["stop_reason"], "SAMPLED_RSS_CAP")
            self.assertEqual(result["scm_result_count"], 0)

    def test_active_time_cap_stops_between_atomic_scm_units(self):
        with tempfile.TemporaryDirectory() as temp:
            calls = []
            def slow_worker(context):
                calls.append(context["scm_id"])
                time.sleep(0.05)
                return {"test_only": True, "input_sha256": "fixture",
                        "policy_results": [{"policy_id": p, "status": "OK"} for p in EXPECTED]}
            slow_worker.__test_only_fixture_worker__ = True
            result = make_ledger(temp, active=0.02).run_fixture(["scm-1", "scm-2"], slow_worker)
            self.assertEqual(result["status"], "RESOURCE_STOP")
            self.assertEqual(calls, ["scm-1"])
            self.assertTrue((Path(temp) / "scm-scm-1.json").exists())
            self.assertFalse((Path(temp) / "scm-scm-2.json").exists())
            state = json.loads((Path(temp) / "run_state.json").read_text(encoding="utf-8"))["payload"]
            self.assertEqual(state["stop_reason"], "COHORT_ACTIVE_TIME_CAP")

    def test_storage_cap_preserves_resource_stop_record(self):
        with tempfile.TemporaryDirectory() as temp:
            def big_worker(_context):
                return {"test_only": True, "input_sha256": "fixture",
                        "policy_results": [{"policy_id": p, "status": "OK", "test_payload": "x" * 12000}
                                           for p in EXPECTED]}
            big_worker.__test_only_fixture_worker__ = True
            result = make_ledger(temp, storage=9000).run_fixture(["scm-1"], big_worker)
            self.assertEqual(result["status"], "RESOURCE_STOP")
            state = json.loads((Path(temp) / "run_state.json").read_text(encoding="utf-8"))["payload"]
            self.assertEqual(state["stop_reason"], "COHORT_STORAGE_CAP")

    def test_actual_process_termination_after_checkpoint_resumes_without_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            signal_path = root / "second_started"
            worker_script = root / "interrupt_worker.py"
            worker_script.write_text(
                "import sys,time\n"
                "from pathlib import Path\n"
                "sys.path.insert(0,sys.argv[3])\n"
                "from research.original_objective.cohort_ledger_test_only import FixtureCohortLedger\n"
                "expected=['S0','M1','CANONICAL']\n"
                "def worker(c):\n"
                "  if c['scm_id']=='scm-2':\n"
                "    Path(sys.argv[2]).write_text('started')\n"
                "    time.sleep(90)\n"
                "  return {'test_only':True,'input_sha256':'fixture','policy_results':[{'policy_id':p,'status':'OK'} for p in expected]}\n"
                "worker.__test_only_fixture_worker__=True\n"
                "ledger=FixtureCohortLedger(Path(sys.argv[1]),run_id='fixture-run-v1',cohort='development',master_seed=12345,config={'version':'fixture-v1'},expected_policy_ids=expected,max_active_seconds=300,max_storage_bytes=500000,max_rss_bytes=None,failure_reserve_bytes=1024)\n"
                "ledger.run_fixture(['scm-1','scm-2'],worker)\n",
                encoding="utf-8")
            repo_root = Path(__file__).resolve().parents[1]
            proc = subprocess.Popen([sys.executable, str(worker_script), str(root), str(signal_path), str(repo_root)],
                                    cwd=repo_root)
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline and not signal_path.exists() and proc.poll() is None:
                    time.sleep(0.05)
                self.assertTrue(signal_path.exists(), "child did not reach second SCM stage")
                with self.assertRaises(LedgerConflict):
                    make_ledger(root, active=300).run_fixture(["scm-1", "scm-2"], fixture_worker)
                proc.terminate()
                proc.wait(timeout=10)
            finally:
                if proc.poll() is None:
                    proc.kill(); proc.wait(timeout=10)
            self.assertTrue((root / "scm-scm-1.json").exists())
            self.assertFalse((root / "scm-scm-2.json").exists())
            resumed = make_ledger(root, active=300).run_fixture(["scm-1", "scm-2"], fixture_worker)
            self.assertEqual(resumed["status"], "COMPLETE_TEST_ONLY")
            self.assertEqual(resumed["complete_test_only_scm_count"], 2)


if __name__ == "__main__":
    unittest.main()
