"""Audit stored original pilot artifacts without regenerating any response data."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from research.external_validation.semisynthetic_evaluation.pipeline import file_sha256
from research.external_validation.semisynthetic_evaluation.reproducibility import audit_existing_artifacts


def git_blob(root: Path, commit: str, name: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{name}"])


def audit(root: Path, artifact_dir: Path, output: Path) -> dict:
    root = root.resolve()
    base = root / "research/external_validation/semisynthetic_evaluation"
    lock_path = base / "development_run_lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    source_commit = "116e81d48dbeb4ee86ea164be8f1ffd908c03f62"
    recovered_pipeline = git_blob(root, source_commit,
        "research/external_validation/semisynthetic_evaluation/pipeline.py")
    recovered_pipeline_sha = hashlib.sha256(recovered_pipeline).hexdigest()
    expected_pipeline_sha = lock["code_sha256"][
        "research/external_validation/semisynthetic_evaluation/pipeline.py"]
    if recovered_pipeline_sha != expected_pipeline_sha:
        raise ValueError("recovery commit does not preserve the exact locked pipeline bytes")
    code = []
    for name, expected in lock["code_sha256"].items():
        blob = git_blob(root, source_commit, name)
        working_path = root / name
        working_sha = file_sha256(working_path)
        blob_sha = hashlib.sha256(blob).hexdigest()
        crlf_sha = hashlib.sha256(blob.replace(bytes([10]), bytes([13, 10]))).hexdigest()
        matches = []
        if working_sha == expected: matches.append("runtime_checkout_bytes"); mode = "runtime_checkout_exact"
        elif blob_sha == expected: matches.append("git_blob_bytes"); mode = "git_blob_exact"
        elif crlf_sha == expected: matches.append("git_blob_as_windows_crlf"); mode = "windows_crlf_equivalent"
        else: mode = "MISMATCH"
        if not matches: raise ValueError(f"historical code digest cannot be authenticated: {name}")
        code.append({"path": name, "git_blob_sha256": blob_sha,
            "runtime_checkout_sha256": working_sha, "locked_sha256": expected,
            "match_basis": mode})
    artifact_audit = audit_existing_artifacts(lock_path=lock_path,
        recommendation_path=artifact_dir / "recommendations.json",
        evaluation_path=artifact_dir / "evaluation.json",
        summary_path=base / "development_pilot_summary.json",
        g0_manifest_path=base / "development_g0_manifest.json",
        diagnostics_path=base / "development_policy_diagnostics.json")
    result = {"schema": "RESEARCH_D_PROVENANCE_RECOVERY_AUDIT_V1",
        "historical_gate_before_recovery": "DEVELOPMENT_PILOT_INCOMPLETE",
        "pipeline_exact_hash_recovered": True,
        "recovered_pipeline_sha256": recovered_pipeline_sha,
        "current_pipeline_sha256_after_hardening": file_sha256(base / "pipeline.py"),
        "pipeline_recovered_commit": source_commit,
        "original_run_lock_sha256": file_sha256(lock_path),
        "original_run_lock_expected_code_sha256": lock["code_sha256"],
        "source_hash_audit": code, "stored_artifact_audit": artifact_audit,
        "raw_response_rows_available": False,
        "bootstrap_intervals_independently_recomputed": False,
        "historical_gate_promoted_retroactively": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists(): raise FileExistsError(f"refusing to overwrite audit output: {output.name}")
    output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = audit(Path(__file__).resolve().parents[3], args.artifact_dir, args.output)
    print(json.dumps({"status": result["stored_artifact_audit"]["status"],
        "source_files": len(result["source_hash_audit"]),
        "recommendation_rows": result["stored_artifact_audit"]["recommendation_rows"]}, sort_keys=True))


if __name__ == "__main__":
    main()
