"""Version and runtime guard for the active Step 4 production contract."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Mapping

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FREEZE_MANIFEST = HERE / "step4c2_final_freeze_manifest.json"
OPERATIONAL_SETTINGS = HERE / "step4c2_operational_settings.json"
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".toml", ".yml", ".yaml"}
REQUIRED_FREEZE_ARTIFACTS = {
    "research/budget_aware_refinement/step4_topology_generator.py",
    "research/budget_aware_refinement/step4_error_injection.py",
    "research/budget_aware_refinement/step4b_task_budget.py",
    "research/budget_aware_refinement/step4b2_population.py",
    "research/budget_aware_refinement/step4_rng.py",
    "research/budget_aware_refinement/step4c1_proposal.py",
    "research/budget_aware_refinement/step4c1_indirect_only_yield_v2.json.gz",
    "research/budget_aware_refinement/step4c1_scm.py",
    "research/budget_aware_refinement/step4c1_pipeline.py",
    "research/budget_aware_refinement/step3_adapter.py",
    "research/budget_aware_refinement/graph_adapter.py",
    "research/budget_aware_refinement/step4c1_gt.py",
    "research/budget_aware_refinement/step4c1_evaluation.py",
    "research/budget_aware_refinement/step4b4_failure_rules.py",
    "research/budget_aware_refinement/step4c1_cohort.py",
    "research/budget_aware_refinement/step4b4_mock_runner.py",
    "research/budget_aware_refinement/step4c2_freeze.py",
    "research/budget_aware_refinement/run_step4c2_research_cohort.py",
    "research/budget_aware_refinement/write_step4c2_freeze_manifest.py",
    "research/budget_aware_refinement/step4c2_operational_settings.json",
    "research/budget_aware_refinement/run_step4c2_resource_qualification_v2.py",
    "research/budget_aware_refinement/run_step4c2_proposal_cost_benchmark.py",
    "research/budget_aware_refinement/step4c2_proposal_cost_benchmark_v1.json",
    "research/budget_aware_refinement/step4c2_resource_qualification_v2.json",
    "research/budget_aware_refinement/STEP4_CURRENT_ACTIVE_CONTRACT.md",
    "research/budget_aware_refinement/STEP4_PREREGISTRATION.md",
    "research/budget_aware_refinement/STEP4_SCM_GENERATION_SPEC.md",
    "research/budget_aware_refinement/STEP4_STATISTICAL_ANALYSIS_PLAN.md",
    "research/budget_aware_refinement/STEP4_FAILURE_HANDLING.md",
    "research/budget_aware_refinement/RESEARCH_PROTOCOL.md",
    "research/budget_aware_refinement/STEP4C1_COHORT_READINESS_REPORT.md",
    "research/budget_aware_refinement/STEP4C2_FINAL_FREEZE_AUDIT.md",
    "research/budget_aware_refinement/RESEARCH_STATUS.md",
    "research/budget_aware_refinement/DECISION_LOG.md",
    "research/budget_aware_refinement/EXPERIMENT_REGISTRY.md",
    "research/budget_aware_refinement/STEP4_FROZEN_PROTOCOL.md",
    "src/integrated_pilot.py",
    "src/decision_mvp.py",
    "tests/test_step4c2_freeze.py",
    "tests/test_step4c2_resource_qualification.py",
    "tests/test_step4b4_mock_runner.py",
    "tests/test_step4c1_cohort.py",
    "tests/test_step4c1_production.py",
    "docs/research_state.json",
    "requirements.txt",
}


class FreezeBindingError(RuntimeError):
    """The runtime or artifact set does not match the frozen study contract."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalized_artifact_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return raw


def artifact_sha256(path: Path) -> str:
    return sha256_bytes(normalized_artifact_bytes(path))


def current_runtime() -> dict:
    versions = {}
    for package in ("numpy", "pandas", "networkx"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {"operating_system": platform.system(),
        "platform_fingerprint": platform.platform(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(), "dependencies": versions}


def load_operational_settings(path: Path = OPERATIONAL_SETTINGS, *, runtime: dict | None = None) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    settings = json.loads(raw.decode("utf-8-sig"))
    if settings.get("status") != "FROZEN" or settings.get("schema_version") != 1:
        raise FreezeBindingError("operational settings are not a frozen supported version")
    expected = settings["runtime"]
    actual = current_runtime() if runtime is None else runtime
    for key in ("operating_system", "platform_fingerprint", "python_implementation", "python_version"):
        if actual[key] != expected[key]:
            raise FreezeBindingError(f"runtime mismatch for {key}: expected {expected[key]!r}, got {actual[key]!r}")
    if actual["dependencies"] != expected["dependencies"]:
        raise FreezeBindingError(f"dependency fingerprint mismatch: {actual['dependencies']!r}")
    return settings, artifact_sha256(Path(path))


def verify_freeze_manifest(*, require_frozen: bool = True,
                           manifest_path: Path = FREEZE_MANIFEST) -> tuple[dict, str]:
    path = Path(manifest_path)
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if require_frozen and manifest.get("status") != "FROZEN":
        raise FreezeBindingError("production cohort entry is disabled until the freeze manifest is FROZEN")
    if manifest.get("schema_version") != 1 or manifest.get("manifest_excludes_itself") is not True:
        raise FreezeBindingError("unsupported or self-referential freeze manifest")
    if manifest.get("settings_sha256") != artifact_sha256(OPERATIONAL_SETTINGS):
        raise FreezeBindingError("operational settings hash does not match the freeze manifest")
    settings = json.loads(OPERATIONAL_SETTINGS.read_text(encoding="utf-8-sig"))
    if manifest.get("active_contract") != settings.get("active_contract"):
        raise FreezeBindingError("manifest active contract differs from operational settings")
    if manifest.get("runtime_fingerprint") != settings.get("runtime"):
        raise FreezeBindingError("manifest runtime fingerprint differs from operational settings")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise FreezeBindingError("freeze manifest artifact list is empty")
    missing = REQUIRED_FREEZE_ARTIFACTS - set(artifacts)
    if missing:
        raise FreezeBindingError(f"freeze manifest omits required artifacts: {sorted(missing)}")
    for relpath, expected in artifacts.items():
        candidate = (ROOT / relpath).resolve()
        if not candidate.is_relative_to(ROOT.resolve()) or not candidate.is_file():
            raise FreezeBindingError(f"manifest artifact is missing or outside repository: {relpath}")
        if artifact_sha256(candidate) != expected:
            raise FreezeBindingError(f"frozen artifact changed: {relpath}")
    return manifest, artifact_sha256(path)


def assert_production_ready(*, expected_commit: str,
                            expected_tree: str) -> tuple[dict, dict, str, str]:
    """Validate runtime and all frozen content before any proposal is generated."""
    settings, settings_sha = load_operational_settings()
    manifest, manifest_sha = verify_freeze_manifest(require_frozen=True)
    if manifest.get("settings_sha256") != settings_sha:
        raise FreezeBindingError("freeze manifest and loaded settings disagree")
    if not expected_commit or not expected_tree:
        raise FreezeBindingError("production entry requires explicit expected Git commit and tree")
    actual_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    if actual_commit != expected_commit:
        raise FreezeBindingError(f"Git commit mismatch: expected {expected_commit}, got {actual_commit}")
    actual_tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    if actual_tree != expected_tree:
        raise FreezeBindingError(f"Git tree mismatch: expected {expected_tree}, got {actual_tree}")
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise FreezeBindingError("production cohort entry requires a clean worktree")
    return settings, manifest, settings_sha, manifest_sha


def build_manifest(artifact_paths: list[str]) -> dict:
    """Build a content manifest; Git commit/tree are recorded out of band."""
    settings, settings_sha = load_operational_settings()
    missing = REQUIRED_FREEZE_ARTIFACTS - set(artifact_paths)
    if missing:
        raise ValueError(f"freeze artifact list omits required paths: {sorted(missing)}")
    artifacts = {}
    for relpath in sorted(set(artifact_paths)):
        candidate = (ROOT / relpath).resolve()
        if not candidate.is_relative_to(ROOT.resolve()) or not candidate.is_file():
            raise ValueError(f"invalid freeze artifact path: {relpath}")
        artifacts[relpath] = artifact_sha256(candidate)
    return {"schema_version": 1, "status": "FROZEN", "protocol": "STEP4_CURRENT_ACTIVE_CONTRACT",
        "manifest_excludes_itself": True,
        "hash_normalization": "UTF-8 text suffixes normalized CRLF/CR to LF; all other artifacts hashed byte-for-byte",
        "settings_sha256": settings_sha, "runtime_fingerprint": settings["runtime"],
        "active_contract": settings["active_contract"], "artifacts": artifacts,
        "git_revision_binding": {"recorded_externally": True,
            "note": "The exact commit and tree are recorded in the PR/CI Self-Review after commit; the manifest excludes Git identity to avoid self-reference."}}
