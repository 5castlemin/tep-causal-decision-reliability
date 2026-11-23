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
from research.original_objective.proposal_pipeline import build_research_c_proposal
from research.original_objective import proposal_pipeline
from research.original_objective.e2e_fixture import _RESEARCH_EXECUTION_CAPABILITY
from scripts.prepare_research_c_manifest import prepare_manifest
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
            "FN_REV_only": {**truth},
            "zero_error": {**truth},
        }
        scenarios["FN_only"].pop(pe.pair("A", "B"))
        scenarios["FP_only"][pe.pair("A", "Y")] = ("A", "Y")
        scenarios["REV_only"].pop(pe.pair("A", "B"))
        scenarios["REV_only"][pe.pair("A", "B")] = ("B", "A")
        scenarios["FN_REV_only"].pop(pe.pair("A", "B"))
        scenarios["FN_REV_only"].pop(pe.pair("C", "D"))
        scenarios["FN_REV_only"][pe.pair("C", "D")] = ("D", "C")

        for name, estimate in scenarios.items():
            with self.subTest(name=name):
                events = pe.metrics(truth, estimate, "X", "Y", pe.Config())["events"]
                types = {kind for _, kind in events.values()}
                expected = {"FN_only": {"FN"}, "FP_only": {"FP"},
                            "REV_only": {"REV"},
                            "FN_REV_only": {"FN", "REV"},
                            "zero_error": set()}[name]
                self.assertEqual(types, expected)
                # Every named subset and the canonical reference is executable,
                # including subsets with zero eligible candidates.
                for subset in pe.catalog():
                    result = pe.run(truth, estimate, "X", "Y", 2, subset)
                    self.assertLessEqual(result["total_cost"], 2)
                pe.run(truth, estimate, "X", "Y", 2, pe.METRICS,
                       canonical=True)
                full = run_fixed_fixture(replace(fixture, initial_graph=estimate),
                                         budgets=(2,))["budgets"][0]
                self.assertEqual(full["policy_vector_status"], "COMPLETE")
                self.assertEqual(len(full["policies"]), 17)
                self.assertTrue(all(p["evaluation_status"] == "TEST_ONLY_OK"
                                    for p in full["policies"]))
                if name != "zero_error":
                    repair_metrics = {"FN_only": {"M1"}, "FP_only": {"M2"},
                                      "REV_only": {"M3"},
                                      "FN_REV_only": {"M1", "M3"}}[name]
                    s0_policy = next(p for p in full["policies"]
                                     if p["policy_id"] == "S0")
                    self.assertEqual(s0_policy["edit_log"], [])
                    self.assertEqual(s0_policy["total_edit_cost"], 0)
                    no_candidates = [p for p in full["policies"]
                                     if p["policy_id"] not in {"S0", "CANONICAL_ORACLE"}
                                     and not repair_metrics.intersection(
                                         p["policy_id"].split("+"))]
                    for policy in no_candidates:
                        self.assertEqual(policy["edit_log"], [])
                        self.assertEqual(policy["total_edit_cost"], 0)
                        self.assertEqual(policy["final_graph_sha256"],
                                         policy["initial_graph_sha256"])

    def test_research_c_proposal_builder_keeps_strict_task_and_records_q_common_flag(self):
        no_support = build_research_c_proposal(
            cohort="development", master_seed=0,
            proposal_id="test-only-search-0-0", attempt=0,
            template="chain_mediation", node_count=7)
        self.assertTrue(no_support["accepted"])
        self.assertFalse(no_support["q_common_eligible"])
        self.assertEqual(no_support["reason"], None)
        self.assertTrue(no_support["action"] and no_support["target"])
        self.assertIsNotNone(no_support["scm_id"])
        self.assertFalse(no_support["scm_generated"])
        self.assertEqual(no_support["q_recipe_counts"]["FN"], 0)

        common = build_research_c_proposal(
            cohort="development", master_seed=0,
            proposal_id="test-only-search-0-9", attempt=9,
            template="multiple_directed_paths", node_count=6)
        self.assertTrue(common["accepted"])
        self.assertTrue(common["q_common_eligible"])
        self.assertTrue(all(common["q_recipe_counts"][kind] > 0
                            for kind in ("FN", "FP", "REV")))

    def test_approved_proposal_stage_uses_research_c_a2_builder(self):
        stage = {"proposal_stage_complete": False}
        with patch.object(proposal_pipeline, "run_proposal_stage", return_value=stage) as run_stage:
            result = proposal_pipeline.run_approved_research_proposal_cohort(
                Path("unused-test-only-output"), run_id="development-test-a2",
                cohort_type="development", master_seed=0, target_admissions=1,
                proposal_cap=1, resource_limits=object(),
                _authorization=_RESEARCH_EXECUTION_CAPABILITY)
        self.assertEqual(result["classification"], "RESEARCH_COHORT_INCOMPLETE")
        self.assertIs(run_stage.call_args.kwargs["proposal_builder"],
                      build_research_c_proposal)

    def test_p1_b2_delta_is_s0_regret_minus_full_greedy_regret(self):
        fixture, _ = make_fixed_fixture()
        result = run_fixed_fixture(fixture, budgets=(0, 1, 2, 3, 4))
        row = result["budgets"][2]
        p1 = row["primary_comparison"]
        self.assertEqual(p1["contrast_id"], "P1_B2_S0_MINUS_FULL_GREEDY")
        self.assertEqual(p1["status"], "COMPLETE")
        by_id = {p["policy_id"]: p for p in row["policies"]}
        expected = (by_id["S0"]["evaluation"]["regret"] -
                    by_id["M1+M2+M3+M4"]["evaluation"]["regret"])
        self.assertAlmostEqual(p1["delta"], expected)
        self.assertEqual(row["primary_comparison"]["cohort_aggregation"],
                         "not_computed_by_single_SCM_runner")

    def test_runner_p1_record_binds_s0_and_full_greedy_to_same_inputs(self):
        fixture, metadata = make_fixed_fixture()
        payload = runner.execute_fixture_input(fixture, metadata=metadata,
            g0_seed=17, task_id="test-only-p1", budgets=(0, 1, 2, 3, 4),
            apply_g0_generator=False)
        p1 = payload["e2e_result"]["budgets"][2]["primary_comparison"]
        self.assertTrue(p1["same_conditions_for_pair"])
        self.assertEqual(p1["shared_conditions"]["observations_sha256"],
                         payload["input_binding"]["observations_sha256"])
        self.assertEqual(p1["shared_conditions"]["truth_spec_sha256"],
                         payload["input_binding"]["truth_spec_sha256"])

    def test_gt_evaluation_changes_do_not_change_repairs_or_recommendations(self):
        fixture, _ = make_fixed_fixture()
        base = run_fixed_fixture(fixture, budgets=(2,))["budgets"][0]
        changed_coefficients = dict(fixture.truth_spec["coefficients"])
        changed_coefficients["X->M"] *= -1.0
        altered_truth = {**fixture.truth_spec, "coefficients": changed_coefficients}
        altered_fixture = replace(fixture, truth_spec=altered_truth)
        altered = run_fixed_fixture(altered_fixture, budgets=(2,))["budgets"][0]
        base_by_id = {p["policy_id"]: p for p in base["policies"]}
        altered_by_id = {p["policy_id"]: p for p in altered["policies"]}
        self.assertEqual(set(base_by_id), set(altered_by_id))
        for policy_id in base_by_id:
            self.assertEqual(base_by_id[policy_id]["edit_log"],
                             altered_by_id[policy_id]["edit_log"])
            self.assertEqual(base_by_id[policy_id]["evaluation"]["selected_action"],
                             altered_by_id[policy_id]["evaluation"]["selected_action"])
            self.assertEqual(base_by_id[policy_id]["evaluation"]["selected_k"],
                             altered_by_id[policy_id]["evaluation"]["selected_k"])
        self.assertNotEqual(
            [p["evaluation"]["regret"] for p in base["policies"]],
            [p["evaluation"]["regret"] for p in altered["policies"]])

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

    def test_manifest_preparer_only_binds_existing_approved_config(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, _, config, _ = _approved_bundle(directory)
            output = Path(directory) / "prepared-manifest.json"
            with patch.object(runner, "_git_clean_except_build_artifacts", return_value=True):
                receipt = prepare_manifest(config_path, output)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["approval_status"], "USER_APPROVED")
            self.assertEqual(manifest["config_sha256"], runner._digest(config))
            self.assertEqual(manifest["source_revision"], runner._git_revision(runner.ROOT))
            self.assertFalse(receipt["research_execution_started"])
            self.assertEqual(config["contract_status"], "USER_APPROVED")
            self.assertEqual(manifest["excluded_untracked_paths"], [".build_reframed/"])

    def test_manifest_preparer_refuses_proposed_config_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, _, config, _ = _approved_bundle(directory)
            config["contract_status"] = "PROPOSED_NOT_APPROVED"
            config["research_cohort_execution_enabled"] = False
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = Path(directory) / "must-not-exist.json"
            with self.assertRaisesRegex(runner.ResearchModeBlocked, "JSON Schema"):
                prepare_manifest(config_path, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
