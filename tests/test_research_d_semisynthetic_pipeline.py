"""No-R tests for Research D's locked evaluator boundary and schema guards."""
from __future__ import annotations

import json
import tempfile
import unittest
import hashlib
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from research.external_validation.semisynthetic_evaluation.pipeline import (
    POLICY_IDS, _validate_frame, canonical_json, evaluate_locked, sha256_bytes,
    lock_recommendations, make_g0, reconstruct_g0, validate_recommendation_lock,
)


class SemisyntheticPipelineBoundaryTests(unittest.TestCase):
    class _Mechanism:
        def produce_sample(self, newdata, random_state):
            return newdata.iloc[:, 0].to_numpy(dtype=float) + random_state.normal(0, 0.01, len(newdata))

    class _Model:
        def __init__(self):
            self.nodes = ["Station1_mp_0", "Station1_mp_4"]
            self.graph = nx.DiGraph([("Station1_mp_0", "Station1_mp_4")])
            self.drf = {"Station1_mp_0": object(), "Station1_mp_4": SemisyntheticPipelineBoundaryTests._Mechanism()}

        def parents(self, of_node):
            return list(self.graph.predecessors(of_node))

    @staticmethod
    def _locked_manifest(path, contract):
        rows = []
        for budget in range(5):
            for policy in POLICY_IDS:
                rows.append({"g0_seed_id": 8, "budget": budget, "policy_id": policy,
                             "recommended_action": 0.5, "repair_cost": 0,
                             "repaired_graph_sha256": "a" * 64})
        body = {"locked": True, "contract_sha256": sha256_bytes(contract.read_bytes()),
            "actions": [0.5], "g0_seed_ids": [8], "recommendations": rows,
            "target_training_only": 0.5, "scale_training_only": 1.0,
            "training_rows": 512, "training_sha256": "b" * 64,
            "task": {"action": "Station1_mp_0", "target": "Station1_mp_4"},
            "graph_free_baseline": {"action": 0.5}}
        body["content_sha256"] = sha256_bytes(canonical_json(body))
        path.write_text(json.dumps(body), encoding="utf-8")

    def test_evaluator_lock_requires_preexisting_locked_recommendations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text(json.dumps({"mode": "development_reproduction_only",
                "action_grid": {"values": [0.5]},
                "evaluation": {"seed_root": 314159, "rows_per_action": 2,
                    "bootstrap_replicates": 20, "bootstrap_seed": 314160},
                "task": {"action": "Station1_mp_0", "target": "Station1_mp_4"},
                "g0": {"seed_ids": [8], "budgets": [0, 1, 2, 3, 4]},
                "target_scale": {"target": 0.5, "scale": 1.0},
                "training": {"n": 512, "sha256": "b" * 64}}), encoding="utf-8")
            missing = root / "missing.json"
            with self.assertRaises(ValueError):
                validate_recommendation_lock(missing, sha256_bytes(contract.read_bytes()))
            unlocked = root / "unlocked.json"
            body = {"locked": False, "contract_sha256": sha256_bytes(contract.read_bytes())}
            body["content_sha256"] = sha256_bytes(canonical_json(body))
            unlocked.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_recommendation_lock(unlocked, sha256_bytes(contract.read_bytes()))

    def test_evaluator_lock_detects_tampering_and_contract_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text('{"contract":"locked"}', encoding="utf-8")
            body = {"locked": True, "contract_sha256": sha256_bytes(contract.read_bytes()), "recommendations": []}
            body["content_sha256"] = sha256_bytes(canonical_json(body))
            lock = root / "recommendations.json"
            lock.write_text(json.dumps(body), encoding="utf-8")
            validated, digest = validate_recommendation_lock(lock, sha256_bytes(contract.read_bytes()))
            self.assertEqual(digest, body["content_sha256"])
            self.assertTrue(validated["locked"])
            changed = dict(body)
            changed["recommendations"] = [{"action": 123}]
            lock.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_recommendation_lock(lock, sha256_bytes(contract.read_bytes()))
            lock.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_recommendation_lock(lock, "0" * 64)

    def test_evaluator_frame_gate_checks_exact_shape_schema_and_finite_values(self):
        frame = pd.DataFrame({"X": [0.25, 0.25], "Y": [1.0, 2.0]})
        array = _validate_frame(frame, ["X", "Y"], 2)
        self.assertEqual(array.shape, (2, 2))
        with self.assertRaises(ValueError):
            _validate_frame(frame, ["Y", "X"], 2)
        with self.assertRaises(ValueError):
            _validate_frame(frame.iloc[:1], ["X", "Y"], 2)
        bad = frame.copy()
        bad.loc[0, "Y"] = np.inf
        with self.assertRaises(ValueError):
            _validate_frame(bad, ["X", "Y"], 2)

    def test_evaluator_e2e_requires_locked_complete_manifest_and_emits_aggregates_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text(json.dumps({"mode": "development_reproduction_only",
                "action_grid": {"values": [0.5]},
                "evaluation": {"seed_root": 314159, "rows_per_action": 2,
                    "bootstrap_replicates": 20, "bootstrap_seed": 314160},
                "task": {"action": "Station1_mp_0", "target": "Station1_mp_4"},
                "g0": {"seed_ids": [8], "budgets": [0, 1, 2, 3, 4]},
                "target_scale": {"target": 0.5, "scale": 1.0},
                "training": {"n": 512, "sha256": "b" * 64}}), encoding="utf-8")
            lock = root / "recommendations.json"
            output = root / "evaluation.json"
            self._locked_manifest(lock, contract)
            result = evaluate_locked(model=self._Model(), lock_path=lock, contract_path=contract,
                output_path=output, evaluation_seed_root=314159, rows_per_action=2,
                bootstrap_replicates=20, bootstrap_seed=314160)
            self.assertEqual(result["total_intervention_rows"], 2)
            self.assertTrue(result["raw_response_rows_saved"] is False)
            self.assertFalse(result["policy_recommendation_changed_after_lock"])
            self.assertEqual(len(result["evaluation_rows"]), 85)
            self.assertEqual(len(result["primary_two_source_uncertainty"]["two_source_percentile_95"]), 2)

    def test_evaluator_refuses_recommendation_actions_outside_common_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text('{"contract":"locked"}', encoding="utf-8")
            lock = root / "recommendations.json"
            self._locked_manifest(lock, contract)
            body = json.loads(lock.read_text(encoding="utf-8"))
            body["recommendations"][0]["recommended_action"] = 0.75
            body.pop("content_sha256")
            body["content_sha256"] = sha256_bytes(canonical_json(body))
            lock.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate_locked(model=self._Model(), lock_path=lock, contract_path=contract,
                    output_path=root / "evaluation.json", evaluation_seed_root=314159, rows_per_action=2)

    def test_evaluator_rejects_duplicate_g0_ids_even_with_recomputed_content_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text('{"contract":"locked"}', encoding="utf-8")
            lock = root / "recommendations.json"
            self._locked_manifest(lock, contract)
            body = json.loads(lock.read_text(encoding="utf-8"))
            body["g0_seed_ids"] = [8, 8]
            body.pop("content_sha256")
            body["content_sha256"] = sha256_bytes(canonical_json(body))
            lock.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate_locked(model=self._Model(), lock_path=lock, contract_path=contract,
                    output_path=root / "evaluation.json", evaluation_seed_root=314159, rows_per_action=2)

    def test_evaluator_refuses_existing_output_and_pilot_cap_overrun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text('{"contract":"locked"}', encoding="utf-8")
            lock = root / "recommendations.json"
            self._locked_manifest(lock, contract)
            existing = root / "existing.json"
            existing.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                evaluate_locked(model=self._Model(), lock_path=lock, contract_path=contract,
                    output_path=existing, evaluation_seed_root=314159, rows_per_action=2)
            with self.assertRaises(ValueError):
                evaluate_locked(model=self._Model(), lock_path=lock, contract_path=contract,
                    output_path=root / "over-cap.json", evaluation_seed_root=314159, rows_per_action=257)

    def test_research_c_policy_catalog_connects_to_existing_ridge_recommender(self):
        nodes = [f"Station1_mp_{i}" for i in range(6)]
        edge_list = [(nodes[0], nodes[1]), (nodes[0], nodes[2]), (nodes[1], nodes[2]),
                     (nodes[1], nodes[4]), (nodes[3], nodes[4]), (nodes[3], nodes[5]),
                     (nodes[4], nodes[5])]
        from research.original_objective import policy_engine as pe
        truth = {pe.pair(a, b): (a, b) for a, b in edge_list}
        record = make_g0(truth, nodes, 702019)
        g0 = reconstruct_g0(record, truth)
        rng = np.random.default_rng(7841)
        frame = pd.DataFrame(rng.normal(size=(96, len(nodes))), columns=nodes)
        actions = [-1.0, -0.5, 0.0, 0.5, 1.0]
        contract = (Path(__file__).parents[1] / "research" / "external_validation" /
                    "semisynthetic_evaluation" / "development_contract.json")
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "recommendations.json"
            manifest, digest = lock_recommendations(frame, hashlib.sha256(b"train").hexdigest(),
                truth, nodes, actions, [{"seed_id": 702019, "record": record, "g0": g0}], lock,
                contract_path=contract)
            self.assertEqual(len(manifest["recommendations"]), 85)
            self.assertEqual(manifest["policies_per_graph_budget"], 17)
            self.assertEqual(manifest["content_sha256"], digest)
            self.assertTrue(all(row["recommended_action"] in actions for row in manifest["recommendations"]))


if __name__ == "__main__":
    unittest.main()
