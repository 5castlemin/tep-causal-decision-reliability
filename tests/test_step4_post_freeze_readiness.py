from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from research.budget_aware_refinement import step4c2_freeze as freeze


class PostFreezeReadinessTests(unittest.TestCase):
    @staticmethod
    def _revision() -> tuple[str, str]:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=freeze.ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=freeze.ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        return commit, tree

    def test_exact_clean_revision_passes_production_readiness_without_generating_data(self):
        commit, tree = self._revision()

        settings, manifest, settings_sha, manifest_sha = freeze.assert_production_ready(
            expected_commit=commit, expected_tree=tree,
        )

        self.assertEqual(manifest["status"], "FROZEN")
        self.assertEqual(settings["status"], "FROZEN")
        self.assertEqual(manifest["settings_sha256"], settings_sha)
        self.assertEqual(freeze.artifact_sha256(freeze.FREEZE_MANIFEST), manifest_sha)
        self.assertEqual(settings["mode"], "research_cohort_only")
        # Readiness returns before run_cohort/proposal generation is called.

    def test_wrong_commit_is_rejected(self):
        _, tree = self._revision()
        with self.assertRaisesRegex(freeze.FreezeBindingError, "Git commit mismatch"):
            freeze.assert_production_ready(expected_commit="0" * 40, expected_tree=tree)

    def test_wrong_tree_is_rejected(self):
        commit, _ = self._revision()
        with self.assertRaisesRegex(freeze.FreezeBindingError, "Git tree mismatch"):
            freeze.assert_production_ready(expected_commit=commit, expected_tree="0" * 40)

    def test_changed_manifested_source_hash_is_rejected(self):
        manifest = json.loads(freeze.FREEZE_MANIFEST.read_text(encoding="utf-8"))
        key = "research/budget_aware_refinement/step4c1_gt.py"
        manifest["artifacts"][key] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(freeze.FreezeBindingError, "frozen artifact changed"):
                freeze.verify_freeze_manifest(manifest_path=path)

    def test_changed_operational_settings_file_is_rejected(self):
        original = json.loads(freeze.OPERATIONAL_SETTINGS.read_text(encoding="utf-8"))
        original["resources"]["unit_timeout_seconds"] = 3.0
        with tempfile.TemporaryDirectory() as directory:
            changed_path = Path(directory) / "settings.json"
            changed_path.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(freeze, "OPERATIONAL_SETTINGS", changed_path):
                with self.assertRaisesRegex(freeze.FreezeBindingError, "settings hash"):
                    freeze.verify_freeze_manifest()


if __name__ == "__main__":
    unittest.main()
