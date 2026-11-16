import json
import hashlib
import os
import subprocess
import sys
import tempfile
import time
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


def _spin_forever():
    while True:
        pass


def _slow_stage():
    time.sleep(.5)
    return {"slept": True}


def _allocate_memory():
    block = bytearray(96 * 1024 * 1024)
    for i in range(0, len(block), 4096):
        block[i] = 1
    time.sleep(.5)
    return {"allocated": len(block)}


def _crash_process():
    os._exit(37)


def _raise_stage_error():
    raise RuntimeError("worker exception fixture")


def _stage_graph(): return {"fixture": "graph"}
def _stage_fit(): return {"fixture": "fit"}
def _stage_recommend(): return {"fixture": "recommend"}
def _stage_truth(): return {"fixture": "truth"}


def _kill_after(target):
    def hook(stage):
        if stage == target:
            os._exit(73)
    return hook


class Step4B4MockRunnerTests(unittest.TestCase):
    def test_final_gate_manifest_matches_mock_sources_and_raw_ledger(self):
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        manifest = json.loads((root / "step4b4_final_gate_manifest.json").read_text(encoding="utf-8"))
        settings_bytes = json.dumps(manifest["settings"], sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(settings_bytes).hexdigest(), manifest["settings_sha256"])
        # Source hashes in v1 describe the historical implementation, not this remediation.
        raw_name = "step4b4_mock_pipeline_run_v2.jsonl"
        self.assertEqual(hashlib.sha256((root / raw_name).read_bytes()).hexdigest(),
                         manifest["artifact_sha256"][raw_name])

    def test_production_contract_does_not_promote_mock_truth_to_evaluation(self):
        path = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement" / "STEP4C1_PRODUCTION_RUNNER_CONTRACT.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(contract["production_ready"])
        self.assertFalse(contract["truth_stub_is_successful_evaluation"])
        self.assertEqual(contract["status"], "NOT_FROZEN")
        states = {stage["name"]: stage["state"] for stage in contract["stages"]}
        self.assertEqual(states["ground_truth_evaluation"],
                         "STEP3_FIXED_FIXTURE_ADAPTER_VALIDATED_PRODUCTION_INPUT_REQUIRED")
        self.assertEqual(states["scm_and_shared_data"],
                         "IMPLEMENTED_FIXED_FIXTURE_VALIDATED_NOT_RUN_ON_STUDY_COHORT")
        self.assertEqual(states["cohort_registry_and_orchestrator"],
                         "IMPLEMENTED_FIXED_PROPOSAL_AND_LEDGER_FIXTURES_VALIDATED_NOT_RUN_ON_STUDY_COHORT")
        self.assertFalse(contract["production_ready"])

    def test_existing_graph_ridge_path_and_truth_stub_do_not_emit_outcomes(self):
        from research.budget_aware_refinement.run_step4b4_mock_pipeline import (
            MOCK_CONFIG, MOCK_INPUT_SHA256, build_mock_stages,
        )
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "integrated.jsonl"
            result = run_pipeline("fixed-numeric-fixture", ledger,
                build_mock_stages(ledger, "fixed-numeric-fixture"),
                config=MOCK_CONFIG, input_sha256=MOCK_INPUT_SHA256)
            self.assertEqual(result["status"], "OK")
            events = recover_jsonl(ledger)
            truth = next(row for row in events if row["event"] == "stage:truth")
            self.assertFalse(truth["output"]["evaluation_performed"])
            self.assertIsNone(truth["output"]["regret"])

    def test_integrated_pipeline_restarts_at_each_checkpoint_in_fresh_process(self):
        from research.budget_aware_refinement.run_step4b4_mock_pipeline import (
            MOCK_CONFIG, MOCK_INPUT_SHA256, MOCK_RNG_KEY, build_mock_stages,
        )
        for stop_before in ("fit", "recommend", "truth"):
            with self.subTest(stop_before=stop_before), tempfile.TemporaryDirectory() as td:
                ledger = Path(td) / "resumed.jsonl"
                uninterrupted = Path(td) / "uninterrupted.jsonl"
                code = """
import os, sys
from pathlib import Path
from research.budget_aware_refinement.run_step4b4_mock_pipeline import *
stage_to_stop=sys.argv[2]
stages=build_mock_stages(Path(sys.argv[1]),'integrated-restart')
run_pipeline('integrated-restart',Path(sys.argv[1]),stages,rng_key=MOCK_RNG_KEY,
             config=MOCK_CONFIG,input_sha256=MOCK_INPUT_SHA256,isolate_stages=True,
             checkpoint_hook=lambda stage: os._exit(73) if stage == {'fit':'graph','recommend':'fit','truth':'recommend'}[stage_to_stop] else None)
"""
                child = subprocess.run([sys.executable, "-c", code, str(ledger), stop_before], check=False)
                self.assertEqual(child.returncode, 73)
                events_before = recover_jsonl(ledger)
                self.assertEqual(events_before[-1]["event"], f"stage:{ {'fit':'graph','recommend':'fit','truth':'recommend'}[stop_before] }")
                resumed = run_pipeline("integrated-restart", ledger,
                    build_mock_stages(ledger, "integrated-restart"), rng_key=MOCK_RNG_KEY, config=MOCK_CONFIG,
                    input_sha256=MOCK_INPUT_SHA256, isolate_stages=True)
                baseline = run_pipeline("integrated-restart", uninterrupted,
                    build_mock_stages(uninterrupted, "integrated-restart"), rng_key=MOCK_RNG_KEY, config=MOCK_CONFIG,
                    input_sha256=MOCK_INPUT_SHA256, isolate_stages=True)
                self.assertEqual(resumed["status"], "OK")
                self.assertEqual(baseline["status"], "OK")
                resumed_result = next(r["result_sha256"] for r in recover_jsonl(ledger) if r["event"] == "terminal")
                baseline_result = next(r["result_sha256"] for r in recover_jsonl(uninterrupted) if r["event"] == "terminal")
                self.assertEqual(resumed_result, baseline_result)

    def test_composite_regret_rejects_nonfinite_and_bad_numeric_values(self):
        def rows(value=0.0):
            return {kind: {"status": "OK", "global_regret": value,
                           "task_focused_regret": 0.0} for kind in ("FN", "FP", "REV")}
        for bad in (float("nan"), float("inf"), float("-inf"), "0.4", object()):
            result = composite_scm_result(rows(bad))
            self.assertFalse(result["complete"])
            self.assertIsNone(result["D_i"])
            self.assertEqual(result["status"], "NONFINITE")
        self.assertEqual(composite_scm_result(rows(0.0))["D_i"], 0.0)
        self.assertGreater(composite_scm_result(rows(2.0))["D_i"], 0)
        self.assertLess(composite_scm_result(rows(-2.0))["D_i"], 0)

    def test_event_digest_output_digest_and_configuration_are_verified(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "tamper.jsonl"
            run_pipeline("integrity", ledger, ok_stages(), config={"version": 1}, input_sha256="a" * 64)
            records = recover_jsonl(ledger)
            self.assertEqual(records[-1]["event"], "terminal")
            tampered = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
            tampered["output"]["fixture"] = "altered"
            lines = ledger.read_text(encoding="utf-8").splitlines()
            lines[0] = json.dumps(tampered, sort_keys=True, separators=(",", ":"))
            ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                recover_jsonl(ledger)

    def test_same_run_rejects_changed_config_or_input_hash(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "binding.jsonl"
            run_pipeline("bound", ledger, ok_stages(), config={"x": 1}, input_sha256="b" * 64)
            with self.assertRaises(ValueError):
                run_pipeline("bound", ledger, ok_stages(), config={"x": 2}, input_sha256="b" * 64)
            with self.assertRaises(ValueError):
                run_pipeline("bound", ledger, ok_stages(), config={"x": 1}, input_sha256="c" * 64)
            with self.assertRaises(ValueError):
                run_pipeline("bound", ledger, ok_stages(), config={"x": 1}, input_sha256="b" * 64,
                             rng_key="different-rng")

    def test_checkpoint_stage_order_and_terminal_completeness_are_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ordered.jsonl"
            run_pipeline("ordered", ledger, ok_stages())
            rows = recover_jsonl(ledger)
            # Recompute a valid digest so this specifically exercises semantic validation.
            rows[1]["event"] = "stage:recommend"
            rows[1].pop("event_sha256")
            from research.budget_aware_refinement.step4b4_mock_runner import _event, _canonical
            rows[1] = _event(rows[1]["run_id"], rows[1]["event"], **{
                k: v for k, v in rows[1].items() if k not in ("run_id", "event", "event_sha256")
            })
            ledger.write_bytes(b"\n".join(_canonical(row) for row in rows) + b"\n")
            with self.assertRaises(ValueError):
                run_pipeline("ordered", ledger, ok_stages())

    def test_failed_stage_terminal_is_idempotently_recovered_without_promotion(self):
        cases = (("fit", RuntimeError("ridge"), "RIDGE_FAIL", False),
                 ("truth", RuntimeError("truth"), "GT_EVAL_FAIL", False),
                 ("graph", _spin_forever, "TIMEOUT", True),
                 ("graph", _allocate_memory, "RSS_LIMIT", True))
        for stage_name, failure, expected, isolated in cases:
            with self.subTest(stage=stage_name, expected=expected), tempfile.TemporaryDirectory() as td:
                ledger = Path(td) / "failed.jsonl"
                stages = {"graph": _stage_graph, "fit": _stage_fit,
                          "recommend": _stage_recommend, "truth": _stage_truth}
                if stage_name in ("fit", "truth"):
                    def fail(value=failure): raise value
                    stages[stage_name] = fail
                else:
                    stages[stage_name] = failure
                result = run_pipeline("failed-run", ledger, stages, isolate_stages=isolated,
                                      max_unit_seconds=.15,
                                      max_rss_bytes=64 * 1024 * 1024 if expected == "RSS_LIMIT" else None)
                self.assertEqual(result["status"], expected)
                rows = recover_jsonl(ledger)
                self.assertEqual(rows[-1]["status"], expected)
                self.assertEqual(rows[-1]["completed_stages"], [r["event"].split(":",1)[1]
                                 for r in rows if r["event"].startswith("stage:") and r["status"] == "OK"])
                again = run_pipeline("failed-run", ledger, stages, isolate_stages=isolated,
                                     max_unit_seconds=.15,
                                     max_rss_bytes=64 * 1024 * 1024 if expected == "RSS_LIMIT" else None)
                self.assertEqual(again["status"], expected)
                self.assertEqual(len(recover_jsonl(ledger)), len(rows))

    def test_cumulative_active_stage_time_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "timed.jsonl"
            now = {"t": 0.0}
            def clock(): return now["t"]
            def stage(seconds, name):
                def call():
                    now["t"] += seconds
                    return {"name": name}
                return call
            first = {"graph": stage(1200, "graph"), "fit": _stage_fit,
                     "recommend": _stage_recommend, "truth": _stage_truth}
            with self.assertRaises(SimulatedProcessStop):
                run_pipeline("timed-run", ledger, first, max_wall_seconds=1800, max_unit_seconds=1800, clock=clock,
                             checkpoint_hook=lambda name: (_ for _ in ()).throw(SimulatedProcessStop())
                             if name == "graph" else None)
            self.assertEqual(recover_jsonl(ledger)[0]["elapsed_seconds"], 1200)
            second = {"graph": stage(1200, "graph"), "fit": stage(400, "fit"),
                      "recommend": stage(20, "recommend"), "truth": _stage_truth}
            with self.assertRaises(SimulatedProcessStop):
                run_pipeline("timed-run", ledger, second, max_wall_seconds=1800,
                             max_unit_seconds=1800, clock=clock,
                             checkpoint_hook=lambda name: (_ for _ in ()).throw(SimulatedProcessStop())
                             if name == "fit" else None)
            self.assertEqual(recover_jsonl(ledger)[-1]["elapsed_total_seconds"], 1600)
            third = {"graph": stage(1200, "graph"), "fit": stage(400, "fit"),
                     "recommend": stage(20, "recommend"), "truth": stage(200, "truth")}
            result = run_pipeline("timed-run", ledger, third, max_wall_seconds=1800,
                                  max_unit_seconds=1800, clock=clock)
            self.assertEqual(result["status"], "WALL_CAP")
            events = recover_jsonl(ledger)
            self.assertEqual(events[-1]["status"], "WALL_CAP")
            self.assertGreaterEqual(events[-1]["cumulative_elapsed_seconds"], 1800)

    def test_isolated_stages_terminate_timeout_memory_exit_and_exception(self):
        cases = (
            ("TIMEOUT", _spin_forever, {"max_unit_seconds": .2}),
            ("TIMEOUT", _slow_stage, {"max_unit_seconds": .1}),
            ("RSS_LIMIT", _allocate_memory, {"max_rss_bytes": 64 * 1024 * 1024}),
            ("CHILD_EXIT", _crash_process, {}),
            ("RIDGE_FAIL", _raise_stage_error, {}),
        )
        for expected, fit, limits in cases:
            with self.subTest(expected=expected, fit=fit.__name__), tempfile.TemporaryDirectory() as td:
                ledger = Path(td) / "isolated.jsonl"
                stages = {"graph": _stage_graph, "fit": _stage_fit,
                          "recommend": _stage_recommend, "truth": _stage_truth}
                stages["fit"] = fit
                result = run_pipeline("isolated", ledger, stages, isolate_stages=True, **limits)
                self.assertEqual(result["status"], expected)
                records = recover_jsonl(ledger)
                self.assertEqual(records[-1]["status"], expected)

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
            result = run_pipeline("r-cap", ledger, stages, max_ledger_bytes=1100)
            self.assertEqual(result["status"], "DISK_CAP")
            rows = recover_jsonl(ledger)
            self.assertEqual(rows[-1]["status"], "DISK_CAP")
            self.assertLessEqual(ledger.stat().st_size, 1100)
            self.assertEqual(run_pipeline("r-cap", ledger, stages, max_ledger_bytes=1100)["status"], "DISK_CAP")

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
            self.assertEqual(run_pipeline("r-time", ledger, stages, max_wall_seconds=1.0, clock=clock)["status"], "WALL_CAP")

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
