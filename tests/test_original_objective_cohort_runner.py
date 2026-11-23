"""Durability, process interruption and GT arithmetic checks for fixture cohort runner."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

from research.original_objective import cohort_runner as cr
from research.original_objective.cohort_runner import (
    CohortIntegrityError, run_test_only_cohort, read_test_only_cohort,
)
from research.original_objective.fixed_fixture_data import (
    make_fixed_fixture, make_nondegenerate_fixture,
)
from research.budget_aware_refinement.step3_adapter import K


def _fixtures():
    return {"fixed-scm": make_fixed_fixture,
            "nondegenerate-scm": {"factory": make_nondegenerate_fixture,
                                  "apply_g0_generator": False}}


class ResearchCCohortRunnerTests(unittest.TestCase):
    def test_two_fixed_scms_complete_and_nondegenerate_regret_matches_hand_calculation(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_test_only_cohort(Path(directory), run_id="fixture-cohort-v1",
                                          master_seed=20261124, fixtures=_fixtures(),
                                          budgets=(0, 1))
            self.assertEqual(result["counts"]["completed"], 2)
            self.assertEqual(result["complete_policy_evaluations"], 68)
            self.assertTrue(result["all_scm_complete"])
            self.assertEqual([r["scm_id"] for r in result["scms"]],
                             ["fixed-scm", "nondegenerate-scm"])
            self.assertNotEqual(result["scms"][0]["rng_streams"],
                                result["scms"][1]["rng_streams"])
            for scm in result["scms"]:
                self.assertEqual(scm["status"], "COMPLETED")
                self.assertEqual(scm["result"]["classification"],
                                 "TEST_ONLY_NOT_RESEARCH_COHORT")
                for budget in scm["result"]["e2e_result"]["budgets"]:
                    self.assertEqual(budget["policy_vector_status"], "COMPLETE")
                    self.assertEqual(len({p["shared_observations_sha256"]
                                          for p in budget["policies"]}), 1)
                    self.assertEqual(len({p["shared_input_sha256"]
                                          for p in budget["policies"]}), 1)

            special = next(r["result"] for r in result["scms"]
                           if r["scm_id"] == "nondegenerate-scm")
            fixture, _ = make_nondegenerate_fixture()
            observations = fixture.observations
            x_i, y_i = fixture.truth_spec["nodes"].index("X"), fixture.truth_spec["nodes"].index("Y")
            x_mean = float(observations[:, x_i].mean())
            y_mean = float(observations[:, y_i].mean())
            x_sd = float(observations[:, x_i].std(ddof=1))
            y_sd = float(observations[:, y_i].std(ddof=1))
            # By hand from the explicit SCM: do(X=a) gives M=.9a, Y=.9M=.81a.
            hand_losses = {k: ((0.81 * (x_mean + k * x_sd) - (y_mean + y_sd)) / y_sd) ** 2
                           for k in K}
            hand_best = min(hand_losses.values())
            budget1 = next(b for b in special["e2e_result"]["budgets"] if b["budget"] == 1)
            by_policy = {p["policy_id"]: p for p in budget1["policies"]}
            s0, m4 = by_policy["S0"], by_policy["M4"]
            self.assertEqual(s0["evaluation"]["selected_k"], 0.0)
            self.assertEqual(m4["evaluation"]["selected_k"], 1.0)
            self.assertAlmostEqual(s0["evaluation"]["regret"],
                                   hand_losses[s0["evaluation"]["selected_k"]] - hand_best,
                                   places=12)
            self.assertAlmostEqual(m4["evaluation"]["regret"],
                                   hand_losses[m4["evaluation"]["selected_k"]] - hand_best,
                                   places=12)
            self.assertGreater(s0["evaluation"]["regret"], 0.5)
            self.assertAlmostEqual(m4["evaluation"]["regret"], 0.0, places=12)

    def test_replay_is_idempotent_config_conflict_and_checksum_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = run_test_only_cohort(root, run_id="replay-v1", master_seed=5,
                                         fixtures={"fixed-scm": make_fixed_fixture}, budgets=(0,))
            again = run_test_only_cohort(root, run_id="replay-v1", master_seed=5,
                                         fixtures={"fixed-scm": make_fixed_fixture}, budgets=(0,))
            self.assertEqual(first["scms"][0]["attempt_count"], 1)
            self.assertEqual(again["scms"][0]["attempt_count"], 1)
            self.assertEqual(first["scms"][0]["result_sha256"], again["scms"][0]["result_sha256"])
            db = sqlite3.connect(root / "research_c_fixture_cohort.sqlite")
            transitions = db.execute(
                "SELECT from_status,to_status FROM events WHERE run_id='replay-v1' AND scm_id='fixed-scm' ORDER BY event_id"
            ).fetchall()
            db.close()
            self.assertEqual(transitions, [(None, "PROPOSED"), ("PROPOSED", "ADMITTED"),
                                           ("ADMITTED", "RUNNING"), ("RUNNING", "COMPLETED")])
            with self.assertRaises(cr.LedgerConflict):
                run_test_only_cohort(root, run_id="replay-v1", master_seed=5,
                                     fixtures={"fixed-scm": make_fixed_fixture}, budgets=(1,))

            db = sqlite3.connect(root / "research_c_fixture_cohort.sqlite")
            value = db.execute("SELECT result_json FROM scms WHERE run_id='replay-v1'").fetchone()[0]
            db.execute("UPDATE scms SET result_json=? WHERE run_id='replay-v1'",
                       (value[:-2] + "xx",))
            db.commit(); db.close()
            with self.assertRaises(CohortIntegrityError):
                read_test_only_cohort(root, run_id="replay-v1")

    def test_one_scm_failure_is_recorded_and_does_not_corrupt_other_scm(self):
        def bad_factory():
            raise RuntimeError("fixture-specific injected failure")
        with tempfile.TemporaryDirectory() as directory:
            result = run_test_only_cohort(Path(directory), run_id="isolation-v1", master_seed=7,
                                          fixtures={"bad-scm": bad_factory,
                                                    "good-scm": make_fixed_fixture},
                                          budgets=(0,))
            self.assertEqual(result["counts"]["failed"], 1)
            self.assertEqual(result["counts"]["completed"], 1)
            self.assertTrue(result["scms"][0]["failure_reason"].startswith("RuntimeError:"))
            self.assertEqual(result["scms"][1]["status"], "COMPLETED")

    def test_partial_policy_vector_is_failed_not_completed(self):
        original = cr.execute_fixture_input
        def incomplete(*args, **kwargs):
            payload = original(*args, **kwargs)
            payload["e2e_result"]["budgets"][0]["policy_vector_status"] = "INCOMPLETE"
            return payload
        with tempfile.TemporaryDirectory() as directory, patch.object(cr, "execute_fixture_input", incomplete):
            result = run_test_only_cohort(Path(directory), run_id="partial-v1", master_seed=8,
                                          fixtures={"partial-scm": make_fixed_fixture}, budgets=(0,))
            self.assertEqual(result["counts"]["failed"], 1)
            self.assertEqual(result["completed_scm_count"], 0)
            self.assertIn("CohortIntegrityError", result["scms"][0]["failure_reason"])

    def test_subprocess_kill_and_resume_matches_uninterrupted_run(self):
        repo_root = Path(__file__).resolve().parents[1]
        for stage in ("after_claim", "before_commit"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as interrupted_dir, \
                    tempfile.TemporaryDirectory() as uninterrupted_dir:
                root = Path(interrupted_dir)
                signal = root / "hook_entered"
                code = r'''
import sys,time
from pathlib import Path
from research.original_objective.cohort_runner import run_test_only_cohort
from research.original_objective.fixed_fixture_data import make_fixed_fixture, make_nondegenerate_fixture
root, signal, stage = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
def hook(scm_id):
    if scm_id == "nondegenerate-scm":
        signal.write_text("entered", encoding="utf-8")
        time.sleep(120)
hook.__test_only_fixture_hook__ = True
fixtures={"fixed-scm":make_fixed_fixture,"nondegenerate-scm":{"factory":make_nondegenerate_fixture,"apply_g0_generator":False}}
kw={"after_claim_hook":hook} if stage == "after_claim" else {"before_commit_hook":hook}
run_test_only_cohort(root,run_id="crash-resume-v1",master_seed=20261124,fixtures=fixtures,budgets=(0,1),**kw)
'''
                proc = subprocess.Popen([sys.executable, "-c", code, str(root), str(signal), stage],
                                        cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline and not signal.exists() and proc.poll() is None:
                        time.sleep(0.05)
                    self.assertTrue(signal.exists(), "child did not reach requested interruption point")
                    with self.assertRaises(cr.LedgerConflict):
                        run_test_only_cohort(root, run_id="crash-resume-v1", master_seed=20261124,
                                             fixtures=_fixtures(), budgets=(0, 1))
                    proc.terminate(); proc.wait(timeout=15)
                finally:
                    if proc.poll() is None:
                        proc.kill(); proc.wait(timeout=15)
                checkpoint = read_test_only_cohort(root, run_id="crash-resume-v1")
                self.assertEqual(checkpoint["scms"][0]["status"], "COMPLETED")
                self.assertEqual(checkpoint["scms"][1]["status"], "RUNNING")

                resumed = run_test_only_cohort(root, run_id="crash-resume-v1", master_seed=20261124,
                                               fixtures=_fixtures(), budgets=(0, 1))
                uninterrupted = run_test_only_cohort(Path(uninterrupted_dir),
                    run_id="crash-resume-v1", master_seed=20261124,
                    fixtures=_fixtures(), budgets=(0, 1))
                self.assertEqual(resumed["config_sha256"], uninterrupted["config_sha256"])
                self.assertEqual([s["result_sha256"] for s in resumed["scms"]],
                                 [s["result_sha256"] for s in uninterrupted["scms"]])
                self.assertEqual([s["input_sha256"] for s in resumed["scms"]],
                                 [s["input_sha256"] for s in uninterrupted["scms"]])
                self.assertEqual([s["attempt_count"] for s in resumed["scms"]], [1, 2])
                self.assertTrue(resumed["all_scm_complete"])


if __name__ == "__main__":
    unittest.main()
