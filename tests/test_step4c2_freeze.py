from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from research.budget_aware_refinement.step4b4_mock_runner import LedgerConflict, run_pipeline
from research.budget_aware_refinement.step4c2_freeze import (
    FREEZE_MANIFEST, OPERATIONAL_SETTINGS, REQUIRED_FREEZE_ARTIFACTS,
    FreezeBindingError, artifact_sha256, load_operational_settings, verify_freeze_manifest,
)


class Step4C2FreezeBindingTests(unittest.TestCase):
    def test_settings_and_manifest_cover_active_runtime_contract(self):
        settings = json.loads(OPERATIONAL_SETTINGS.read_text(encoding="utf-8"))
        _, settings_sha = load_operational_settings(runtime=settings["runtime"])
        manifest, manifest_sha = verify_freeze_manifest()
        self.assertEqual(manifest["status"], "FROZEN")
        self.assertEqual(manifest["settings_sha256"], settings_sha)
        self.assertTrue(manifest_sha)
        self.assertTrue(REQUIRED_FREEZE_ARTIFACTS.issubset(manifest["artifacts"]))
        for path, expected in manifest["artifacts"].items():
            self.assertEqual(artifact_sha256(Path(__file__).resolve().parents[1] / path), expected, path)

    def test_wrong_commit_prevents_production_readiness(self):
        import subprocess
        from research.budget_aware_refinement.step4c2_freeze import ROOT, assert_production_ready
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT,
            check=True, capture_output=True, text=True).stdout.strip()
        with self.assertRaises(FreezeBindingError):
            assert_production_ready(expected_commit="0" * 40, expected_tree=tree)

    def test_changed_freeze_binding_blocks_ledger_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "bound.jsonl"
            first = {"protocol": "fixture", "freeze_manifest_sha256": "a" * 64,
                     "settings_sha256": "b" * 64}
            result = run_pipeline("freeze-bound-run", ledger, {"one": lambda: {"ok": True}},
                rng_key="fixture-key", config=first, input_sha256="fixture-input",
                scm_id="dev-freeze-fixture", cohort="development", isolate_stages=False)
            self.assertEqual(result["status"], "OK")
            changed = {**first, "freeze_manifest_sha256": "c" * 64}
            with self.assertRaises(LedgerConflict):
                run_pipeline("freeze-bound-run", ledger, {"one": lambda: {"ok": True}},
                    rng_key="fixture-key", config=changed, input_sha256="fixture-input",
                    scm_id="dev-freeze-fixture", cohort="development", isolate_stages=False)


if __name__ == "__main__":
    unittest.main()
