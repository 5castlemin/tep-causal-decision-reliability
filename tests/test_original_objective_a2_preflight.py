"""TEST_ONLY checks for A2 support handling and non-execution preflight."""
import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from research.original_objective import policy_engine as pe
from research.original_objective import runner
from research.original_objective.e2e_fixture import run_fixed_fixture
from research.original_objective.fixed_fixture_data import make_fixed_fixture
from research.budget_aware_refinement.step4c1_proposal import q_common_eligibility
from tests.test_original_objective_proposal_stage_gate import _approved_bundle


class A2PopulationFeasibilityTests(unittest.TestCase):
    def test_strict_task_without_q_common_recipe_support_is_structurally_valid(self):
        nodes = ("M", "P", "Q", "R", "X", "Y")
        edges = (("X", "M"), ("M", "Y"), ("P", "Q"), ("Q", "R"))
        support = q_common_eligibility(nodes, edges, "X", "Y")
        self.assertEqual(support["reason"], "missing_same_type_two_candidate_support")
        self.assertTrue(any(len(path) >= 3 for path in support["task_paths"]))

        truth = pe.state(edges)
        for subset in pe.catalog():
            result = pe.run(truth, truth, "X", "Y", 2, subset)
            self.assertEqual(result["edits"], [])
            self.assertEqual(result["total_cost"], 0)
            self.assertEqual(result["final_hash"], result["initial_hash"])
        canonical = pe.run(truth, truth, "X", "Y", 2, pe.METRICS,
                           canonical=True)
        self.assertEqual(canonical["edits"], [])
        self.assertEqual(canonical["total_cost"], 0)

    def test_zero_off_task_support_is_reported_na_not_as_an_official_zero_rate(self):
        truth = pe.state((("X", "M"), ("M", "Y")))
        result = pe.metrics(truth, truth, "X", "Y", pe.Config())
        self.assertIsNone(result["report"]["M1"]["value"])
        self.assertEqual(result["report"]["M1"]["na_reason"], "zero_denominator")
        self.assertIsNone(result["report"]["M2"]["value"])
        policy = pe.run(truth, truth, "X", "Y", 2, ("M1",))
        self.assertEqual(policy["edits"], [])
        self.assertEqual(policy["total_cost"], 0)
        self.assertEqual(policy["stop_reason"], "candidate_pool_exhausted")

    def test_each_single_error_type_and_multiple_missing_types_are_evaluable(self):
        fixture, meta = make_fixed_fixture()
        truth = meta["truth"]
        scenarios = {
            "FN_only": {**truth},
            "FP_only": {**truth},
            "REV_only": {**truth},
            "zero_error": {**truth},
        }
        scenarios["FN_only"].pop(pe.pair("A", "B"))
        scenarios["FP_only"][pe.pair("A", "Y")] = ("A", "Y")
        scenarios["REV_only"].pop(pe.pair("A", "B"))
        scenarios["REV_only"][pe.pair("A", "B")] = ("B", "A")

        for name, estimate in scenarios.items():
            with self.subTest(name=name):
                events = pe.metrics(truth, estimate, "X", "Y", pe.Config())["events"]
                types = {kind for _, kind in events.values()}
                expected = {"FN_only": {"FN"}, "FP_only": {"FP"},
                            "REV_only": {"REV"}, "zero_error": set()}[name]
                self.assertEqual(types, expected)
                # Every named subset and the canonical reference is executable,
                # including subsets with zero eligible candidates.
                for subset in pe.catalog():
                    result = pe.run(truth, estimate, "X", "Y", 2, subset)
                    self.assertLessEqual(result["total_cost"], 2)
                pe.run(truth, estimate, "X", "Y", 2, pe.METRICS,
                       canonical=True)

    def test_zero_error_g0_runs_all_policies_through_recommendation_and_gt_evaluation(self):
        fixture, meta = make_fixed_fixture()
        q_support = q_common_eligibility(
            fixture.truth_spec["nodes"], fixture.truth_spec["edges"],
            fixture.action, fixture.target)
        self.assertFalse(q_support["eligible"])
        self.assertEqual(q_support["reason"], "missing_same_type_two_candidate_support")
        self.assertEqual(q_support["recipe_counts"]["FN"], 0)
        no_error_fixture = replace(fixture, initial_graph=meta["truth"])
        result = run_fixed_fixture(no_error_fixture, budgets=(0, 2))
        row = result["budgets"][1]
        self.assertEqual(row["policy_vector_status"], "COMPLETE")
        self.assertEqual(len(row["policies"]), 17)
        self.assertEqual(next(p for p in row["policies"] if p["policy_id"] == "S0")[
            "candidate_status"], "NO_EDIT_POLICY")
        self.assertTrue(all(p["candidate_status"] == "NO_INITIAL_ERRORS"
                            for p in row["policies"] if p["policy_id"] != "S0"))
        for policy in row["policies"]:
            self.assertEqual(policy["edit_log"], [])
            self.assertEqual(policy["total_edit_cost"], 0)
            self.assertEqual(policy["final_graph_sha256"],
                             policy["initial_graph_sha256"])
            self.assertEqual(policy["evaluation_status"], "TEST_ONLY_OK")
            self.assertIsNotNone(policy["evaluation"]["regret"])
        s0_rows = [next(p for p in budget["policies"] if p["policy_id"] == "S0")
                   for budget in result["budgets"]]
        self.assertEqual(s0_rows[0]["final_graph_sha256"],
                         s0_rows[1]["final_graph_sha256"])
        self.assertEqual(s0_rows[0]["evaluation"]["regret"],
                         s0_rows[1]["evaluation"]["regret"])

    def test_one_candidate_with_budget_two_stops_as_exhausted_not_failure(self):
        fixture, _ = make_fixed_fixture()
        truth = pe.state(fixture.truth_spec["edges"])
        estimate = dict(truth)
        estimate.pop(pe.pair("A", "B"))
        one_error = replace(fixture, initial_graph=estimate)
        result = run_fixed_fixture(one_error, budgets=(2,))["budgets"][0]
        self.assertEqual(result["policy_vector_status"], "COMPLETE")
        for policy in result["policies"]:
            has_m1 = (policy["policy_id"] == "CANONICAL_ORACLE"
                      or "M1" in policy["policy_id"].split("+"))
            self.assertEqual(policy["repair_candidate_count"], int(has_m1))
            if policy["policy_id"] in {"M1", "M1+M2+M3+M4", "CANONICAL_ORACLE"}:
                self.assertEqual(len(policy["edit_log"]), 1)
                self.assertEqual(policy["total_edit_cost"], 1)
                self.assertEqual(policy["unused_budget"], 1)
                self.assertEqual(policy["stop_reason"], "candidate_pool_exhausted")
                self.assertEqual(policy["evaluation_status"], "TEST_ONLY_OK")


class ResearchPreflightTests(unittest.TestCase):
    def test_preflight_cli_without_bundle_fails_before_proposal_stage(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "run_research_c_runner.py"
        result = subprocess.run([sys.executable, str(script), "--mode", "preflight"],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("RESEARCH_PREFLIGHT_BLOCKED", result.stderr)
        self.assertIn("approved config and matching execution manifest are required",
                      result.stderr)

    def test_preflight_validates_bundle_without_creating_proposals_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, manifest_path, config, _ = _approved_bundle(directory)
            hook = Mock(side_effect=AssertionError("preflight must not dispatch"))
            with patch.object(runner, "_git_clean_except_build_artifacts", return_value=True):
                result = runner.run_research_mode(
                    approved_config_path=config_path,
                    execution_manifest_path=manifest_path,
                    _test_only_gate_orchestrator=type(
                        "Hook", (), {"__test_only_approval_gate_hook__": True,
                                     "__call__": lambda self, **kw: hook(**kw)})(),
                    validate_only=True)
            self.assertEqual(result["classification"], "RESEARCH_BUNDLE_PREFLIGHT_ONLY")
            self.assertFalse(result["proposal_generation_started"])
            self.assertFalse(result["scm_generation_started"])
            self.assertEqual(result["configuration_sha256"], runner._digest(config))
            self.assertFalse(Path(config["output_root"]).exists())
            hook.assert_not_called()

    def test_preflight_rejects_invalid_schema_without_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, manifest_path, config, manifest = _approved_bundle(directory)
            config["repair"]["unexpected"] = True
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manifest["config_sha256"] = runner._digest(config)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(runner, "_git_clean_except_build_artifacts", return_value=True):
                with self.assertRaisesRegex(runner.ResearchModeBlocked,
                                            "JSON Schema"):
                    runner.run_research_mode(approved_config_path=config_path,
                        execution_manifest_path=manifest_path, validate_only=True)


if __name__ == "__main__":
    unittest.main()
