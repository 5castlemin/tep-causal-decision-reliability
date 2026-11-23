"""Integration tests for the independent TEST_ONLY fixture runner."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from research.original_objective.runner import (
    ResearchModeBlocked, run_fixture_mode, run_research_mode,
    _digest,
)
from research.original_objective.proposal_pipeline import (
    build_approved_research_inputs, run_cohort_orchestration,
)
from research.original_objective.cohort_runner import run_approved_research_cohort
from research.original_objective.execution_limits import ResourceLimits


class ResearchCRunnerTests(unittest.TestCase):
    def test_fixture_runner_executes_e2e_and_writes_bound_results(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fixture.json"
            result = run_fixture_mode(output)
            wrapper = json.loads(output.read_text(encoding="utf-8"))
            payload = wrapper["payload"]
            self.assertEqual(result["classification"], "TEST_ONLY_NOT_RESEARCH_COHORT")
            self.assertEqual(result["policy_evaluation_count"], 85)
            self.assertTrue(result["all_policy_vectors_complete"])
            self.assertEqual(wrapper["payload_sha256"], _digest(payload))
            self.assertEqual(payload["config_sha256"], result["config_sha256"])
            self.assertEqual(payload["input_sha256"], result["input_sha256"])
            self.assertTrue(payload["e2e_result"]["regret_research_result"] is False)
            self.assertFalse(payload["research_cohort_generated"])
            self.assertEqual(len(payload["code_sha256"]), 23)
            for budget in payload["e2e_result"]["budgets"]:
                self.assertEqual(budget["policy_vector_status"], "COMPLETE")
                policies = budget["policies"]
                self.assertEqual(len(policies), 17)
                shared = {p["shared_input_sha256"] for p in policies}
                data = {p["shared_observations_sha256"] for p in policies}
                actions = {tuple(p["shared_action_candidates"]) for p in policies}
                self.assertEqual(len(shared), 1)
                self.assertEqual(len(data), 1)
                self.assertEqual(len(actions), 1)
                for policy in policies:
                    self.assertEqual(policy["evaluation_status"], "TEST_ONLY_OK")
                    self.assertIn("edit_log", policy)
                    self.assertIn("regret", policy["evaluation"])
                    self.assertEqual(policy["final_graph_sha256"],
                                     policy["structural_graph_sha256"])
                    self.assertEqual(policy["fit_graph_sha256"],
                                     policy["learner_graph_sha256"])
                    self.assertTrue(policy["unresolved_abstention"] is not None)
            with self.assertRaises(FileExistsError):
                run_fixture_mode(output)

    def test_repeat_run_has_identical_research_values_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            a_path, b_path = Path(directory) / "a.json", Path(directory) / "b.json"
            run_fixture_mode(a_path)
            run_fixture_mode(b_path)
            a, b = (json.loads(p.read_text(encoding="utf-8"))["payload"]
                    for p in (a_path, b_path))
            self.assertEqual(a["input_sha256"], b["input_sha256"])
            self.assertEqual(a["config_sha256"], b["config_sha256"])
            self.assertEqual(a["g0_generation"], b["g0_generation"])
            for left, right in zip(a["e2e_result"]["budgets"], b["e2e_result"]["budgets"]):
                self.assertEqual(left["policies"], right["policies"])

    def test_research_mode_fails_before_fixture_or_scm_factory(self):
        factory = Mock(side_effect=AssertionError("factory must not be called"))
        with self.assertRaises(ResearchModeBlocked):
            run_research_mode(approved_config_path=None,
                              execution_manifest_path=None,
                              fixture_factory=factory)
        factory.assert_not_called()

    def test_research_mode_rejects_proposed_config_before_factory(self):
        factory = Mock(side_effect=AssertionError("factory must not be called"))
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "candidate.json"
            manifest_path = Path(directory) / "manifest.json"
            config_path.write_text(json.dumps({
                "contract_status": "PROPOSED_NOT_APPROVED",
                "research_cohort_execution_enabled": False,
            }), encoding="utf-8")
            manifest_path.write_text(json.dumps({"approval_status": "NOT_APPROVED"}),
                                     encoding="utf-8")
            with self.assertRaises(ResearchModeBlocked):
                run_research_mode(approved_config_path=config_path,
                                  execution_manifest_path=manifest_path,
                                  fixture_factory=factory)
        factory.assert_not_called()

    def test_research_input_builder_records_admissions_without_drawing_scm(self):
        calls = []

        def proposal_builder(**kwargs):
            calls.append(kwargs)
            return {"proposal_id": kwargs["proposal_id"], "cohort": "development",
                    "master_seed": 41, "attempt": kwargs["attempt"], "nodes": ["X", "M", "Y"],
                    "template": "chain_mediation", "node_count": 3,
                    "topology_hash": "topology-test", "topology_edges": [["X", "M"], ["M", "Y"]],
                    "action": "X", "target": "Y", "accepted": True,
                    "scm_id": f"dev-scm-{kwargs['proposal_id']}"}

        built = build_approved_research_inputs(
            cohort_type="development", master_seed=41, target_admissions=1,
            proposal_cap=1, proposal_builder=proposal_builder)
        self.assertEqual(len(calls), 1)
        self.assertEqual(built["shortfall"], 0)
        self.assertEqual(len(built["admitted_factories"]), 1)
        row = built["proposal_outcomes"][0]
        self.assertEqual(row["status"], "ADMITTED")
        self.assertEqual(row["admission_ordinal"], 0)
        self.assertEqual(row["delta"], 1)
        # Factory is merely assembled here; no coefficients, observations,
        # G0, fitted model, interventions or Regret have been produced.
        self.assertFalse(row.get("coefficient_or_data_drawn", False))

    def test_research_ledger_requires_post_gate_capability_before_io(self):
        with tempfile.TemporaryDirectory() as directory:
            limits = ResourceLimits(
                5, 30, 60, 256 * 1024 * 1024, 1_000_000, 2_000_000,
                3_000_000, 0, classification="USER_APPROVED_RESEARCH_RESOURCE_PROFILE")
            with self.assertRaises(PermissionError):
                run_approved_research_cohort(
                    Path(directory), run_id="development-run", master_seed=1,
                    fixtures={}, resource_limits=limits, _authorization=None)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_shared_orchestration_core_runs_test_only_without_study_label(self):
        from research.original_objective.fixed_fixture_data import make_fixed_fixture

        with tempfile.TemporaryDirectory() as directory:
            limits = ResourceLimits(30, 60, 90, 512 * 1024 * 1024,
                                    10_000_000, 20_000_000, 30_000_000, 0)
            result = run_cohort_orchestration(
                Path(directory), mode="TEST_ONLY", run_id="test-only-shared-core",
                master_seed=661, fixtures={"fixed-scm": make_fixed_fixture},
                budgets=(0,), resource_limits=limits)
            self.assertEqual(result["classification"], "TEST_ONLY_NOT_RESEARCH_COHORT")
            self.assertEqual(result["completed_scm_count"], 1)
            self.assertEqual(result["complete_policy_evaluations"], 17)
            self.assertFalse(result["scms"][0]["result"]["research_cohort_generated"])


if __name__ == "__main__":
    unittest.main()
