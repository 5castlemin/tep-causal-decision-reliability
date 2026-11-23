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
            self.assertEqual(len(payload["code_sha256"]), 9)
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


if __name__ == "__main__":
    unittest.main()
