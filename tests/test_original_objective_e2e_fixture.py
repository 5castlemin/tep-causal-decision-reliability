"""Fixed TEST_ONLY bridge checks; never sample a study cohort."""
import unittest
import inspect
import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from research.original_objective import policy_engine as pe
from research.original_objective.e2e_fixture import run_fixed_fixture, run_research_cohort
from research.original_objective.fixed_fixture_data import make_fixed_fixture
from research.original_objective.g0_candidate import corrupt_graph_candidate
from research.original_objective.unresolved_completion_test_only import complete_unresolved_for_test_only


class G0CandidateTests(unittest.TestCase):
    def test_deterministic_dag_and_complete_rejection_record(self):
        fixture, meta = make_fixed_fixture()
        truth, nodes = meta["truth"], meta["nodes"]
        a = corrupt_graph_candidate(truth, nodes=nodes, action="X", target="Y",
                                    master_seed=44, task_id="fixed-task")
        b = corrupt_graph_candidate(truth, nodes=nodes, action="X", target="Y",
                                    master_seed=44, task_id="fixed-task")
        self.assertEqual(a, b)
        graph = pe.state(a["initial_graph"]["edges"], unresolved=a["initial_graph"]["unresolved"])
        self.assertTrue(pe.dag(graph))
        self.assertEqual(a["contract_status"], "PROPOSED_NOT_APPROVED")
        json.dumps(a, allow_nan=False)
        self.assertEqual(a["summary"]["proposed"], len(a["attempted_events"]))
        self.assertEqual(a["summary"]["retries"], 0)
        self.assertEqual(a["summary"]["accepted"] + a["summary"]["rejected_dag"],
                         a["summary"]["proposed"])
        self.assertEqual(len({tuple(row["pair"]) for row in a["attempted_events"]}),
                         len(a["attempted_events"]))

    def test_dag_invalid_corruption_is_recorded_without_resampling(self):
        fixture, meta = make_fixed_fixture()
        result = corrupt_graph_candidate(meta["truth"], nodes=meta["nodes"], action="X", target="Y",
                                         master_seed=91, task_id="all-pairs-test",
                                         true_corruption_rate=1.0, false_adjacency_rate=1.0)
        graph = pe.state(result["initial_graph"]["edges"], unresolved=result["initial_graph"]["unresolved"])
        self.assertTrue(pe.dag(graph))
        self.assertEqual(result["summary"]["retries"], 0)
        self.assertGreater(result["summary"]["rejected_dag"], 0)
        self.assertEqual(result["summary"]["proposed"],
                         result["summary"]["true_adjacencies_considered"]+
                         result["summary"]["false_pairs_considered"])

    def test_proposals_opportunities_and_realized_errors_reconcile(self):
        _, meta = make_fixed_fixture()
        result = corrupt_graph_candidate(meta["truth"], nodes=meta["nodes"], action="X", target="Y",
                                         master_seed=44, task_id="fixed-task")
        accepted = [r for r in result["attempted_events"] if r["acceptance_status"] == "accepted"]
        proposed_counts = Counter(r["kind"] for r in result["attempted_events"])
        accepted_counts = Counter(r["kind"] for r in accepted)
        realized_counts = Counter(k for row in result["realized_error_counts_by_metric"].values() for k, n in row.items() for _ in range(n))
        self.assertEqual(sum(proposed_counts.values()), result["summary"]["proposed"])
        self.assertEqual(sum(accepted_counts.values()), result["summary"]["accepted"])
        self.assertEqual({kind: accepted_counts[kind] for kind in ("FN", "FP", "REV", "UNRES")},
                         result["summary"]["accepted_by_kind"])
        # Every realized event is an accepted proposal; DAG rejection cannot silently redraw.
        self.assertEqual(dict(realized_counts), dict(accepted_counts))
        self.assertEqual(result["rates"]["configured"]["conditional_true_error_mix"],
                         {"FN": 1/3, "REV": 1/3, "UNRES": 1/3})
        self.assertIn("event_opportunities_by_metric_kind_and_zone", result)

    def test_zero_rate_is_recorded_as_zero_error_without_resampling(self):
        _, meta = make_fixed_fixture()
        result = corrupt_graph_candidate(meta["truth"], nodes=meta["nodes"], action="X", target="Y",
                                         master_seed=44, task_id="zero", true_corruption_rate=0,
                                         false_adjacency_rate=0)
        self.assertEqual(result["generation_status"], "NO_INITIAL_ERRORS")
        self.assertEqual(result["summary"]["proposed"], 0)
        self.assertEqual(result["summary"]["retries"], 0)


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

    def test_test_only_unresolved_completion_is_gt_blind_deterministic_and_fit_usable(self):
        fixture, meta = make_fixed_fixture()
        partial = pe.state([("C", "B"), ("B", "A")], unresolved=[("A", "C")])
        with self.assertRaises(PermissionError):
            complete_unresolved_for_test_only(partial, nodes=meta["nodes"])
        completed = complete_unresolved_for_test_only(partial, nodes=meta["nodes"], test_only=True)
        repeated = complete_unresolved_for_test_only(partial, nodes=meta["nodes"], test_only=True)
        self.assertEqual(completed, repeated)
        self.assertTrue(completed["gt_information_used"] is False)
        self.assertTrue(completed["outcome_information_used"] is False)
        self.assertTrue(completed["representation_transition_not_repair"])
        self.assertFalse(completed["charged_to_repair_budget"])
        self.assertEqual(completed["assignments"], [{"pair": ["A", "C"], "direction": ["C", "A"]}])
        self.assertTrue(pe.dag(pe.state(completed["completed_edges"])))

        # The adapter can now consume the completed directed graph, but no truth
        # or GT outcome is passed to recommendation. This is still TEST_ONLY.
        from research.budget_aware_refinement.step3_adapter import prepare
        from integrated_pilot import fit_model
        from decision_mvp import static_mean_response
        graph_result, selection = prepare(
            {"node_ids": list(meta["nodes"]), "action": fixture.action, "target": fixture.target},
            fixture.observations, list(meta["nodes"]), list(meta["nodes"]), fixture.delta,
            fit_model, static_mean_response,
            graph_result={"final_graph": completed["completed_edges"], "edit_sequence": []})
        self.assertEqual(selection["action"], "X")
        self.assertNotIn("gt_loss", selection)
        self.assertNotIn("regret", selection)

    def test_policy_pair_diagnostics_separate_graph_action_and_regret_ties(self):
        fixture, _ = make_fixed_fixture()
        result = run_fixed_fixture(fixture, budgets=(1,))
        row = result["budgets"][0]
        diagnostics = row["policy_comparison_diagnostics"]
        self.assertEqual(row["expected_policy_count"], 17)
        self.assertEqual(row["evaluable_policy_count"], 17)
        self.assertTrue(row["common_policy_comparison_allowed"])
        self.assertEqual(sum(diagnostics["tie_cause_categories"].values()), diagnostics["pair_count"])
        self.assertGreater(diagnostics["same_final_graph_pairs"], 0)
        self.assertIsNotNone(diagnostics["same_action_rate"])

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
