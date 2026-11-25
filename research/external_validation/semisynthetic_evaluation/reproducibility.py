"""Fail-closed byte, repository, environment and artifact checks for Research D."""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import platform
import subprocess
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from .pipeline import canonical_json, file_sha256, verify_sources


def git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def repository_identity(root: Path, *, require_clean: bool = True) -> dict:
    root = root.resolve()
    status = git_value(root, "status", "--porcelain", "--untracked-files=all")
    if require_clean and status:
        raise ValueError("Research D execution requires a clean repository worktree")
    return {"commit": git_value(root, "rev-parse", "HEAD"),
            "tree": git_value(root, "rev-parse", "HEAD^{tree}"),
            "worktree_clean": not bool(status), "status_sha256": hashlib.sha256(status.encode()).hexdigest()}


def require_external_outputs(root: Path, paths: list[Path]) -> None:
    root = root.resolve()
    for path in paths:
        resolved = path.resolve()
        if resolved == root or root in resolved.parents:
            raise ValueError(f"generated Research D data/artifact must remain outside the repository: {path.name}")


def research_code_hashes(root: Path, names: list[str]) -> dict[str, str]:
    root = root.resolve()
    result = {}
    for name in names:
        path = (root / name).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(f"missing or escaped locked research code path: {name}")
        result[name] = file_sha256(path)
    return result


def verify_file_digest(path: Path, expected: str, label: str) -> str:
    actual = file_sha256(path)
    if actual != expected:
        raise ValueError(f"{label} raw-byte SHA-256 mismatch")
    return actual


def validate_original_artifact_audit(audit: dict) -> None:
    stored = audit.get("stored_artifact_audit", {})
    if (stored.get("status") != "PASS_SAVED_ARTIFACTS_AUDITED_RAW_RESPONSE_ROWS_NOT_AVAILABLE"
            or not audit.get("pipeline_exact_hash_recovered")
            or audit.get("historical_gate_promoted_retroactively") is not False):
        raise ValueError("historical source/artifact audit is incomplete or inconsistent")


def serialize_training_frame(frame: pd.DataFrame) -> bytes:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("training frame must be a nonempty DataFrame")
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("training frame contains nonfinite values")
    return frame.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8")


def read_training_frame(path: Path, *, node_order: list[str], rows: int,
                        expected_numeric_sha256: str) -> pd.DataFrame:
    frame = pd.read_csv(path, float_precision="round_trip")
    if list(frame.columns) != list(node_order) or frame.shape != (rows, len(node_order)):
        raise ValueError("round-trip training CSV schema/shape mismatch")
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("round-trip training CSV contains nonfinite values")
    actual = hashlib.sha256(values.tobytes(order="C")).hexdigest()
    if actual != expected_numeric_sha256:
        raise ValueError("round-trip training CSV numeric digest mismatch")
    return frame


def validate_csv_float_round_trip(values: list[float]) -> dict:
    frame = pd.DataFrame({"value": np.asarray(values, dtype=np.float64)})
    raw = serialize_training_frame(frame)
    decoded = pd.read_csv(io.BytesIO(raw), float_precision="round_trip")
    if decoded.shape != frame.shape or list(decoded.columns) != list(frame.columns):
        raise ValueError("CSV float round-trip changed shape or column order")
    before = frame.to_numpy(dtype=np.float64).tobytes(order="C")
    after = decoded.to_numpy(dtype=np.float64).tobytes(order="C")
    if before != after:
        raise ValueError("CSV float round-trip changed IEEE-754 values")
    return {"rows": len(frame), "input_numeric_sha256": hashlib.sha256(before).hexdigest(),
            "roundtrip_numeric_sha256": hashlib.sha256(after).hexdigest(),
            "exact_bytes_match": True, "parser": "pandas.read_csv(float_precision='round_trip')"}


def validate_code_hashes(expected: dict[str, str], actual: dict[str, str]) -> None:
    if actual != expected:
        changed = sorted(set(actual) | set(expected))
        changed = [name for name in changed if actual.get(name) != expected.get(name)]
        raise ValueError("research source byte hash differs: " + ", ".join(changed))


def validate_reproduction_science(new: dict, original: dict) -> None:
    checks = {
        "source data": (new.get("source"), original.get("source")),
        "graph": (new.get("graph_sha256"), original.get("graph_sha256")),
        "node order": (new.get("node_order"), original.get("node_order")),
        "task": (new.get("task"), original.get("task")),
        "actions": (new.get("action_grid"), original.get("action_grid")),
        "training": (new.get("training"), original.get("training")),
        "target/scale": (new.get("target_scale"), original.get("target_scale")),
        "G0 seed/error/budget": ({k: new["g0"].get(k) for k in
            ("seed_ids", "q", "r", "dag_invalid", "policy_count_per_graph_budget", "budgets")},
            {k: original["g0"].get(k) for k in
            ("seed_ids", "q", "r", "dag_invalid", "policy_count_per_graph_budget", "budgets")}),
        "policy set": (new.get("policy_ids"), original.get("policy_ids", list(__import__(
            "research.external_validation.semisynthetic_evaluation.pipeline", fromlist=["POLICY_IDS"]).POLICY_IDS))),
        "evaluation contract": ({k: new["evaluation"].get(k) for k in
            ("rows_per_action", "action_count", "total_intervention_rows", "seed_root", "loss_estimator",
             "bootstrap_replicates", "bootstrap_seed")},
            {k: original["evaluation"].get(k) for k in
            ("rows_per_action", "action_count", "total_intervention_rows", "seed_root", "loss_estimator")}
            | {"bootstrap_replicates": 2000, "bootstrap_seed": 91420263}),
    }
    differences = [name for name, (actual, expected) in checks.items() if actual != expected]
    if differences:
        raise ValueError("Development reproduction changes scientific conditions: " + ", ".join(differences))


def external_source_manifest(source_root: Path) -> dict:
    source_root = source_root.resolve()
    commit = git_value(source_root, "rev-parse", "HEAD")
    if commit != "8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9":
        raise ValueError("causalAssembly source commit differs from pinned commit")
    status = git_value(source_root, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise ValueError("causalAssembly pinned source worktree is dirty")
    files = git_value(source_root, "ls-files", "causalAssembly").splitlines()
    source_files = [name for name in files if name.endswith(".py")]
    return {"commit": commit, "worktree_clean": True,
            "python_source_sha256": {name: file_sha256(source_root / name) for name in source_files}}


def runtime_fingerprint() -> dict:
    from rpy2.robjects import r
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "numpy": np.__version__, "pandas": pd.__version__, "networkx": nx.__version__,
            "R": str(r("as.character(getRversion())")[0]),
            "R_drf": str(r('as.character(packageVersion("drf"))')[0]),
            "rpy2": importlib.metadata.version("rpy2"), "causalAssembly": "1.2.1"}


def locked_invocation(contract: dict) -> dict:
    return {"mode": "development_reproduction_only", "run_id": contract["run_id"],
        "fit_seed": contract["fit_seed"],
        "fit_check_seed": contract["fit_reproducibility"]["check_seed"],
        "fit_check_sha256": contract["fit_reproducibility"]["same_seed_refit_sample_sha256"],
        "evaluation_seed_root": contract["evaluation"]["seed_root"],
        "rows_per_action": contract["evaluation"]["rows_per_action"],
        "actions": contract["action_grid"]["values"],
        "target": contract["target_scale"]["target"], "scale": contract["target_scale"]["scale"],
        "g0_seed_ids": contract["g0"]["seed_ids"], "budgets": contract["g0"]["budgets"],
        "policy_ids": contract["policy_ids"],
        "bootstrap_replicates": contract["evaluation"]["bootstrap_replicates"],
        "bootstrap_seed": contract["evaluation"]["bootstrap_seed"]}


def validate_locked_invocation(contract: dict, invocation: dict) -> None:
    expected = locked_invocation(contract)
    if invocation != expected:
        changed = sorted(set(expected) | set(invocation))
        changed = [key for key in changed if expected.get(key) != invocation.get(key)]
        raise ValueError("evaluator invocation differs from run lock: " + ", ".join(changed))


def build_execution_manifest(*, root: Path, source_root: Path, data_root: Path,
                             contract_path: Path, recommendation_path: Path,
                             code_names: list[str], run_id: str, invocation: dict,
                             support_artifacts: dict[str, Path] | None = None) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
    recorded = recommendation.get("content_sha256")
    body = dict(recommendation)
    body.pop("content_sha256", None)
    canonical_hash = hashlib.sha256(canonical_json(body)).hexdigest()
    if recorded != canonical_hash:
        raise ValueError("recommendation canonical content hash is invalid")
    repo = repository_identity(root)
    source_data = verify_sources(source_root, data_root)
    validate_locked_invocation(contract, invocation)
    support_hashes = {key: file_sha256(path)
        for key, path in sorted((support_artifacts or {}).items())}
    if (support_hashes.get("training_frame_csv") != contract.get("training_frame_csv_sha256")
            or support_hashes.get("recommendation_input") != contract.get("recommendation_input_sha256")):
        raise ValueError("pre-evaluator training/recommendation artifacts differ from scientific run lock")
    return {"schema": "RESEARCH_D_REPRODUCTION_EXECUTION_MANIFEST_V1",
            "mode": "development_reproduction_only", "run_id": run_id,
            "repository": repo, "code_sha256": research_code_hashes(root, code_names),
            "source": source_data, "external_source": external_source_manifest(source_root),
            "runtime": runtime_fingerprint(),
            "contract_sha256": file_sha256(contract_path),
            "recommendation_raw_sha256": file_sha256(recommendation_path),
            "recommendation_content_sha256": canonical_hash,
            "recommendation_row_count": recommendation.get("row_count"),
            "training_sha256": contract["training"]["sha256"],
            "support_artifact_sha256": support_hashes,
            "invocation": invocation}


def verify_execution_manifest(*, root: Path, source_root: Path, data_root: Path,
                              contract_path: Path, recommendation_path: Path,
                              execution_manifest_path: Path, expected_manifest_sha256: str,
                              code_names: list[str], invocation: dict,
                              output_path: Path | None = None,
                              support_artifacts: dict[str, Path] | None = None) -> tuple[dict, dict]:
    manifest_raw = execution_manifest_path.read_bytes()
    actual_manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    if actual_manifest_sha != expected_manifest_sha256:
        raise ValueError("execution manifest SHA-256 mismatch")
    manifest = json.loads(manifest_raw)
    if manifest.get("schema") != "RESEARCH_D_REPRODUCTION_EXECUTION_MANIFEST_V1" \
            or manifest.get("mode") != "development_reproduction_only":
        raise ValueError("unsupported or unapproved execution mode")
    if manifest.get("invocation") != invocation:
        raise ValueError("evaluator CLI arguments differ from the locked invocation")
    current_support = {key: file_sha256(path)
        for key, path in sorted((support_artifacts or {}).items())}
    if support_artifacts is not None and current_support != manifest.get("support_artifact_sha256"):
        raise ValueError("learner/recommendation support artifacts changed")
    if output_path is not None and output_path.exists():
        raise FileExistsError("refusing to overwrite existing evaluation output")
    repo = repository_identity(root)
    if repo != manifest.get("repository"):
        raise ValueError("repository commit/tree/worktree identity changed")
    code = research_code_hashes(root, code_names)
    validate_code_hashes(manifest.get("code_sha256", {}), code)
    validate_code_hashes(json.loads(contract_path.read_text(encoding="utf-8")).get("code_sha256", {}), code)
    source = verify_sources(source_root, data_root)
    if source != manifest.get("source") or external_source_manifest(source_root) != manifest.get("external_source"):
        raise ValueError("pinned external source/data changed")
    if runtime_fingerprint() != manifest.get("runtime"):
        raise ValueError("runtime fingerprint differs from execution manifest")
    contract_sha = file_sha256(contract_path)
    if contract_sha != manifest.get("contract_sha256"):
        raise ValueError("scientific run lock changed")
    recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
    if file_sha256(recommendation_path) != manifest.get("recommendation_raw_sha256"):
        raise ValueError("recommendation raw-byte digest differs from execution manifest")
    body = dict(recommendation)
    recorded = body.pop("content_sha256", None)
    canonical_hash = hashlib.sha256(canonical_json(body)).hexdigest()
    if recorded != canonical_hash or canonical_hash != manifest.get("recommendation_content_sha256"):
        raise ValueError("recommendation manifest integrity check failed")
    if recommendation.get("contract_sha256") != contract_sha:
        raise ValueError("recommendation manifest references another run lock")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    validate_locked_invocation(contract, invocation)
    if recommendation.get("training_sha256") != contract["training"]["sha256"] \
            or recommendation.get("training_rows") != contract["training"]["n"]:
        raise ValueError("recommendation training source differs from run lock")
    if recommendation.get("actions") != contract["action_grid"]["values"] \
            or recommendation.get("g0_seed_ids") != contract["g0"]["seed_ids"]:
        raise ValueError("recommendation action or G0 support differs from run lock")
    if manifest.get("recommendation_row_count") != len(recommendation.get("recommendations", [])):
        raise ValueError("recommendation row count differs from execution manifest")
    return manifest, recommendation


def audit_existing_artifacts(*, lock_path: Path, recommendation_path: Path,
                             evaluation_path: Path, summary_path: Path,
                             g0_manifest_path: Path, diagnostics_path: Path) -> dict:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    rec = json.loads(recommendation_path.read_text(encoding="utf-8"))
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    g0 = json.loads(g0_manifest_path.read_text(encoding="utf-8"))
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    rec_body = dict(rec); rec_content = rec_body.pop("content_sha256", None)
    rec_actual_content = hashlib.sha256(canonical_json(rec_body)).hexdigest()
    if rec_content != rec_actual_content or len(rec["recommendations"]) != 2720:
        raise ValueError("original recommendation manifest hash/count failed")
    lock_raw_sha = file_sha256(lock_path)
    if (rec.get("contract_sha256") != lock_raw_sha
            or rec.get("training_sha256") != lock["training"]["sha256"]
            or rec.get("training_rows") != lock["training"]["n"]
            or rec.get("actions") != lock["action_grid"]["values"]
            or rec.get("g0_seed_ids") != lock["g0"]["seed_ids"]
            or rec.get("target_training_only") != lock["target_scale"]["target"]
            or rec.get("scale_training_only") != lock["target_scale"]["scale"]):
        raise ValueError("original recommendation manifest differs from scientific lock")
    expected = {(seed, budget, policy) for seed in lock["g0"]["seed_ids"]
                for budget in lock["g0"]["budgets"]
                for policy in ("S0", "M1", "M2", "M3", "M4", "M1+M2", "M1+M3", "M1+M4",
                    "M2+M3", "M2+M4", "M3+M4", "M1+M2+M3", "M1+M2+M4", "M1+M3+M4",
                    "M2+M3+M4", "M1+M2+M3+M4", "CANONICAL_ORACLE")}
    keys = {(r["g0_seed_id"], r["budget"], r["policy_id"]) for r in rec["recommendations"]}
    if keys != expected or len(keys) != 2720:
        raise ValueError("original recommendation grid is incomplete or duplicated")
    if (evaluation.get("recommendation_lock_sha256") != rec_content
            or evaluation.get("contract_sha256") != lock_raw_sha
            or len(evaluation.get("evaluation_rows", [])) != 2720):
        raise ValueError("original evaluation artifact is not bound to the recommendations")
    if evaluation.get("total_intervention_rows") != 1280 or evaluation.get("rows_per_action") != 256:
        raise ValueError("original evaluation support/count differs from contract")
    g0_body = dict(g0); g0_recorded = g0_body.pop("content_sha256", None)
    if g0_recorded != hashlib.sha256(canonical_json(g0_body)).hexdigest():
        raise ValueError("G0 manifest canonical content hash is invalid")
    g0_ids = [row["seed_id"] for row in g0.get("g0", [])]
    if g0_ids != lock["g0"]["seed_ids"] or g0.get("g0_count") != 32:
        raise ValueError("G0 manifest seed IDs differ from original run lock")
    g0_hashes = {row["seed_id"]: row["initial_graph_sha256"] for row in g0["g0"]}
    if (g0.get("run_lock_sha256") != lock_raw_sha
            or g0.get("recommendation_lock_sha256") != rec_content):
        raise ValueError("G0 manifest binding does not match the original run")
    if any(row["initial_graph_sha256"] != g0_hashes[row["g0_seed_id"]]
           for row in rec["recommendations"]):
        raise ValueError("recommendation initial graph hashes differ from G0 manifest")
    diag_body = dict(diagnostics); diag_recorded = diag_body.pop("content_sha256", None)
    if diag_recorded != hashlib.sha256(canonical_json(diag_body)).hexdigest():
        raise ValueError("policy diagnostics canonical hash is invalid")
    if (diagnostics.get("recommendation_lock_sha256") != rec_content
            or diagnostics.get("evaluation_sha256_local_artifact") != file_sha256(evaluation_path)):
        raise ValueError("policy diagnostics reference different evaluation artifacts")
    eval_by_key = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in evaluation["evaluation_rows"]}
    if set(eval_by_key) != expected:
        raise ValueError("evaluation policy grid is incomplete")
    losses = evaluation["loss_table"]
    for row in evaluation["evaluation_rows"]:
        action_loss = losses[str(float(row["action"]))]["bias_corrected_loss"]
        if row["loss_bc"] != action_loss:
            raise ValueError("same-action evaluator loss mismatch")
    primary_deltas = []
    for seed in lock["g0"]["seed_ids"]:
        s0 = eval_by_key[(seed, 2, "S0")]["loss_bc"]
        fg = eval_by_key[(seed, 2, "M1+M2+M3+M4")]["loss_bc"]
        primary_deltas.append(s0 - fg)
    primary_mean = float(np.mean(primary_deltas))
    reported = summary["primary_B2_S0_minus_FullGreedy"]["mean_delta_loss_bc"]
    if not np.isclose(primary_mean, reported, rtol=0, atol=1e-14):
        raise ValueError("primary contrast does not reproduce from saved evaluation rows")
    secondary_deltas = []
    action_agreement = 0
    for seed in lock["g0"]["seed_ids"]:
        m4 = eval_by_key[(seed, 2, "M4")]
        fg = eval_by_key[(seed, 2, "M1+M2+M3+M4")]
        secondary_deltas.append(m4["loss_bc"] - fg["loss_bc"])
        m4_rec = next(r for r in rec["recommendations"]
            if r["g0_seed_id"] == seed and r["budget"] == 2 and r["policy_id"] == "M4")
        fg_rec = next(r for r in rec["recommendations"]
            if r["g0_seed_id"] == seed and r["budget"] == 2 and r["policy_id"] == "M1+M2+M3+M4")
        action_agreement += m4_rec["recommended_action"] == fg_rec["recommended_action"]
    secondary_mean = float(np.mean(secondary_deltas))
    if not np.isclose(secondary_mean,
            summary["secondary_B2_M4_minus_FullGreedy"]["mean_delta_loss_bc"], rtol=0, atol=1e-14):
        raise ValueError("secondary M4/Full Greedy contrast differs from saved aggregate")
    action_records = []
    for action in evaluation["action_order"]:
        action_records.append({"action": action, **evaluation["action_summary"][str(action)]})
    raw_paths = {"run_lock": lock_path, "recommendations": recommendation_path,
                 "evaluation": evaluation_path, "summary": summary_path,
                 "g0_manifest": g0_manifest_path, "policy_diagnostics": diagnostics_path}
    hashes = {name: {"sha256": file_sha256(path), "bytes": path.stat().st_size}
              for name, path in raw_paths.items()}
    return {"schema": "RESEARCH_D_ORIGINAL_PILOT_ARTIFACT_AUDIT_V1",
        "status": "PASS_SAVED_ARTIFACTS_AUDITED_RAW_RESPONSE_ROWS_NOT_AVAILABLE",
        "artifacts": hashes, "recommendation_rows": len(rec["recommendations"]),
        "evaluation_policy_rows": len(evaluation["evaluation_rows"]),
        "intervention_response_rows": evaluation["total_intervention_rows"],
        "action_summaries": action_records, "primary_recomputed_from_saved_aggregates": primary_mean,
        "primary_reported": reported, "g0_seed_count": len(lock["g0"]["seed_ids"]),
        "secondary_m4_minus_full_greedy_recomputed": secondary_mean,
        "m4_full_greedy_action_agreement_count_b2": int(action_agreement),
        "g0_manifest_records": len(g0.get("g0", [])),
        "policy_budget_diagnostic_rows": len(diagnostics.get("policy_budget_summary", [])),
        "bootstrap_raw_response_recomputation_possible": False,
        "reason": "The original evaluator discarded raw response rows; stored summaries support integrity and arithmetic checks, not independent re-bootstrap."}
