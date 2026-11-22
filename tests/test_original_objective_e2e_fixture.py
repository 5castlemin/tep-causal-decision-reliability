"""Fixed TEST_ONLY bridge checks; never sample a study cohort."""
import unittest
import inspect
import json
from pathlib import Path
from unittest.mock import patch

from research.original_objective import policy_engine as pe
from research.original_objective.e2e_fixture import run_fixed_fixture, run_research_cohort
from research.original_objective.fixed_fixture_data import make_fixed_fixture
from research.original_objective.g0_candidate import corrupt_graph_candidate


class G0CandidateTests(unittest.TestCase):
    def test_deterministic_dag_and_complete_rejection_record(self):
        fixture, meta = make_fixed_fixture()
        truth, nodes = meta["truth"], meta["nodes"]
        a = corrupt_graph_candidate(truth, nodes=nodes, action="X", target="Y",
                                    master_seed=44, task_id="fixed-task")
        b = corrupt_graph_candidate(truth, nodes=nodes, action="X", target="Y",
                                    master_seed=44, task_id="fixed-task")
        self.assertEqual(a, b)
        graph = a["initial_graph"]
        self.assertTrue(pe.dag(graph))
        self.assertEqual(a["status"], "PROPOSED_NOT_APPROVED")
        self.assertEqual(a["summary"]["attempted"], len(a["attempted_events"]))
        self.assertEqual(a["summary"]["retries"], 0)
        self.assertEqual(a["summary"]["applied"] + a["summary"]["rejected_dag"],
                         a["summary"]["attempted"])
        self.assertEqual(len({tuple(row["pair"]) for row in a["attempted_events"]}),
                         len(a["attempted_events"]))

    def test_dag_invalid_corruption_is_recorded_without_resampling(self):
        fixture, meta = make_fixed_fixture()
        result = corrupt_graph_candidate(meta["truth"], nodes=meta["nodes"], action="X", target="Y",
                                         master_seed=91, task_id="all-pairs-test",
                                         true_corruption_rate=1.0, false_adjacency_rate=1.0)
        self.assertTrue(pe.dag(result["initial_graph"]))
        self.assertEqual(result["summary"]["retries"], 0)
        self.assertGreater(result["summary"]["rejected_dag"], 0)
        self.assertEqual(result["summary"]["attempted"],
                         result["summary"]["true_adjacencies_considered"]+
                         result["summary"]["false_pairs_considered"])


class EndToEndFixedFixtureTests(unittest.TestCase):
    def test_hand_expected_metric_events_are_singly_attributed(self):
        fixture, meta = make_fixed_fixture()
        stats = pe.metrics(meta["truth"], fixture.initial_graph, fixture.action,
                           fixture.target, pe.Config())
        self.assertEqual(stats["counts"]["M1"]["FN"], 1)
        self.assertEqual(stats["counts"]["M2"]["FP"], 1)
        self.assertEqual(stats["counts"]["M3"]["REV"], 1)
        self.assertEqual(stats["counts"]["M4"]["FN"], 1)
        self.assertEqual(stats["counts"]["M4"]["REV"], 1)
        self.assertEqual(sum(sum(row.values()) for row in stats["counts"].values()), 5)

    def test_full_catalog_graph_fit_recommend_gt_and_regret_are_test_only(self):
        fixture, _ = make_fixed_fixture()
        first = run_fixed_fixture(fixture, budgets=(0, 1, 2, 3, 4))
        second = run_fixed_fixture(fixture, budgets=(0, 1, 2, 3, 4))
        self.assertEqual(first, second)
        self.assertTrue(first["test_only"])
        self.assertFalse(first["research_cohort_generated"])
        self.assertFalse(first["regret_research_result"])
        fitted_graphs = {policy["fit_graph_sha256"] for budget in first["budgets"]
                         for policy in budget["policies"] if "fit_graph_sha256" in policy}
        self.assertEqual(first["model_cache_entries"], len(fitted_graphs),
                         "model cache is keyed by distinct final graph and shared inputs")
        self.assertGreaterEqual(first["model_cache_entries"], 1)
        self.assertEqual(first["model_cache_entries"], len({
            p["fit_graph_sha256"] for budget in first["budgets"] for p in budget["policies"]
            if p["evaluation_status"] == "TEST_ONLY_OK"}))
        for budget in first["budgets"]:
            self.assertEqual(len(budget["policies"]), 17)
            for policy in budget["policies"]:
                self.assertTrue(policy["test_only"])
                self.assertLessEqual(policy["total_edit_cost"], policy["budget"])
                if policy["evaluation_status"] == "TEST_ONLY_OK":
                    self.assertEqual(policy["training_data_sha256"], first["input"]["observations_sha256"])
                    self.assertEqual(policy["fit_graph_sha256"], policy["final_graph_sha256"])
                    self.assertAlmostEqual(policy["evaluation"]["regret"],
                                           policy["evaluation"]["gt_selected_loss"]-
                                           policy["evaluation"]["gt_best_loss"], places=12)
                    self.assertGreaterEqual(policy["evaluation"]["regret"], -1e-12)
                else:
                    self.assertIsNone(policy["evaluation"])

    def test_research_cohort_entry_is_fail_closed(self):
        with self.assertRaisesRegex(PermissionError, "RESEARCH_C_COHORT_BLOCKED"):
            run_research_cohort(cohort="development")

    def test_candidate_schema_is_valid_json_and_disables_research_execution(self):
        path = Path(__file__).resolve().parents[1] / "research/original_objective/research_c_candidate_config.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["contract_status"]["const"], "PROPOSED_NOT_APPROVED")
        self.assertIs(schema["properties"]["research_cohort_execution_enabled"]["const"], False)

    def test_error_free_graph_is_distinct_from_empty_candidate_pool(self):
        fixture, meta = make_fixed_fixture()
        no_error = type(fixture)(fixture.truth_spec, meta["truth"], fixture.observations,
                                 fixture.action, fixture.target, fixture.delta, True)
        result = run_fixed_fixture(no_error, budgets=(0,))
        statuses = {row["candidate_status"] for row in result["budgets"][0]["policies"]}
        self.assertEqual(statuses, {"NO_INITIAL_ERRORS", "NO_EDIT_POLICY"})
        self.assertEqual({p["candidate_status"] for p in result["budgets"][0]["policies"]
                          if p["policy_id"] != "S0"}, {"NO_INITIAL_ERRORS"})

    def test_residual_unresolved_state_fails_closed_before_fit(self):
        fixture, meta = make_fixed_fixture()
        unresolved = pe.state([("A", "B"), ("C", "D"), ("X", "M"), ("M", "Y"), ("Z", "Y")],
                              unresolved=[("Z", "X")])
        modified = type(fixture)(fixture.truth_spec, unresolved, fixture.observations,
                                 fixture.action, fixture.target, fixture.delta, True)
        result = run_fixed_fixture(modified, budgets=(0,))
        statuses = {p["status"] for p in result["budgets"][0]["policies"]}
        self.assertEqual(statuses, {"GRAPH_INPUT_UNSUPPORTED"})

    def test_model_fit_failure_is_recorded_without_gt_evaluation(self):
        fixture, _ = make_fixed_fixture()
        with patch("research.original_objective.e2e_fixture.fit_model",
                   side_effect=RuntimeError("fixture fit sentinel")):
            result = run_fixed_fixture(fixture, budgets=(0,))
        for row in result["budgets"][0]["policies"]:
            self.assertEqual(row["status"], "MODEL_FIT_FAILURE")
            self.assertEqual(row["evaluation_status"], "NOT_EVALUATED")
            self.assertIsNone(row["evaluation"])

    def test_policy_schedule_signature_has_no_outcome_inputs(self):
        parameters = set(inspect.signature(pe.run).parameters)
        forbidden = {"gt_loss", "gt_regret", "intervention_effect", "gt_selected_loss"}
        self.assertTrue(parameters.isdisjoint(forbidden))
        result = pe.run(pe.state([("X", "M"), ("M", "Y")]),
                        pe.state([("M", "Y")]), "X", "Y", 1, ("M1",))
        self.assertIsNone(result["evaluation"]["decision_regret"])
        self.assertIsNone(result["evaluation"]["gt_selected_loss"])


if __name__ == "__main__":
    unittest.main()
