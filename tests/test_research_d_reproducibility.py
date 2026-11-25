"""Fail-closed tests for Research D source and evaluator lock verification."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from research.external_validation.semisynthetic_evaluation.reproducibility import (
    locked_invocation, validate_code_hashes, validate_locked_invocation, verify_file_digest,
    validate_reproduction_science, validate_original_artifact_audit,
    serialize_training_frame, read_training_frame, validate_csv_float_round_trip,
)


class ResearchDReproducibilityTests(unittest.TestCase):
    def _contract(self):
        return {"run_id": "rd-development-reproduction-20261125-01",
            "fit_seed": 91420261,
            "fit_reproducibility": {"check_seed": 123, "same_seed_refit_sample_sha256": "a" * 64},
            "evaluation": {"seed_root": 456, "rows_per_action": 256,
                "bootstrap_replicates": 2000, "bootstrap_seed": 789},
            "action_grid": {"values": [0.1, 0.2, 0.3]},
            "target_scale": {"target": 1.25, "scale": 0.75},
            "g0": {"seed_ids": [11, 12], "budgets": [0, 1, 2, 3, 4]},
            "policy_ids": ["S0", "M1", "M1+M2"]}

    def test_locked_cli_captures_every_recommendation_and_evaluation_setting(self):
        expected = locked_invocation(self._contract())
        self.assertEqual(expected["mode"], "development_reproduction_only")
        self.assertEqual(expected["fit_seed"], 91420261)
        self.assertEqual(expected["fit_check_sha256"], "a" * 64)
        self.assertEqual(expected["evaluation_seed_root"], 456)
        self.assertEqual(expected["rows_per_action"], 256)
        self.assertEqual(expected["actions"], [0.1, 0.2, 0.3])
        self.assertEqual(expected["g0_seed_ids"], [11, 12])
        self.assertEqual(expected["policy_ids"], ["S0", "M1", "M1+M2"])
        self.assertEqual(expected["bootstrap_seed"], 789)

    def test_any_locked_cli_mutation_is_detectable(self):
        base = locked_invocation(self._contract())
        mutations = {
            "mode": "final", "run_id": "other", "fit_seed": 9,
            "fit_check_seed": 9, "fit_check_sha256": "b" * 64,
            "evaluation_seed_root": 9, "rows_per_action": 255,
            "actions": [0.1, 0.2], "target": 0.0, "scale": 1.0,
            "g0_seed_ids": [12, 11], "budgets": [0, 2],
            "policy_ids": ["S0"], "bootstrap_replicates": 5,
            "bootstrap_seed": 1,
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                changed = copy.deepcopy(base)
                changed[key] = value
                with self.assertRaisesRegex(ValueError, key):
                    validate_locked_invocation(self._contract(), changed)

    def test_one_byte_code_change_fails_source_digest_binding(self):
        expected = {"pipeline.py": "1" * 64, "worker.py": "2" * 64}
        with self.assertRaisesRegex(ValueError, "pipeline.py"):
            validate_code_hashes(expected, {**expected, "pipeline.py": "3" * 64})
        with self.assertRaisesRegex(ValueError, "worker.py"):
            validate_code_hashes(expected, {"pipeline.py": expected["pipeline.py"]})

    def test_raw_file_digest_does_not_accept_self_rehashed_replacement(self):
        original = b"locked recommendation manifest"
        replacement = b"mutated recommendation manifest"
        expected = hashlib.sha256(original).hexdigest()
        self.assertNotEqual(hashlib.sha256(replacement).hexdigest(), expected)
        # Verifying against the independently recorded expected digest fails even
        # if the replacement file has a newly computed internal content digest.
        with self.assertRaisesRegex(ValueError, "recommendation raw-byte"):
            from pathlib import Path
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "recommendations.json"
                path.write_bytes(replacement)
                verify_file_digest(path, expected, "recommendation raw-byte")

    def test_reproduction_contract_rejects_scientific_condition_change(self):
        old = {"source": {"data_sha256": {"x": "a" * 64}}, "graph_sha256": "b" * 64,
            "node_order": ["X", "M", "Y"],
            "task": {"action": "X", "target": "Y", "reference_path": ["X", "M", "Y"],
                "strict_indirect_only": True, "interpretation": "virtual benchmark intervention; not physical controllability"},
            "action_grid": {"quantiles": [0.1, 0.3, 0.5], "values": [0.1, 0.2, 0.3],
                "support_checks": [], "joint_support_claim": False},
            "training": {"n": 2, "seed": 3, "sha256": "c" * 64, "all_policies_share": True},
            "target_scale": {"target": 1.0, "scale": 0.5, "delta_sd": 1, "rule": "fixed"},
            "g0": {"seed_ids": [1], "q": 0.15, "r": 0.05, "dag_invalid": "record and reject without redraw",
                "policy_count_per_graph_budget": 17, "budgets": [0, 1, 2, 3, 4]},
            "evaluation": {"rows_per_action": 256, "action_count": 3, "total_intervention_rows": 768,
                "seed_root": 45, "loss_estimator": "bias-corrected squared mean; no truncation"}}
        new = copy.deepcopy(old)
        new["evaluation"].update({"bootstrap_replicates": 2000, "bootstrap_seed": 91420263})
        new["policy_ids"] = ["S0", "M1", "M2", "M3", "M4", "M1+M2", "M1+M3", "M1+M4",
            "M2+M3", "M2+M4", "M3+M4", "M1+M2+M3", "M1+M2+M4", "M1+M3+M4",
            "M2+M3+M4", "M1+M2+M3+M4", "CANONICAL_ORACLE"]
        validate_reproduction_science(new, old)
        new["target_scale"]["target"] += 0.1
        with self.assertRaisesRegex(ValueError, "target/scale"):
            validate_reproduction_science(new, old)

    def test_historical_audit_status_is_read_from_saved_artifact_audit_record(self):
        audit = {"pipeline_exact_hash_recovered": True,
            "historical_gate_promoted_retroactively": False,
            "stored_artifact_audit": {"status":
                "PASS_SAVED_ARTIFACTS_AUDITED_RAW_RESPONSE_ROWS_NOT_AVAILABLE"}}
        validate_original_artifact_audit(audit)
        audit["stored_artifact_audit"]["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "audit"):
            validate_original_artifact_audit(audit)

    def test_action_grid_and_edge_case_doubles_round_trip_exactly(self):
        actions = [0.000155911358968, 0.0001724093665238, 0.00018679686613765,
                   0.00020263502221978, 0.00022589388613683002]
        result = validate_csv_float_round_trip(actions +
            [0.1, 1e-200, float(np.nextafter(0.5, 1.0)), 1.2345678901234567])
        self.assertTrue(result["exact_bytes_match"])
        self.assertEqual(result["input_numeric_sha256"], result["roundtrip_numeric_sha256"])

    def test_training_csv_loader_preserves_numeric_digest_order_shape_and_values(self):
        frame = pd.DataFrame({"X": [0.000155911358968, 1e-200, 1.2345678901234567],
                              "Y": [0.1, float(np.nextafter(0.5, 1.0)), -3.141592653589793]})
        expected = hashlib.sha256(frame.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "training.csv"
            path.write_bytes(serialize_training_frame(frame))
            loaded = read_training_frame(path, node_order=["X", "Y"], rows=3,
                                         expected_numeric_sha256=expected)
            self.assertEqual(list(loaded.columns), ["X", "Y"])
            self.assertEqual(loaded.shape, (3, 2))
            self.assertEqual(frame.to_numpy(dtype=float).tobytes(order="C"),
                             loaded.to_numpy(dtype=float).tobytes(order="C"))
            with self.assertRaisesRegex(ValueError, "schema/shape"):
                read_training_frame(path, node_order=["Y", "X"], rows=3,
                                    expected_numeric_sha256=expected)


if __name__ == "__main__":
    unittest.main()
