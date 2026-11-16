import unittest
import hashlib
import json
import subprocess
import sys

import numpy as np

from research.budget_aware_refinement.run_step4b4_mock_pipeline import MOCK_CONFIG, MOCK_INPUT_SHA256, build_mock_stages
from research.budget_aware_refinement.step4b4_mock_runner import LedgerConflict, run_pipeline
from research.budget_aware_refinement.step4c1_evaluation import evaluate_frozen_pair, evaluate_policy_pair
from research.budget_aware_refinement.step4c1_proposal import q_common_eligibility, proposal_stratum
from research.budget_aware_refinement.step4c1_gt import analytic_intervention_means
from research.budget_aware_refinement.step4c1_scm import (generate_observations,
    generate_scm_parameters, scm_signature)
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
        truth = {("X", "M"), ("M", "Y"), ("P", "Q"), ("Q", "R")}
        result = q_common_eligibility(nodes, truth, "X", "Y")
        self.assertNotEqual(result["reason"], "task_has_direct_edge")
        self.assertEqual(result["reason"], "missing_same_type_two_candidate_support")
        self.assertEqual(proposal_stratum(cohort="development", master_seed=91,
                                          proposal_id="dev-proposal-fixture"),
                         proposal_stratum(cohort="development", master_seed=91,
                                          proposal_id="dev-proposal-fixture"))
        self.assertNotEqual(proposal_stratum(cohort="development", master_seed=91,
                                             proposal_id="dev-proposal-fixture"),
                            proposal_stratum(cohort="confirmation", master_seed=91,
                                             proposal_id="rep-proposal-fixture"))

    def test_strict_indirect_only_rejects_direct_and_mixed_paths(self):
        nodes = ("X", "M", "Y", "P", "Q", "R")
        indirect = {("X", "M"), ("M", "Y"), ("P", "Q"), ("Q", "R")}
        direct = {("X", "Y"), ("P", "Q"), ("Q", "R")}
        both = indirect | {("X", "Y")}
        self.assertEqual(q_common_eligibility(nodes, indirect, "X", "Y")["reason"],
                         "missing_same_type_two_candidate_support")
        self.assertEqual(q_common_eligibility(nodes, direct, "X", "Y")["reason"],
                         "task_not_indirect_only")
        self.assertEqual(q_common_eligibility(nodes, both, "X", "Y")["reason"],
                         "task_has_direct_edge")

    def test_strict_yield_report_matches_new_raw_summary_and_hashes(self):
        import gzip
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        summary = json.loads((root / "step4c1_indirect_only_yield_v2_summary.json").read_text(encoding="utf-8"))
        raw_path = root / "step4c1_indirect_only_yield_v2.json.gz"
        raw = json.loads(gzip.decompress(raw_path.read_bytes()))
        report = (root / "STEP4C1_FINAL_PRODUCTION_READINESS.md").read_text(encoding="utf-8")
        self.assertEqual(summary["strict_indirect_accepted"], 595)
        self.assertEqual(summary["actual_attempts"], 2000)
        self.assertEqual(summary["changed_acceptance_rows"], 42)
        self.assertEqual(summary["strict_indirect_accepted"],
                         sum(r["accepted_q_common_strict_indirect"] for r in raw["rows"]))
        self.assertEqual(summary["raw_artifact_sha256"], hashlib.sha256(raw_path.read_bytes()).hexdigest())
        self.assertEqual(summary["settings_sha256"], raw["settings_sha256"])
        self.assertIn("595/2,000 (29.75%)", report)
        self.assertIn("386", report)
        self.assertIn("1,104", report)

    def test_production_manifest_hashes_match_artifacts(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/budget_aware_refinement/step4c1_production_manifest.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(manifest["status"], "NOT_FROZEN")
        for relative, expected in manifest["artifacts"].items():
            path = root / relative
            payload = path.read_bytes()
            if path.suffix in {".py", ".md", ".json", ".txt", ".toml", ".yml", ".yaml"}:
                payload = payload.replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(payload).hexdigest(), expected, relative)

    def test_scm_parameter_and_observation_streams_are_reproducible(self):
        proposal = {"accepted": True, "cohort": "development", "master_seed": 12,
                    "scm_id": "dev-scm-fixed-a0000", "template": "chain_mediation",
                    "node_count": 3, "attempt": 0, "nodes": ["A", "M", "Y"],
                    "topology_edges": [["A", "M"], ["M", "Y"]]}
        a, b = generate_scm_parameters(proposal), generate_scm_parameters(proposal)
        self.assertEqual(a, b)
        coeffs = list(a["truth_spec"]["coefficients"].values())
        self.assertTrue(all(.25 <= abs(x) <= .8 for x in coeffs))
        self.assertEqual(scm_signature(a["truth_spec"]), a["equation_signature_sha256"])
        data_a, data_b = generate_observations(proposal, a), generate_observations(proposal, b)
        self.assertEqual(data_a["data_sha256"], data_b["data_sha256"])
        self.assertEqual(data_a["n_rows"], 512)
        self.assertTrue(data_a["same_data_for_all_types_policies"])

    def test_analytic_gt_hand_calculation_and_do_cuts_parent_edge(self):
        truth = {"nodes": ["P", "X", "M", "Y"],
            "topological_order": ["P", "X", "M", "Y"],
            "edges": [["P", "X"], ["X", "M"], ["M", "Y"], ["X", "Y"]],
            "coefficients": {"P->X": 4.0, "X->M": 2.0,
                             "M->Y": 3.0, "X->Y": -1.0},
            "noise": {"means": {"P": 0.0, "X": 0.0, "M": 0.0, "Y": 0.0}}}
        means = analytic_intervention_means(truth, "X", 2.0)
        self.assertEqual(means["X"], 2.0)  # P->X is cut by do(X)
        self.assertEqual(means["M"], 4.0)
        self.assertEqual(means["Y"], 10.0) # 2*3*2 - 1*2
        zero = {**truth, "coefficients": {**truth["coefficients"], "X->Y": -6.0}}
        self.assertEqual(analytic_intervention_means(zero, "X", 2.0)["Y"], 0.0)
        self.assertEqual(analytic_intervention_means(truth, "X", 2.0), means)

    def test_complete_pipeline_with_explicit_fixed_equation_fixture(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from research.budget_aware_refinement.step4c1_pipeline import run_eligible_proposal
        from research.budget_aware_refinement.step4b4_mock_runner import recover_jsonl
        from research.budget_aware_refinement.step4c1_scm import _topological_order
        from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal

        proposal = build_structural_proposal(cohort="development", master_seed=101,
            proposal_id="f5", attempt=0)
        self.assertTrue(proposal["accepted"])
        nodes = proposal["nodes"]
        edges = proposal["topology_edges"]
        truth = {"nodes": nodes, "topological_order": list(_topological_order(nodes, edges)),
            "edges": edges,
            "coefficients": {f"{a}->{b}": .5 for a, b in edges},
            "noise": {"family": "fixed_fixture", "means": {node: 0.0 for node in nodes},
                      "sd": {node: 1.0 for node in nodes}}}
        noise = np.random.default_rng(723).normal(size=(512, len(nodes)))
        fixture = {"truth_spec": truth, "exogenous_noise": noise}
        with TemporaryDirectory() as td:
            ledger = Path(td) / "pipeline.jsonl"
            result = run_eligible_proposal(proposal, ledger,
                delta=1, isolate_stages=False, _fixture_payload=fixture, max_rss_bytes=None)
            composite = next(row["output"] for row in recover_jsonl(ledger)
                         if row.get("event") == "stage:composite")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(composite["status"], "OK")
        self.assertEqual(len(composite["type_differences"]), 3)
        self.assertTrue(composite["complete"])
        self.assertTrue(composite["gt_evaluation_performed"])
        self.assertTrue(np.isfinite(composite["D_i"]))
        self.assertTrue(composite["observational_data_sha256"])

    def test_actual_process_stop_and_resume_matches_uninterrupted_pipeline(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        helper = Path(__file__).with_name("step4c1_pipeline_worker.py")
        with TemporaryDirectory() as td:
            root = Path(td)
            baseline = root / "baseline.jsonl"
            completed = subprocess.run([sys.executable, str(helper), str(baseline), "-"],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            expected = next(json.loads(line)["result_sha256"] for line in reversed(
                baseline.read_text(encoding="utf-8").splitlines())
                if json.loads(line).get("event") == "terminal")
            for stage in ("scm", "policy_graphs", "recommendations", "gt_evaluation"):
                ledger = root / f"{stage}.jsonl"
                stopped = subprocess.run([sys.executable, str(helper), str(ledger), stage],
                    capture_output=True, text=True, timeout=60)
                self.assertEqual(stopped.returncode, 29, stopped.stderr)
                resumed = subprocess.run([sys.executable, str(helper), str(ledger), "-"],
                    capture_output=True, text=True, timeout=60)
                self.assertEqual(resumed.returncode, 0, resumed.stderr)
                terminal = next(json.loads(line) for line in reversed(
                    ledger.read_text(encoding="utf-8").splitlines())
                    if json.loads(line).get("event") == "terminal")
                self.assertEqual(terminal["status"], "OK")
                self.assertEqual(terminal["result_sha256"], expected)

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
