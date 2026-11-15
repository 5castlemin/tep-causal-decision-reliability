import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from research.budget_aware_refinement.step4b4_mock_runner import (
    SimulatedProcessStop,
    append_event,
    composite_scm_result,
    recover_jsonl,
    run_pipeline,
)


def ok_stages(counter=None):
    counter = counter if counter is not None else {}
    def stage(name):
        def call():
            counter[name] = counter.get(name, 0) + 1
            return {"fixture": name, "value": counter[name]}
        return call
    return {name: stage(name) for name in ("graph", "fit", "recommend", "truth")}


class Step4B4MockRunnerTests(unittest.TestCase):
    def test_final_gate_manifest_matches_mock_sources_and_raw_ledger(self):
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        manifest = json.loads((root / "step4b4_final_gate_manifest.json").read_text(encoding="utf-8"))
        settings_bytes = json.dumps(manifest["settings"], sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(settings_bytes).hexdigest(), manifest["settings_sha256"])
        for name, expected in manifest["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected)

    def test_existing_graph_ridge_path_and_truth_stub_do_not_emit_outcomes(self):
        from research.budget_aware_refinement.run_step4b4_mock_pipeline import build_mock_stages
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "integrated.jsonl"
            result = run_pipeline("fixed-numeric-fixture", ledger, build_mock_stages())
            self.assertEqual(result["status"], "OK")
            events = recover_jsonl(ledger)
            truth = next(row for row in events if row["event"] == "stage:truth")
            self.assertFalse(truth["output"]["evaluation_performed"])
            self.assertIsNone(truth["output"]["regret"])

    def test_forced_stop_resume_and_no_duplicate_completed_events(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            calls = {}
            stages = ok_stages(calls)
            original_fit = stages["fit"]
            stop_once = {"yes": True}
            def interrupted_fit():
                if stop_once["yes"]:
                    stop_once["yes"] = False
                    raise SimulatedProcessStop()
                return original_fit()
            stages["fit"] = interrupted_fit
            with self.assertRaises(SimulatedProcessStop):
                run_pipeline("r-1", ledger, stages)
            self.assertEqual([r["event"] for r in recover_jsonl(ledger)], ["stage:graph"])
            result = run_pipeline("r-1", ledger, stages)
            self.assertEqual(result["status"], "OK")
            self.assertEqual(calls["graph"], 1)
            self.assertEqual(calls["fit"], 1)
            rows = recover_jsonl(ledger)
            self.assertEqual(len(rows), 5)
            self.assertEqual(len({(r["run_id"], r["event"]) for r in rows}), len(rows))
            again = run_pipeline("r-1", ledger, ok_stages({}))
            self.assertEqual(again["status"], "OK")
            self.assertEqual(len(recover_jsonl(ledger)), 5)

    def test_forced_process_exit_resumes_from_fsynced_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "process.jsonl"
            code = """
import os, sys
from pathlib import Path
from research.budget_aware_refinement.step4b4_mock_runner import run_pipeline
p=Path(sys.argv[1])
def graph(): return {'fixture':'graph'}
def stop(): os._exit(73)
def later(): return {'fixture':'later'}
run_pipeline('killed-run',p,{'graph':graph,'fit':stop,'recommend':later,'truth':later})
"""
            child = subprocess.run([sys.executable, "-c", code, str(ledger)], check=False)
            self.assertEqual(child.returncode, 73)
            rows_before = recover_jsonl(ledger)
            self.assertEqual([row["event"] for row in rows_before], ["stage:graph"])
            calls = {}
            result = run_pipeline("killed-run", ledger, ok_stages(calls))
            self.assertEqual(result["status"], "OK")
            self.assertEqual(calls.get("graph", 0), 0)
            self.assertEqual(len(recover_jsonl(ledger)), 5)

    def test_partial_tail_is_removed_and_completed_records_survive(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            append_event(ledger, {"run_id": "x", "event": "stage:graph", "status": "OK"}, max_bytes=4096)
            with ledger.open("ab") as handle:
                handle.write(b'{"run_id":"x","event":')
            rows = recover_jsonl(ledger)
            self.assertEqual(len(rows), 1)
            self.assertTrue(ledger.read_bytes().endswith(b"\n"))

    def test_conflicting_same_run_event_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            first = {"run_id": "x", "event": "stage:graph", "status": "OK"}
            append_event(ledger, first, max_bytes=4096)
            self.assertFalse(append_event(ledger, first, max_bytes=4096))
            with self.assertRaises(ValueError):
                append_event(ledger, first | {"status": "DIFFERENT"}, max_bytes=4096)

    def test_rng_key_is_bound_to_run_id(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            run_pipeline("rng-bound", ledger, ok_stages(), rng_key="key-a")
            with self.assertRaises(ValueError):
                run_pipeline("rng-bound", ledger, ok_stages(), rng_key="key-b")

    def test_one_policy_failure_and_gt_failure_leave_vector_incomplete(self):
        row = composite_scm_result({
            "FN": {"status": "OK", "global_regret": 1.0, "task_focused_regret": 0.5},
            "FP": {"status": "RIDGE_FAIL", "global_regret": None, "task_focused_regret": 0.3},
            "REV": {"status": "OK", "global_regret": 0.2, "task_focused_regret": 0.1},
        })
        self.assertFalse(row["complete"])
        self.assertIsNone(row["D_i"])
        gt = composite_scm_result({
            "FN": {"status": "OK", "global_regret": 1, "task_focused_regret": 0},
            "FP": {"status": "GT_EVAL_FAIL", "global_regret": None, "task_focused_regret": None},
            "REV": {"status": "OK", "global_regret": 1, "task_focused_regret": 0},
        })
        self.assertEqual(gt["reason"], "incomplete_FP")

    def test_failure_status_is_preserved_and_no_success_terminal_is_written(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            stages = ok_stages()
            def fail():
                raise RuntimeError("fixture Ridge failure")
            stages["fit"] = fail
            result = run_pipeline("r-fail", ledger, stages)
            self.assertEqual(result["status"], "RIDGE_FAIL")
            rows = recover_jsonl(ledger)
            self.assertEqual(rows[-2]["status"], "RIDGE_FAIL")
            self.assertEqual(rows[-1]["status"], "RIDGE_FAIL")

    def test_disk_cap_stops_with_terminal_record_and_keeps_raw_state(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            stages = ok_stages()
            result = run_pipeline("r-cap", ledger, stages, max_ledger_bytes=700)
            self.assertEqual(result["status"], "DISK_CAP")
            rows = recover_jsonl(ledger)
            self.assertEqual(rows[-1]["status"], "DISK_CAP")
            self.assertLessEqual(ledger.stat().st_size, 700)

    def test_wall_limit_is_checked_at_stage_boundaries_and_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            now = {"t": 0.0}
            def clock():
                return now["t"]
            stages = ok_stages()
            def graph():
                now["t"] = 2.0
                return {"fixture": "graph"}
            stages["graph"] = graph
            result = run_pipeline("r-time", ledger, stages, max_wall_seconds=1.0, clock=clock)
            self.assertEqual(result["status"], "WALL_CAP")
            rows = recover_jsonl(ledger)
            self.assertEqual(rows[-1]["status"], "WALL_CAP")

    def test_unit_timeout_is_recorded_after_nonpreemptive_stage(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "run.jsonl"
            now = {"t": 0.0}
            def clock():
                value = now["t"]
                now["t"] += .3
                return value
            result = run_pipeline("r-unit-time", ledger, ok_stages(),
                                  max_unit_seconds=.1, clock=clock)
            self.assertEqual(result["status"], "TIMEOUT")
            rows = recover_jsonl(ledger)
            self.assertEqual(rows[-2]["status"], "TIMEOUT")
            self.assertEqual(rows[-2]["output"]["fixture"], "graph")


if __name__ == "__main__":
    unittest.main()
