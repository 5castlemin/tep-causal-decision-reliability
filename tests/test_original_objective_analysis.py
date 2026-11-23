import unittest
import json
import tempfile
from pathlib import Path

from research.original_objective.analysis import (
    m4_secondary_delta,
    p1_delta,
    paired_bootstrap_mean,
    paired_summary,
    paired_t_summary,
    percentile_linear,
    validate_heldout_bootstrap_contract,
)
from research.original_objective.runner import _digest
from scripts.analyze_research_c_cohort import _load_analysis_bundle


class ResearchCAnalysisTests(unittest.TestCase):
    def test_primary_sign_and_missing_pair_contract(self):
        self.assertAlmostEqual(p1_delta(0.4, 0.1), 0.3)
        self.assertAlmostEqual(p1_delta(0.1, 0.4), -0.3)
        self.assertEqual(p1_delta(0.2, 0.2), 0.0)
        self.assertIsNone(p1_delta(None, 0.0))
        self.assertIsNone(p1_delta(0.0, None))

    def test_m4_secondary_sign_and_missing_pair_contract(self):
        self.assertAlmostEqual(m4_secondary_delta(0.4, 0.1), 0.3)
        self.assertAlmostEqual(m4_secondary_delta(0.1, 0.4), -0.3)
        self.assertIsNone(m4_secondary_delta(None, 0.1))

    def test_bootstrap_is_deterministic_and_resamples_pairs(self):
        values = [0.0, 0.0, 1.0, -0.5]
        first = paired_bootstrap_mean(values, seed=2026112302, replicates=10_000)
        second = paired_bootstrap_mean(values, seed=2026112302, replicates=10_000)
        self.assertEqual(first, second)
        self.assertEqual(first["resampling_unit"], "SCM")
        self.assertEqual(first["resample_size"], len(values))
        self.assertEqual(first["replicates"], 10_000)
        self.assertLessEqual(first["lower"], first["upper"])

    def test_paired_t_and_sign_summary_keep_ties(self):
        values = [0.5, 0.0, -0.5, 0.0]
        summary = paired_summary(values)
        self.assertEqual(summary["sign_counts"], {"improve": 1, "worsen": 1, "tie": 2})
        interval = paired_t_summary(values)
        self.assertEqual(interval["n_pairs"], 4)
        self.assertEqual(interval["df"], 3)
        self.assertAlmostEqual(interval["mean"], 0.0)
        self.assertLess(interval["lower"], 0)
        self.assertGreater(interval["upper"], 0)

    def test_percentile_uses_linear_interpolation(self):
        self.assertEqual(percentile_linear([0.0, 10.0], 0.25), 2.5)

    def test_approved_heldout_bootstrap_contract_is_fixed(self):
        validate_heldout_bootstrap_contract(2026112302, 10_000)
        with self.assertRaisesRegex(ValueError, "seed differs"):
            validate_heldout_bootstrap_contract(2026112303, 10_000)
        with self.assertRaisesRegex(ValueError, "replicate count differs"):
            validate_heldout_bootstrap_contract(2026112302, 9999)

    def _bundle(self):
        config = {
            "contract_status": "USER_APPROVED", "research_cohort_execution_enabled": True,
            "preregistration_status": "PREREGISTERED", "cohort_type": "development",
            "run_id": "development-test-run", "configuration_version": "research-c-execution-v1",
            "runtime_fingerprint": {"python_version": "3.11.15"}, "output_root": "C:/test/output",
            "resource_limits": {"unit_timeout_seconds": 30}, "population": {}, "scm": {}, "task": {},
            "g0": {}, "repair": {}, "evaluation": {},
            "rng_protocol": {"master_seed": 5},
        }
        manifest = {
            "approval_status": "USER_APPROVED", "manifest_version": "research-c-execution-manifest-v1",
            "config_sha256": _digest(config), "cohort_type": config["cohort_type"],
            "run_id": config["run_id"], "configuration_version": config["configuration_version"],
            "runtime_fingerprint": config["runtime_fingerprint"], "output_root": config["output_root"],
            "excluded_untracked_paths": [".build_reframed/"],
            "contract_sha256": _digest({key: config[key] for key in (
                "configuration_version", "contract_status", "preregistration_status", "population",
                "scm", "task", "g0", "repair", "evaluation")}),
            "resource_limits_sha256": _digest(config["resource_limits"]),
        }
        return config, manifest

    def test_analysis_bundle_binding_and_approval_gate(self):
        config, manifest = self._bundle()
        with tempfile.TemporaryDirectory() as folder:
            config_path, manifest_path = Path(folder) / "config.json", Path(folder) / "manifest.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            loaded_config, loaded_manifest = _load_analysis_bundle(config_path, manifest_path)
            self.assertEqual(loaded_config, config)
            self.assertEqual(loaded_manifest, manifest)
            config["contract_status"] = "PROPOSED"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "user-approved"):
                _load_analysis_bundle(config_path, manifest_path)

    def test_analysis_bundle_rejects_config_manifest_hash_mismatch(self):
        config, manifest = self._bundle()
        manifest["config_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            config_path, manifest_path = Path(folder) / "config.json", Path(folder) / "manifest.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "configuration hash"):
                _load_analysis_bundle(config_path, manifest_path)


if __name__ == "__main__":
    unittest.main()
