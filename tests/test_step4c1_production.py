import unittest
import hashlib

import numpy as np

from research.budget_aware_refinement.run_step4b4_mock_pipeline import MOCK_CONFIG, MOCK_INPUT_SHA256, build_mock_stages
from research.budget_aware_refinement.step4b4_mock_runner import LedgerConflict, run_pipeline
from research.budget_aware_refinement.step4c1_evaluation import evaluate_frozen_pair, evaluate_policy_pair
from research.budget_aware_refinement.step4c1_proposal import q_common_eligibility, proposal_stratum
from src.integrated_pilot import fit_model
from src.decision_mvp import static_mean_response


class Step4C1ProductionIntegrationTests(unittest.TestCase):
    def test_same_run_id_does_not_restore_another_run_stage(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as td:
            ledger = Path(td) / "shared.jsonl"
            run_pipeline("run-a", ledger, build_mock_stages(ledger, "run-a"),
                         config=MOCK_CONFIG, input_sha256=MOCK_INPUT_SHA256, scm_id="dev-scm-a")
            run_pipeline("run-b", ledger, build_mock_stages(ledger, "run-b"),
                         config=MOCK_CONFIG, input_sha256=MOCK_INPUT_SHA256, scm_id="dev-scm-b")
            with self.assertRaises(LedgerConflict):
                run_pipeline("run-a", ledger, build_mock_stages(ledger, "run-a"),
                             config=MOCK_CONFIG, input_sha256="different-input")
            with self.assertRaises(LedgerConflict):
                run_pipeline("run-c", ledger, build_mock_stages(ledger, "run-c"),
                             config=MOCK_CONFIG, input_sha256=MOCK_INPUT_SHA256, scm_id="dev-scm-a")

    def test_fixed_topology_q_eligibility_and_proposal_stratum_are_outcome_blind(self):
        nodes = ("M", "P", "Q", "R", "X", "Y")
        truth = {("X", "Y"), ("X", "M"), ("M", "Y"), ("P", "Q")}
        result = q_common_eligibility(nodes, truth, "X", "Y")
        self.assertTrue(result["eligible"])
        self.assertTrue(all(result["recipe_counts"][k] > 0 for k in ("FN", "FP", "REV")))
        self.assertEqual(proposal_stratum(cohort="development", master_seed=91,
                                          proposal_id="dev-proposal-fixture"),
                         proposal_stratum(cohort="development", master_seed=91,
                                          proposal_id="dev-proposal-fixture"))
        self.assertNotEqual(proposal_stratum(cohort="development", master_seed=91,
                                             proposal_id="dev-proposal-fixture"),
                            proposal_stratum(cohort="confirmation", master_seed=91,
                                             proposal_id="rep-proposal-fixture"))

    def test_frozen_pair_uses_same_gt_grid_and_nonfinite_truth_fails(self):
        candidates = [{"k": 0.0, "action": 0.0}, {"k": 1.0, "action": 1.0}]
        global_selection = {"action": "A", "target_node": "Y", "target": 2.0,
                            "sd_y": 1.0, "candidates": candidates, "selected_k": 0.0}
        task_selection = {**global_selection, "selected_k": 1.0}
        calls = []
        def truth(_spec, action, value):
            calls.append((action, value))
            return {"Y": 2.0 * value}
        result = evaluate_frozen_pair(global_selection=global_selection,
                                      task_focused_selection=task_selection,
                                      truth_spec={}, analytic_response=truth)
        self.assertEqual(result["paired_status"], "OK")
        self.assertEqual(result["global"]["regret"], 4.0)
        self.assertEqual(result["task_focused"]["regret"], 0.0)
        self.assertEqual(len(calls), 4)
        failed = evaluate_frozen_pair(global_selection=global_selection,
            task_focused_selection=task_selection, truth_spec={},
            analytic_response=lambda *_: {"Y": float("inf")})
        self.assertEqual(failed["paired_status"], "INCOMPLETE")
        self.assertEqual(failed["global"]["status"], "GT_EVAL_FAIL")
        self.assertIsNone(failed["difference"])

    def test_step3_fit_and_recommendation_are_shared_before_truth_evaluation(self):
        n = 80
        t = np.arange(n, dtype=float)
        data = np.column_stack((t + np.sin(t), .4*t + np.cos(.2*t), .7*t + np.sin(.3*t)))
        nodes = ["A", "M", "Y"]
        request = {"node_ids": nodes, "initial_edges": [["M", "Y"]],
                   "reference_edges": [["A", "M"], ["M", "Y"]],
                   "allowed_types": ["FN"], "budget": 1, "gamma": 1,
                   "action": "A", "target": "Y", "seed": 4}
        evaluator_calls = []
        def analytic(_spec, action, value):
            evaluator_calls.append((action, value))
            return {"Y": 2.0 * value}
        result = evaluate_policy_pair(request=request, global_policy_id="G-FN",
            task_focused_policy_id="T-FN", data=data, columns=nodes, schema=nodes,
            delta=1, truth_spec={}, fit_model=fit_model,
            response=static_mean_response, analytic_response=analytic)
        self.assertEqual(result["paired_status"], "OK")
        self.assertEqual(result["training_data_sha256"], hashlib.sha256(data.tobytes()).hexdigest())
        self.assertEqual(result["global_selection"]["candidates"],
                         result["task_focused_selection"]["candidates"])
        self.assertEqual(len(evaluator_calls), 10)


if __name__ == "__main__":
    unittest.main()
