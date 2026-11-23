"""TEST_ONLY checks for isolated proposal checkpoints and approval gate wiring."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from research.original_objective import runner
from research.original_objective.cohort_runner import run_proposal_stage
from research.original_objective.execution_limits import ResourceLimits
from research.original_objective.fixed_fixture_data import make_fixed_fixture
from research.original_objective.e2e_fixture import _RESEARCH_EXECUTION_CAPABILITY
from research.original_objective import proposal_pipeline
from research.budget_aware_refinement.step4c1_proposal import STRATA, proposal_stratum


def _proposal(cohort, master_seed, proposal_id, attempt):
    return {"cohort": cohort, "master_seed": master_seed,
            "proposal_id": proposal_id, "attempt": attempt, "accepted": False,
            "scm_id": None, "topology_hash": f"fixture-{attempt}"}


def _slow_proposal(cohort, master_seed, proposal_id, attempt):
    time.sleep(3)
    return _proposal(cohort, master_seed, proposal_id, attempt)


def _block_proposal_checkpoint(proposal_id):
    signal = Path(os.environ["DAT_PROPOSAL_TEST_SIGNAL"])
    signal.write_text(proposal_id, encoding="utf-8")
    time.sleep(120)


def _block_before_proposal_commit(proposal_id):
    signal = Path(os.environ["DAT_PROPOSAL_TEST_SIGNAL"])
    signal.write_text(proposal_id, encoding="utf-8")
    time.sleep(120)


_block_proposal_checkpoint.__test_only_fixture_hook__ = True
_block_before_proposal_commit.__test_only_fixture_hook__ = True


def _contract():
    from research.budget_aware_refinement.step4_topology_generator import TEMPLATES
    from research.budget_aware_refinement.step3_adapter import K
    return {
        "population": {"topology_source": "existing_step4_topology_generator_new_research_c_rng_namespace",
            "templates": list(TEMPLATES), "node_counts": [6, 7, 8, 9, 10],
            "target_edge_density": [0.2, 0.4],
            "task_rule": runner.TASK_RULE_ID,
            "eligibility_rule": "strict_indirect_only; allow_zero_fn_fp_rev_recipe_support"},
        "scm": {"family": "signed_linear_acyclic", "coefficient_abs_range": [0.25, 0.8],
            "sign_probability": "independent_fair_sign",
            "noise": {"family": "independent_centered_gaussian", "sd_range": [0.8, 1.2]},
            "observations": {"n": 512, "shared_across_policies": True,
                "training": "common_observational_sample",
                "evaluation": "analytic_GT_no_heldout_observational_loss"}},
        "task": {"action": runner.TASK_SELECTION_DESCRIPTOR,
            "target": runner.TASK_SELECTION_DESCRIPTOR,
            "delta": "alternating_by_admission_ordinal_within_new_cohort",
            "action_grid": list(K), "loss": "squared_standardized_target_mean_error_on_shared_grid"},
        "g0": {"true_adjacency_corruption_rate": 0.15, "false_adjacency_rate": 0.05,
            "true_error_mix": {"FN": 1/3, "REV": 1/3, "UNRES": 1/3},
            "fp_orientation": "fair_direction_draw; reject_if_cyclic",
            "dag_invalid": "record_and_reject_without_redraw", "retry_limit": 0},
        "repair": {"metric_subsets": "all_15_nonempty_subsets_plus_S0",
            "canonical_oracle": "separate_same_information_candidate_cost_budget_DAG_constraints",
            "normalization": "G0_fixed_opportunity_only",
            "metric_weights": "equal_selected_metric_weights",
            "m4_beta": "equal_active_FN_FP_REV_UNRES_components", "fp_rule": "A_only; Rule_B_excluded",
            "edit_costs": {"add": 1, "delete": 1, "orient": 1, "resolve": 1,
                           "delete_unresolved": 1}, "budgets": [0, 1, 2, 3, 4]},
        "evaluation": {"recommendation_input": "shared_observations_and_repaired_graph_only",
            "gt_evaluator": "analytic_hard_do_after_recommendation_frozen",
            "regret": "GT_selected_candidate_loss_minus_best_loss_on_same_grid",
            "primary_contrast": "B2_S0_minus_Full_Greedy_mean_SCM_paired_Regret_difference",
            "research_result_gate": "APPROVED_PREREGISTERED_EXECUTION"}}


def _approved_bundle(directory):
    root = Path(directory)
    output = root / "research-output"
    resource_limits = {"unit_timeout_seconds": 30, "scm_active_seconds": 90,
        "cohort_active_seconds": 120, "sampled_rss_bytes": 536870912,
        "max_result_bytes": 10000000, "max_ledger_bytes": 20000000,
        "max_cohort_storage_bytes": 30000000, "minimum_free_disk_bytes": 0,
        "failure_reserve_bytes": 4096, "max_concurrent_scms": 1}
    config = {"contract_status": "USER_APPROVED", "research_cohort_execution_enabled": True,
        "preregistration_status": "PREREGISTERED", "configuration_version": "research-c-execution-v1",
        "cohort_type": "development", "run_id": "development-test-gate-positive",
        "output_root": str(output.resolve()), **_contract(),
        "rng_protocol": {"master_seed": 1919, "cohort_namespace": "development",
                         "protocol_version": "step4-rng-v1"},
        "resource_limits": resource_limits, "runtime_fingerprint": runner._runtime_fingerprint(),
        "target_admissions": 1, "proposal_cap": 1, "budgets": [0, 1, 2, 3, 4]}
    config_path, manifest_path = root / "config.json", root / "manifest.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    contract_keys = ("configuration_version", "contract_status", "preregistration_status",
        "population", "scm", "task", "g0", "repair", "evaluation")
    manifest = {"approval_status": "USER_APPROVED", "manifest_version": "research-c-execution-manifest-v1",
        "config_sha256": runner._digest(config), "cohort_type": config["cohort_type"],
        "runtime_fingerprint": runner._runtime_fingerprint(),
        "excluded_untracked_paths": [".build_reframed/"],
        "source_revision": runner._git_revision(runner.ROOT),
        "code_sha256": runner._code_hashes(runner.ROOT),
        "configuration_version": config["configuration_version"],
        "contract_sha256": runner._digest({key: config[key] for key in contract_keys}),
        "resource_limits_sha256": runner._digest(config["resource_limits"]),
        "run_id": config["run_id"], "output_root": str(output.resolve())}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return config_path, manifest_path, config, manifest


def _refresh_manifest(config, manifest):
    keys = ("configuration_version", "contract_status", "preregistration_status",
        "population", "scm", "task", "g0", "repair", "evaluation")
    manifest["config_sha256"] = runner._digest(config)
    manifest["resource_limits_sha256"] = runner._digest(config["resource_limits"])
    if all(key in config for key in keys):
        manifest["contract_sha256"] = runner._digest({key: config[key] for key in keys})


class TestOnlyApprovalGateHook:
    __test_only_approval_gate_hook__ = True

    def __init__(self, output_root):
        self.called = False
        self.output_root = Path(output_root)

    def __call__(self, *, config, manifest, output_root, resource_limits):
        self.called = True
        self.assertions = (config["cohort_type"], manifest["approval_status"],
                           resource_limits.classification, output_root.name)
        from research.original_objective.proposal_pipeline import run_cohort_orchestration
        test_limits = ResourceLimits(30, 60, 90, 536870912, 10000000,
            20000000, 30000000, 0, failure_reserve_bytes=4096)
        return run_cohort_orchestration(self.output_root, mode="TEST_ONLY",
            run_id="test-only-approved-gate-hook", master_seed=919,
            fixtures={"fixed-test-only-scm": make_fixed_fixture}, budgets=(0,),
            resource_limits=test_limits)


class ProposalStageAndApprovalGateTests(unittest.TestCase):
    def setUp(self):
        self.limits = ResourceLimits(10, 20, 30, None, 1000000, 2000000,
                                     3000000, 0, failure_reserve_bytes=4096)

    def test_hierarchical_task_schema_and_validator_match_generator(self):
        from jsonschema import Draft202012Validator

        schema_dir = runner.ROOT / "research" / "original_objective"
        candidate_schema = json.loads((schema_dir /
            "research_c_candidate_config.schema.json").read_text(encoding="utf-8"))
        candidate = {"contract_status": "PROPOSED_NOT_APPROVED",
            "research_cohort_execution_enabled": False, **_contract()}
        candidate["evaluation"]["research_result_gate"] = (
            "BLOCK_UNTIL_USER_APPROVAL_AND_PREREGISTRATION")
        self.assertTrue(Draft202012Validator(candidate_schema).is_valid(candidate))

        legacy_rule = "uniform_over_all_strict_indirect_only_pairs; require_no_direct_X_to_Y_edge"
        legacy_candidate = json.loads(json.dumps(candidate))
        legacy_candidate["population"]["task_rule"] = legacy_rule
        self.assertFalse(Draft202012Validator(candidate_schema).is_valid(legacy_candidate))

        with tempfile.TemporaryDirectory() as directory:
            _, _, approved, _ = _approved_bundle(directory)
            runner._validate_supported_research_contract(approved)
            runner._validate_approved_config_schema(approved)

            legacy_approved = json.loads(json.dumps(approved))
            legacy_approved["population"]["task_rule"] = legacy_rule
            legacy_approved["task"]["action"] = "preselected_uniform_eligible_pair"
            legacy_approved["task"]["target"] = "preselected_uniform_eligible_pair"
            with self.assertRaises(runner.ResearchModeBlocked):
                runner._validate_supported_research_contract(legacy_approved)
            with self.assertRaises(runner.ResearchModeBlocked):
                runner._validate_approved_config_schema(legacy_approved)

    def test_hash_rejection_strata_assignment_is_deterministic_not_cyclic(self):
        self.assertEqual(len(STRATA), 20)
        expected = [
            ("fork_branch", 10), ("chain_mediation", 8),
            ("fork_branch", 9), ("observed_common_cause", 9),
            ("multiple_directed_paths", 7), ("observed_common_cause", 8),
        ]
        for i, wanted in enumerate(expected):
            proposal_id = f"test-only-stratum-check-{i:04d}"
            selected = proposal_stratum(cohort="development", master_seed=88002117,
                                        proposal_id=proposal_id)
            self.assertEqual(selected, wanted)
            self.assertEqual(selected, proposal_stratum(cohort="development",
                master_seed=88002117, proposal_id=proposal_id))
        observed = {proposal_stratum(cohort="development", master_seed=88002117,
            proposal_id=f"test-only-stratum-coverage-{i:04d}") for i in range(200)}
        self.assertEqual(observed, set(STRATA))

    def test_observed_common_cause_scaffold_preference_and_a2_recipe_support(self):
        proposal = proposal_pipeline.build_research_c_proposal(cohort="development",
            master_seed=88002117, proposal_id="test-only-scaffold-0000", attempt=0,
            template="observed_common_cause", node_count=6)
        self.assertEqual(proposal["action"], proposal["role_map"]["action"])
        self.assertEqual(proposal["target"], proposal["role_map"]["target"])
        self.assertNotIn((proposal["action"], proposal["target"]),
                         {tuple(edge) for edge in proposal["topology_edges"]})
        self.assertTrue(proposal["accepted"])
        self.assertFalse(proposal["q_common_eligible"])

    def test_proposal_checkpoint_is_deterministic_and_separate_from_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            first = run_proposal_stage(Path(directory), run_id="test-only-proposal-resume",
                cohort_type="TEST_ONLY", master_seed=17, target_admissions=1, proposal_cap=1,
                resource_limits=self.limits, proposal_builder=_proposal)
            again = run_proposal_stage(Path(directory), run_id="test-only-proposal-resume",
                cohort_type="TEST_ONLY", master_seed=17, target_admissions=1, proposal_cap=1,
                resource_limits=self.limits, proposal_builder=_proposal)
            self.assertTrue(first["proposal_stage_complete"])
            self.assertEqual(first["proposal_stage_status"], "SHORTFALL_PROPOSAL_CAP")
            self.assertEqual(first["eligible_count"], 0)
            self.assertEqual(len(first["proposals"]), 1)
            self.assertEqual(first["proposals"], again["proposals"])
            self.assertEqual(first["config_sha256"], again["config_sha256"])
            self.assertEqual(len(again["proposal_checkpoints"]), 1)
            self.assertEqual(again["proposal_checkpoints"][0]["status"], "STRUCTURALLY_INELIGIBLE")

    def test_default_structural_proposal_generator_runs_in_isolated_test_only_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_proposal_stage(Path(directory), run_id="test-only-real-proposal-generator",
                cohort_type="TEST_ONLY", master_seed=20261123, target_admissions=1,
                proposal_cap=1, resource_limits=self.limits)
            self.assertTrue(result["proposal_stage_complete"])
            self.assertEqual(result["proposal_count"], 1)
            proposal = result["proposals"][0]
            self.assertEqual(proposal["cohort"], "development")
            self.assertEqual(proposal["proposal_id"], "development-proposal-000001")
            self.assertIn(proposal["accepted"], (True, False))
            self.assertEqual(result["proposal_checkpoints"][0]["status"],
                "ELIGIBLE" if proposal["accepted"] else "STRUCTURALLY_INELIGIBLE")

    def test_proposal_worker_timeout_records_resource_stop_without_admission(self):
        limits = ResourceLimits(.3, 2, 5, None, 1000000, 2000000,
                                3000000, 0, failure_reserve_bytes=4096)
        with tempfile.TemporaryDirectory() as directory:
            result = run_proposal_stage(Path(directory), run_id="test-only-proposal-timeout",
                cohort_type="TEST_ONLY", master_seed=18, target_admissions=1, proposal_cap=1,
                resource_limits=limits, proposal_builder=_slow_proposal)
            self.assertFalse(result["proposal_stage_complete"])
            self.assertEqual(result["stop_reason"], "UNIT_TIMEOUT")
            self.assertEqual(result["eligible_count"], 0)
            self.assertEqual(result["proposal_checkpoints"][0]["status"], "RESOURCE_LIMIT")

    def test_proposal_rss_limit_is_sampled_and_fail_closed(self):
        limits = ResourceLimits(10, 20, 30, 1, 1000000, 2000000,
                                3000000, 0, failure_reserve_bytes=4096)
        with tempfile.TemporaryDirectory() as directory:
            result = run_proposal_stage(Path(directory), run_id="test-only-proposal-rss",
                cohort_type="TEST_ONLY", master_seed=19, target_admissions=1, proposal_cap=1,
                resource_limits=limits, proposal_builder=_proposal)
            self.assertFalse(result["proposal_stage_complete"])
            self.assertEqual(result["stop_reason"], "SAMPLED_RSS_CAP")
            self.assertEqual(result["eligible_count"], 0)

    def test_proposal_stage_must_complete_before_cohort_admission_and_time_is_carried(self):
        research_limits = ResourceLimits(10, 20, 30, None, 1000000, 2000000,
            3000000, 0, failure_reserve_bytes=4096,
            classification="USER_APPROVED_RESEARCH_RESOURCE_PROFILE")
        incomplete = {"proposal_stage_complete": False, "proposal_stage_status": "RESOURCE_STOP",
            "stop_reason": "UNIT_TIMEOUT", "proposals": [], "proposal_active_seconds": 1.0}
        with patch.object(proposal_pipeline, "run_proposal_stage", return_value=incomplete), \
                patch.object(proposal_pipeline, "run_cohort_orchestration") as cohort:
            result = proposal_pipeline.run_approved_research_proposal_cohort(
                Path("unused"), run_id="development-unit-test", cohort_type="development",
                master_seed=22, target_admissions=1, proposal_cap=1, budgets=(0,),
                resource_limits=research_limits, _authorization=_RESEARCH_EXECUTION_CAPABILITY)
        self.assertFalse(result["all_scm_complete"])
        cohort.assert_not_called()

        proposal = {"proposal_id": "development-proposal-000001", "cohort": "development",
            "attempt": 0, "accepted": True, "scm_id": "test-generated-scm",
            "nodes": ["X", "M", "Y"], "template": "chain_mediation", "node_count": 3,
            "topology_hash": "fixture", "topology_edges": [["X", "M"], ["M", "Y"]],
            "action": "X", "target": "Y"}
        complete = {"proposal_stage_complete": True, "proposal_stage_status": "COMPLETED",
            "stop_reason": None, "proposals": [proposal], "proposal_active_seconds": 12.75,
            "proposal_count": 1, "eligible_count": 1, "shortfall": 0,
            "config_sha256": "a" * 64, "database_path": "TEST_ONLY_MOCK"}
        expected_result = {"completed_scm_count": 1, "all_scm_complete": True,
            "classification": "RESEARCH_COHORT_RESULT"}
        with patch.object(proposal_pipeline, "run_proposal_stage", return_value=complete), \
                patch.object(proposal_pipeline, "run_cohort_orchestration",
                             return_value=expected_result) as cohort:
            proposal_pipeline.run_approved_research_proposal_cohort(
                Path("unused"), run_id="development-unit-test", cohort_type="development",
                master_seed=22, target_admissions=1, proposal_cap=1, budgets=(0,),
                resource_limits=research_limits, _authorization=_RESEARCH_EXECUTION_CAPABILITY)
        self.assertEqual(cohort.call_args.kwargs["proposal_active_seconds"], 12.75)
        self.assertEqual(cohort.call_args.kwargs["fixtures"]["test-generated-scm"]["apply_g0_generator"], False)

    def test_proposal_process_kill_and_resume_preserves_proposal_identity(self):
        repo_root = Path(__file__).resolve().parents[1]
        for hook_name in ("after", "before"):
            with self.subTest(hook=hook_name), tempfile.TemporaryDirectory() as interrupted_dir, \
                    tempfile.TemporaryDirectory() as uninterrupted_dir:
                root = Path(interrupted_dir)
                signal = root / "proposal-hook-entered"
                hook = ("_block_proposal_checkpoint" if hook_name == "after"
                        else "_block_before_proposal_commit")
                code = f'''\
import sys
from pathlib import Path
import importlib
from research.original_objective.cohort_runner import run_proposal_stage
from research.original_objective.execution_limits import ResourceLimits
sys.path.insert(0,str(Path(sys.argv[3]) / "tests"))
module=importlib.import_module(sys.argv[2])
proposal_builder=getattr(module,"_proposal")
hook=getattr(module,"{hook}")
root=Path(sys.argv[1])
limits=ResourceLimits(30,60,90,None,1000000,2000000,3000000,0,failure_reserve_bytes=4096)
run_proposal_stage(root,run_id="test-only-proposal-crash-{hook_name}",cohort_type="TEST_ONLY",
 master_seed=21,target_admissions=1,proposal_cap=1,resource_limits=limits,
 proposal_builder=proposal_builder,{"after_proposal_checkpoint_hook" if hook_name == "after" else "before_proposal_commit_hook"}=hook)
'''
                env = os.environ.copy()
                env["DAT_PROPOSAL_TEST_SIGNAL"] = str(signal)
                proc = subprocess.Popen([sys.executable, "-c", code, str(root), __name__, str(repo_root)], cwd=repo_root,
                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline and not signal.exists() and proc.poll() is None:
                        time.sleep(.05)
                    self.assertTrue(signal.exists(), "proposal worker did not reach interruption hook")
                    proc.terminate(); proc.wait(timeout=15)
                finally:
                    if proc.poll() is None:
                        proc.kill(); proc.wait(timeout=15)
                limits = ResourceLimits(30,60,90,None,1000000,2000000,3000000,0,
                                        failure_reserve_bytes=4096)
                resumed = run_proposal_stage(root,
                    run_id=f"test-only-proposal-crash-{hook_name}", cohort_type="TEST_ONLY",
                    master_seed=21,target_admissions=1,proposal_cap=1,
                    resource_limits=limits,proposal_builder=_proposal)
                uninterrupted = run_proposal_stage(Path(uninterrupted_dir),
                    run_id=f"test-only-proposal-crash-{hook_name}", cohort_type="TEST_ONLY",
                    master_seed=21,target_admissions=1,proposal_cap=1,
                    resource_limits=limits,proposal_builder=_proposal)
                self.assertEqual(resumed["proposals"], uninterrupted["proposals"])
                self.assertEqual(resumed["config_sha256"], uninterrupted["config_sha256"])
                self.assertEqual(resumed["proposal_count"], 1)
                self.assertEqual(len(resumed["proposal_checkpoints"]), 1)

    def test_validated_bundle_reaches_injected_test_only_orchestration(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, manifest_path, _, _ = _approved_bundle(directory)
            hook = TestOnlyApprovalGateHook(Path(directory) / "test-only-orchestration")
            with patch.object(runner, "_git_clean_except_build_artifacts", return_value=True):
                result = runner.run_research_mode(approved_config_path=config_path,
                    execution_manifest_path=manifest_path, _test_only_gate_orchestrator=hook)
            self.assertEqual(result["classification"], "TEST_ONLY_NOT_RESEARCH_COHORT")
            self.assertEqual(result["completed_scm_count"], 1)
            self.assertEqual(result["complete_policy_evaluations"], 17)
            self.assertTrue(hook.called)
            self.assertEqual(hook.assertions[0:3], ("development", "USER_APPROVED",
                "USER_APPROVED_RESEARCH_RESOURCE_PROFILE"))

    def test_mismatched_approval_manifest_and_unapproved_bundle_fail_closed(self):
        for mutation in ("approval", "config_hash", "source_revision", "cohort", "runtime"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                config_path, manifest_path, config, manifest = _approved_bundle(directory)
                if mutation == "approval": manifest["approval_status"] = "NOT_APPROVED"
                elif mutation == "config_hash": manifest["config_sha256"] = "0" * 64
                elif mutation == "source_revision": manifest["source_revision"] = {"commit": "wrong", "tree": "wrong"}
                elif mutation == "cohort": manifest["cohort_type"] = "independent_evaluation"
                else: manifest["runtime_fingerprint"] = {"python_version": "0"}
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                hook = TestOnlyApprovalGateHook(Path(directory) / "blocked-test-only")
                with patch.object(runner, "_git_clean_except_build_artifacts", return_value=True):
                    with self.assertRaises(runner.ResearchModeBlocked):
                        runner.run_research_mode(approved_config_path=config_path,
                            execution_manifest_path=manifest_path,
                            _test_only_gate_orchestrator=hook)
                self.assertFalse(hook.called)

    def test_missing_contract_resources_rng_and_test_output_conflicts_fail_closed(self):
        for mutation in ("missing_contract", "rng", "resources", "test_output"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                config_path, manifest_path, config, manifest = _approved_bundle(directory)
                if mutation == "missing_contract":
                    del config["task"]
                    _refresh_manifest(config, manifest)
                elif mutation == "rng":
                    config["rng_protocol"]["cohort_namespace"] = "independent_evaluation"
                    _refresh_manifest(config, manifest)
                elif mutation == "resources":
                    config["resource_limits"] = {}
                    _refresh_manifest(config, manifest)
                else:
                    conflict_root = Path(config["output_root"])
                    conflict_root.mkdir(parents=True)
                    (conflict_root / "research_c_fixture_proposals.sqlite").write_bytes(b"TEST_ONLY")
                config_path.write_text(json.dumps(config), encoding="utf-8")
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                hook = TestOnlyApprovalGateHook(Path(directory) / "blocked-test-only")
                with patch.object(runner, "_git_clean_except_build_artifacts", return_value=True):
                    with self.assertRaises(runner.ResearchModeBlocked):
                        runner.run_research_mode(approved_config_path=config_path,
                            execution_manifest_path=manifest_path,
                            _test_only_gate_orchestrator=hook)
                self.assertFalse(hook.called)


if __name__ == "__main__":
    unittest.main()
