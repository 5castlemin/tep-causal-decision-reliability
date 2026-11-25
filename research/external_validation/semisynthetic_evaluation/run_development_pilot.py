"""Run outcome-blind structural preflight, then the bounded D development pilot."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.external_validation.semisynthetic_evaluation import reproducibility as repro
from research.original_objective import policy_engine as pe


def write_new(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): raise FileExistsError(f"refusing to overwrite existing Research D artifact: {path.name}")
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def truth_from_model(model):
    truth = {pe.pair(a, b): (a, b) for a, b in model.graph.edges}
    if not pe.dag(truth): raise ValueError("official Station1 graph is not a DAG")
    return truth


def structural_mode(args):
    source_info = d.verify_sources(args.source_root, args.data_root)
    model, source, fit_info = d.load_fit_station1(args.source_root, args.data_root, 91420261)
    truth, nodes = truth_from_model(model), list(model.nodes)
    ids = list(range(701001, 701065))
    rows = d.structural_rows(truth, nodes, ids)
    summary = d.structural_summary(rows, truth)
    detail = []
    for row in rows:
        record, g0 = row["record"], row["g0"]
        stats = pe.metrics(truth, g0, d.TASK_X, d.TASK_Y, pe.Config(fp_rule="A"))
        detail.append({"seed_id": row["seed_id"], "initial_graph_sha256": pe.graph_hash(g0),
            "error_counts": stats["counts"], "support": stats["support"],
            "proposals": record["summary"], "proposal_kinds": record["summary"]["proposed_by_kind"],
            "accepted_kinds": record["summary"]["accepted_by_kind"],
            "task_zone_error_present": any(stats["counts"]["M4"].values())})
    result = {"schema": "RESEARCH_D_STRUCTURAL_PREFLIGHT_V1", "status": "COMPLETED_OUTCOME_BLIND",
        "source": source_info, "fit_seed": 91420261, "official_graph": fit_info,
        "task": {"action": d.TASK_X, "target": d.TASK_Y,
                 "reference_path": [d.TASK_X, "Station1_mp_1", d.TASK_Y]},
        "summary": summary, "seed_records": detail,
        "outcome_data_generated_or_read": False, "decision_regret_calculated": False}
    write_new(args.output, result)
    return result


def code_hashes():
    names = ["research/external_validation/semisynthetic_evaluation/pipeline.py",
        "research/external_validation/semisynthetic_evaluation/run_development_pilot.py",
        "research/external_validation/semisynthetic_evaluation/reproducibility.py",
        "research/external_validation/semisynthetic_evaluation/analyze_development_reproduction.py",
        "research/external_validation/semisynthetic_evaluation/recommendation_worker.py",
        "research/external_validation/semisynthetic_evaluation/evaluate_worker.py",
        "research/external_validation/semisynthetic_evaluation/development_contract.json",
        "research/external_validation/semisynthetic_adapter/float_hard_do_adapter.py",
        "research/original_objective/policy_engine.py", "research/original_objective/g0_candidate.py",
        "src/integrated_pilot.py", "src/decision_mvp.py", "src/pilot_fit.py"]
    return {name: d.file_sha256(d.ROOT / name) for name in names}


AUTHORIZED_RUN_ID = "rd-development-reproduction-20261125-02"


def validate_recovery_inputs(args, original_lock=None):
    if args.recovery_manifest is None:
        return None
    manifest = json.loads(args.recovery_manifest.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "RESEARCH_D_REPRODUCTION_RECOVERY_INPUTS_V1"
            or manifest.get("run_id") != AUTHORIZED_RUN_ID
            or manifest.get("failed_attempt_id") != f"{AUTHORIZED_RUN_ID}-preflight-02-runner"
            or manifest.get("learner_training_rows") != 512
            or manifest.get("g0_seed_records") != 32
            or manifest.get("recommendation_rows") != 0
            or manifest.get("evaluator_rows") != 0):
        raise ValueError("recovery manifest does not describe the authorized post-training failure")
    if d.file_sha256(args.training_frame) != manifest.get("training_csv_sha256"):
        raise ValueError("preserved training CSV raw digest differs from recovery manifest")
    if d.file_sha256(args.recommendation_input) != manifest.get("recommendation_input_sha256"):
        raise ValueError("preserved recommendation input digest differs from recovery manifest")
    expected_numeric = manifest.get("training_numeric_sha256")
    lock = original_lock or json.loads(args.original_lock.read_text(encoding="utf-8"))
    if expected_numeric != lock["training"]["sha256"]:
        raise ValueError("recovery training numeric digest differs from the historical lock")
    train = repro.read_training_frame(args.training_frame, node_order=lock["node_order"],
        rows=512, expected_numeric_sha256=expected_numeric)
    if train.shape != (512, 6):
        raise ValueError("recovered learner input has an unexpected shape")
    request = json.loads(args.recommendation_input.read_text(encoding="utf-8"))
    if (request.get("schema") != "RESEARCH_D_RECOMMENDATION_INPUT_V1"
            or request.get("training_numeric_sha256") != expected_numeric
            or len(request.get("g0", [])) != 32
            or len(request.get("actions", [])) != 5):
        raise ValueError("preserved recommendation request does not match recovery manifest")
    return {"manifest_sha256": d.file_sha256(args.recovery_manifest),
        "training_csv_sha256": manifest["training_csv_sha256"],
        "training_numeric_sha256": expected_numeric,
        "recommendation_input_sha256": manifest["recommendation_input_sha256"],
        "training_rows_reused": 512, "g0_records_reconstructed_and_verified": 32,
        "additional_training_rows_generated": 0}


def dry_run_mode(args):
    if args.run_id != AUTHORIZED_RUN_ID:
        raise ValueError(f"this authorization permits only run id {AUTHORIZED_RUN_ID}")
    if args.attempt_id not in {f"{AUTHORIZED_RUN_ID}-preflight-0{i}" for i in range(1, 4)}:
        raise ValueError("preflight attempt ID must be one of the three authorized unique IDs")
    repo_identity = repro.repository_identity(d.ROOT)
    outputs = [args.output, args.lock, args.recommendations, args.evaluation, args.summary,
               args.execution_manifest, args.training_frame, args.recommendation_input,
               args.response_vectors]
    repro.require_external_outputs(d.ROOT, outputs)
    repro.require_external_outputs(d.ROOT, [args.historical_artifact_dir])
    original_lock = json.loads(args.original_lock.read_text(encoding="utf-8"))
    recovery = validate_recovery_inputs(args, original_lock)
    reused = {args.training_frame.resolve(), args.recommendation_input.resolve()} if recovery else set()
    for path in outputs:
        if path.resolve() in reused:
            continue
        if path.exists():
            raise FileExistsError(f"dry-run output path already exists: {path.name}")
    if d.file_sha256(args.original_lock) != "9f3c63c5aa33123a0619511bfc5cc129b887200700227c5fec4d2f4c2b88a404":
        raise ValueError("historical Development lock SHA-256 mismatch")
    original_audit = json.loads(args.original_audit.read_text(encoding="utf-8"))
    repro.validate_original_artifact_audit(original_audit)
    audit_status = original_audit["stored_artifact_audit"]["status"]
    historical_hashes = original_audit["stored_artifact_audit"]["artifacts"]
    historical_artifacts = {}
    for name in ("recommendations", "evaluation"):
        artifact = args.historical_artifact_dir / f"{name}.json"
        expected = historical_hashes[name]["sha256"]
        if not artifact.is_file() or d.file_sha256(artifact) != expected:
            raise ValueError(f"historical local {name} artifact missing or SHA-256 mismatch")
        historical_artifacts[name] = {"sha256": expected, "bytes": artifact.stat().st_size}
    current_codes = code_hashes()
    for name in ("research/external_validation/semisynthetic_adapter/float_hard_do_adapter.py",
                 "research/external_validation/semisynthetic_evaluation/development_contract.json",
                 "research/original_objective/g0_candidate.py", "research/original_objective/policy_engine.py",
                 "src/decision_mvp.py", "src/integrated_pilot.py", "src/pilot_fit.py"):
        if current_codes[name] != original_lock["code_sha256"][name]:
            raise ValueError(f"historical scientific dependency digest mismatch: {name}")
    runtime = repro.runtime_fingerprint()
    if any(runtime.get(key) != value for key, value in original_lock["runtime"].items()):
        raise ValueError("runtime fingerprint differs from historical Development")
    source_info = d.verify_sources(args.source_root, args.data_root)
    external_source = repro.external_source_manifest(args.source_root)
    structural = json.loads(args.structural.read_text(encoding="utf-8"))
    if structural.get("status") != "COMPLETED_OUTCOME_BLIND" or structural.get("summary", {}).get("n_g0") != 64:
        raise ValueError("outcome-blind 64-seed structural preflight is not valid")
    structural_graph = structural.get("official_graph", {})
    if (structural_graph.get("nodes") != original_lock.get("node_order")
            or len(structural_graph.get("edges", [])) != 7
            or structural.get("source") != original_lock.get("source")):
        raise ValueError("structural preflight graph/source differs from the original lock")
    structural_truth = {pe.pair(a, b): (a, b) for a, b in structural_graph["edges"]}
    if pe.graph_hash(structural_truth) != original_lock["graph_sha256"]:
        raise ValueError("structural preflight reference graph digest mismatch")

    # Confirm the exact package that the runner would import, without fitting or sampling.
    sys.path.insert(0, str(args.source_root.resolve()))
    spec = importlib.util.find_spec("causalAssembly")
    package = importlib.import_module("causalAssembly")
    package_file = Path(package.__file__).resolve()
    source_path = args.source_root.resolve()
    if source_path not in package_file.parents or spec is None:
        raise ValueError("imported causalAssembly package is not from the pinned source checkout")
    package_version = importlib.metadata.version("causalAssembly")
    if package_version != "1.2.1":
        raise ValueError("imported causalAssembly distribution version is not 1.2.1")

    actions = original_lock["action_grid"]["values"]
    if actions != [0.000155911358968, 0.0001724093665238, 0.00018679686613765,
                   0.00020263502221978, 0.00022589388613683002]:
        raise ValueError("historical action grid differs from the authorized fixed values")
    csv_roundtrip = repro.validate_csv_float_round_trip(actions +
        [0.1, 1e-200, float(np.nextafter(0.5, 1.0)), 1.2345678901234567])
    help_results = {}
    for module in ("recommendation_worker", "evaluate_worker"):
        command = [sys.executable, "-m",
            f"research.external_validation.semisynthetic_evaluation.{module}", "--help"]
        completed = subprocess.run(command, cwd=d.ROOT, text=True, capture_output=True, timeout=30)
        if completed.returncode != 0:
            raise RuntimeError(f"{module} CLI dry-run failed: {completed.stderr[-1000:]}")
        help_results[module] = {"exit_code": completed.returncode, "help_available": True}
    preflight = {"schema": "RESEARCH_D_REPRODUCTION_PREFLIGHT_V1",
        "status": "PASS_NO_RESEARCH_SAMPLES_GENERATED",
        "attempt_id": args.attempt_id,
        "run_id": args.run_id, "repository": repo_identity,
        "code_sha256": current_codes, "runtime": runtime, "source": source_info,
        "external_source": external_source, "original_lock_sha256": d.file_sha256(args.original_lock),
        "original_audit_sha256": d.file_sha256(args.original_audit),
        "original_audit_status": audit_status,
        "historical_artifact_sha256": historical_artifacts,
        "recovery_inputs": recovery,
        "structural_preflight_sha256": d.file_sha256(args.structural),
        "package_import": {"version": package_version,
            "module_file_relative_to_pinned_source": package_file.relative_to(source_path).as_posix()},
        "csv_float_roundtrip": csv_roundtrip, "worker_cli": help_results,
        "planned_action_grid": actions,
        "research_samples_generated": 0,
        "checks": {"clean_worktree": True, "outputs_absent": True,
            "original_sources_and_artifacts": True, "runtime_and_packages": True,
            "pinned_source_and_data": True, "structural_preflight": True,
            "package_import_path": True, "roundtrip_csv_exact": True,
            "worker_cli_arguments": True, "recovery_inputs_verified": recovery is not None}}
    write_new(args.output, preflight)
    return preflight


def fit_repro_check(source_root, data_root):
    import numpy as np
    first, _source, info1 = d.load_fit_station1(source_root, data_root, 91420261)
    second, _source2, info2 = d.load_fit_station1(source_root, data_root, 91420261)
    check_seed = d.derive_seed("fit-repro-check", 91420265)
    first.random_state = np.random.default_rng(check_seed)
    second.random_state = np.random.default_rng(check_seed)
    first_frame = first.sample_from_drf(size=16)
    second_frame = second.sample_from_drf(size=16)
    d._validate_frame(first_frame, list(first.nodes), 16)
    d._validate_frame(second_frame, list(second.nodes), 16)
    digest1 = hashlib.sha256(first_frame.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    digest2 = hashlib.sha256(second_frame.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    if digest1 != digest2:
        raise RuntimeError("same-source same-seed DRF refit did not reproduce the check sample")
    del first_frame, second_frame, second
    return first, info1, {"same_seed_refit_sample_sha256": digest1,
        "exact_match": True, "check_rows_per_fit": 16,
        "response_values_recorded": False, "both_fit_seconds": [info1["fit_seconds"], info2["fit_seconds"]]}


def make_lock(args, source, train, model, actions, support_checks, fit_check, repo_identity,
              recommendation_input_sha256, training_csv_sha256, preflight_sha256):
    y = train[d.TASK_Y].to_numpy(dtype=float)
    target, scale = float(y.mean() + y.std(ddof=1)), float(y.std(ddof=1))
    if not np.isfinite([target, scale]).all() or scale <= 0: raise ValueError("invalid training target/scale")
    source_info = d.verify_sources(args.source_root, args.data_root)
    train_hash = hashlib.sha256(train.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    train_check_seed = d.derive_seed("training-sample", 91420262)
    lock = {"schema": "RESEARCH_D_DEVELOPMENT_RUN_LOCK_V2",
        "mode": "development_reproduction_only", "run_id": args.run_id,
        "repository": repo_identity, "fit_seed": 91420261,
        "locked_before_evaluator_generation": True,
        "created_before_intervention_evaluation": True,
        "base_contract_sha256": d.file_sha256(d.CONTRACT_PATH), "source": source_info,
        "recommendation_input_sha256": recommendation_input_sha256,
        "training_frame_csv_sha256": training_csv_sha256,
        "preflight_report_sha256": preflight_sha256,
        "response_vectors_filename": args.response_vectors.name,
        "graph_sha256": pe.graph_hash(truth_from_model(model)), "node_order": list(model.nodes),
        "task": {"action": d.TASK_X, "target": d.TASK_Y,
            "reference_path": [d.TASK_X, "Station1_mp_1", d.TASK_Y], "strict_indirect_only": True,
            "interpretation": "virtual benchmark intervention; not physical controllability"},
        "action_grid": {"quantiles": [0.1, 0.3, 0.5, 0.7, 0.9], "values": actions,
            "support_checks": support_checks, "joint_support_claim": False},
        "training": {"n": 512, "seed": train_check_seed, "sha256": train_hash,
            "all_policies_share": True},
        "target_scale": {"target": target, "scale": scale, "delta_sd": 1,
            "rule": "mean(Y_train)+1*sample_sd(Y_train), ddof=1"},
        "g0": {"seed_ids": list(range(702001, 702033)), "q": 0.15, "r": 0.05,
            "dag_invalid": "record and reject without redraw", "policy_engine": "existing Research C policy_engine.py",
            "policy_count_per_graph_budget": 17, "budgets": [0, 1, 2, 3, 4]},
        "evaluation": {"rows_per_action": 256, "action_count": len(actions),
            "total_intervention_rows": len(actions) * 256,
            "seed_root": d.derive_seed("evaluation-root", 91420264),
            "bootstrap_replicates": 2000, "bootstrap_seed": 91420263,
            "loss_estimator": "bias-corrected squared mean; no truncation",
            "uncertainty": "2000 replicate paired G0 plus within-action row bootstrap"},
        "fit_reproducibility": {**fit_check, "check_seed": d.derive_seed("fit-repro-check", 91420265)},
        "policy_ids": list(d.POLICY_IDS),
        "runtime": repro.runtime_fingerprint(),
        "code_sha256": code_hashes(),
        "resource_limits": {"wall_time_seconds": args.timeout_seconds, "max_g0": 32,
            "max_action_count": 5, "max_rows_per_action": 256,
            "max_total_intervention_rows": 1280, "sampling_parallelism": 1,
            "memory_peak_measured": False},
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "final_evaluation_seeds_or_samples_created": False}
    return lock


def summarize_pilot(result):
    from collections import defaultdict
    primary = d.paired_primary(result)
    rows = result["evaluation_rows"]
    groups = defaultdict(list)
    for row in rows: groups[(row["budget"], row["policy_id"])].append(row)
    policy_summary = []
    for (budget, policy), values in sorted(groups.items()):
        policy_summary.append({"budget": budget, "policy_id": policy,
            "mean_loss_bc": float(np.mean([v["loss_bc"] for v in values])),
            "mean_loss_plugin": float(np.mean([v["loss_plugin"] for v in values])),
            "mean_repair_cost": float(np.mean([v["repair_cost"] for v in values])),
            "same_action_fraction": None, "g0_n": len(values)})
    m4 = [r for r in rows if r["budget"] == 2 and r["policy_id"] == "M4"]
    fg = {r["g0_seed_id"]: r for r in rows if r["budget"] == 2 and r["policy_id"] == "M1+M2+M3+M4"}
    m4_deltas = [r["loss_bc"] - fg[r["g0_seed_id"]]["loss_bc"] for r in m4]
    return {"schema": "RESEARCH_D_DEVELOPMENT_PILOT_SUMMARY_V1", "status": "COMPLETED",
        "primary_B2_S0_minus_FullGreedy": primary,
        "primary_uncertainty": result["primary_two_source_uncertainty"],
        "secondary_B2_M4_minus_FullGreedy": {"n_g0": len(m4_deltas),
            "mean_delta_loss_bc": float(np.mean(m4_deltas)),
            "positive_fraction": float(np.mean(np.asarray(m4_deltas) > 0))},
        "graph_free_association_baseline": result["graph_free_association_baseline"],
        "action_summaries": result["action_summary"], "action_losses": result["loss_table"],
        "policy_budget_summary": policy_summary,
        "g0_count": len({r["g0_seed_id"] for r in rows}), "g0_are_independent_external_scms": False,
        "one_fixed_dgp_and_one_training_sample": True, "final_evaluation": False,
        "interpretation": "development-only conditional robustness pilot; no physical population inference"}


def pilot_mode(args):
    repo_identity = repro.repository_identity(d.ROOT)
    repro.require_external_outputs(d.ROOT, [args.output, args.lock, args.recommendations, args.evaluation,
        args.summary, args.execution_manifest, args.training_frame, args.recommendation_input,
        args.response_vectors, args.historical_artifact_dir, args.preflight_report])
    approved_id = AUTHORIZED_RUN_ID
    if args.run_id != approved_id:
        raise ValueError(f"this authorization permits only run id {approved_id}")
    original_lock = json.loads(args.original_lock.read_text(encoding="utf-8"))
    recovery = validate_recovery_inputs(args, original_lock)
    reused = {args.training_frame.resolve(), args.recommendation_input.resolve()} if recovery else set()
    for path in (args.lock, args.recommendations, args.evaluation, args.summary,
                 args.execution_manifest, args.training_frame, args.recommendation_input,
                 args.response_vectors, args.output):
        if path.resolve() in reused:
            continue
        if path.exists(): raise FileExistsError(f"reproduction output already exists: {path.name}")
    original_lock_sha = d.file_sha256(args.original_lock)
    if original_lock_sha != "9f3c63c5aa33123a0619511bfc5cc129b887200700227c5fec4d2f4c2b88a404":
        raise ValueError("historical Development lock differs from its independently recorded SHA-256")
    original_audit = json.loads(args.original_audit.read_text(encoding="utf-8"))
    repro.validate_original_artifact_audit(original_audit)
    preflight = json.loads(args.preflight_report.read_text(encoding="utf-8"))
    if (preflight.get("status") != "PASS_NO_RESEARCH_SAMPLES_GENERATED"
            or preflight.get("run_id") != approved_id
            or preflight.get("repository") != repo_identity
            or preflight.get("code_sha256") != code_hashes()
            or preflight.get("source") != d.verify_sources(args.source_root, args.data_root)
            or preflight.get("recovery_inputs") != recovery
            or preflight.get("historical_artifact_sha256") is None):
        raise ValueError("actual-input dry-run does not bind to this clean code/source/run")
    for name, record in preflight["historical_artifact_sha256"].items():
        artifact = args.historical_artifact_dir / f"{name}.json"
        if not artifact.is_file() or d.file_sha256(artifact) != record["sha256"]:
            raise ValueError(f"historical {name} artifact changed after dry-run")
    repro.validate_csv_float_round_trip(json.loads(args.original_lock.read_text(encoding="utf-8"))
        ["action_grid"]["values"])
    current_codes = code_hashes()
    for name in ("research/external_validation/semisynthetic_adapter/float_hard_do_adapter.py",
                 "research/external_validation/semisynthetic_evaluation/development_contract.json",
                 "research/original_objective/g0_candidate.py", "research/original_objective/policy_engine.py",
                 "src/decision_mvp.py", "src/integrated_pilot.py", "src/pilot_fit.py"):
        if current_codes[name] != original_lock["code_sha256"][name]:
            raise ValueError(f"recovered historical dependency differs from original lock: {name}")
    actual_runtime = repro.runtime_fingerprint()
    if any(actual_runtime.get(k) != v for k, v in original_lock["runtime"].items()):
        raise ValueError("runtime differs from the original Development Pilot")
    structural = json.loads(args.structural.read_text(encoding="utf-8"))
    if structural.get("status") != "COMPLETED_OUTCOME_BLIND" or structural.get("summary", {}).get("n_g0") != 64:
        raise ValueError("64-seed outcome-blind structural preflight must complete first")
    model, _fit_info, fit_check = fit_repro_check(args.source_root, args.data_root)
    import hashlib
    check_seed = d.derive_seed("fit-repro-check", 91420265)
    model.random_state = np.random.default_rng(check_seed)
    check_frame = model.sample_from_drf(size=16)
    check_digest = hashlib.sha256(check_frame.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    if check_digest != fit_check["same_seed_refit_sample_sha256"]:
        raise RuntimeError("selected fitted DGP differs from deterministic refit check")
    if check_digest != original_lock["fit_reproducibility"]["same_seed_refit_sample_sha256"]:
        raise RuntimeError("same-seed DRF refit check differs from original Development")
    del check_frame
    train_seed = d.derive_seed("training-sample", 91420262)
    if recovery:
        train = repro.read_training_frame(args.training_frame, node_order=list(model.nodes),
            rows=512, expected_numeric_sha256=original_lock["training"]["sha256"])
        values = train.to_numpy(dtype=float)
        train_hash = hashlib.sha256(values.tobytes(order="C")).hexdigest()
    else:
        model.random_state = np.random.default_rng(train_seed)
        train = model.sample_from_drf(size=512)
        values = d._validate_frame(train, list(model.nodes), 512)
        train_hash = hashlib.sha256(train.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
        if train_hash != original_lock["training"]["sha256"]:
            raise RuntimeError("same-seed learner-training frame differs from original Development")
    source_info = d.verify_sources(args.source_root, args.data_root)
    import pandas as pd
    # Retain only the learner training frame in this process.
    train = pd.DataFrame(values, columns=list(model.nodes))
    source_csv = pd.read_csv(args.data_root / "assembly_sample--assembly_line_500.csv")
    source_frame = source_csv.loc[:, list(model.nodes)]
    actions, support_checks = d.action_grid(source_frame, train, model)
    if actions != original_lock["action_grid"]["values"]:
        raise RuntimeError("same-source action grid differs from original Development")
    train_hash = hashlib.sha256(train.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    truth = truth_from_model(model)
    g0_rows = d.structural_rows(truth, list(model.nodes), list(range(702001, 702033)))
    recommendation_request = {"schema": "RESEARCH_D_RECOMMENDATION_INPUT_V1",
        "nodes": list(model.nodes), "reference_edges": [list(edge) for edge in model.graph.edges],
        "actions": actions, "training_numeric_sha256": train_hash,
        "g0": [{"seed_id": row["seed_id"], "record": row["record"],
                "graph_sha256": pe.graph_hash(row["g0"])} for row in g0_rows]}
    if recovery:
        existing_request = json.loads(args.recommendation_input.read_text(encoding="utf-8"))
        if existing_request != recommendation_request:
            raise ValueError("preserved recommendation request differs from deterministic G0 reconstruction")
    else:
        if args.training_frame.exists() or args.recommendation_input.exists():
            raise FileExistsError("reproduction training/recommendation inputs already exist")
        args.training_frame.parent.mkdir(parents=True, exist_ok=True)
        csv_bytes = repro.serialize_training_frame(train)
        args.training_frame.write_bytes(csv_bytes)
        roundtrip_train = repro.read_training_frame(args.training_frame, node_order=list(model.nodes),
            rows=512, expected_numeric_sha256=train_hash)
        if roundtrip_train.to_numpy(dtype=float).tobytes(order="C") != train.to_numpy(dtype=float).tobytes(order="C"):
            raise RuntimeError("serialized learner frame differs byte-for-byte after CSV round-trip")
        write_new(args.recommendation_input, recommendation_request)
    training_csv_sha = d.file_sha256(args.training_frame)
    recommendation_input_sha = d.file_sha256(args.recommendation_input)
    lock = make_lock(args, source_frame, train, model, actions, support_checks, fit_check,
        repo_identity, recommendation_input_sha, training_csv_sha, d.file_sha256(args.preflight_report))
    lock["fit_reproducibility"]["same_seed_refit_sample_sha256"] = check_digest
    repro.validate_reproduction_science(lock, original_lock)
    if args.lock.exists(): raise FileExistsError("pilot run lock already exists; refuse seed/config reuse")
    write_new(args.lock, lock)
    contract_hash = d.file_sha256(args.lock)
    del model, train, source_csv, source_frame, g0_rows
    rec_command = [sys.executable, "-m", "research.external_validation.semisynthetic_evaluation.recommendation_worker",
        "--input", str(args.recommendation_input.resolve()), "--input-sha256", recommendation_input_sha,
        "--training", str(args.training_frame.resolve()), "--training-sha256", training_csv_sha,
        "--contract-sha256", contract_hash, "--output", str(args.recommendations.resolve())]
    rec_started = time.perf_counter()
    rec_result = subprocess.run(rec_command, cwd=d.ROOT, text=True, capture_output=True,
        timeout=args.timeout_seconds)
    if rec_result.returncode != 0:
        raise RuntimeError(f"recommendation worker failed ({rec_result.returncode}): {rec_result.stderr[-2000:]}")
    recommendation_manifest = json.loads(args.recommendations.read_text(encoding="utf-8"))
    if recommendation_manifest.get("row_count") != 2720:
        raise RuntimeError("recommendation worker emitted an incomplete policy grid")
    invocation = repro.locked_invocation(lock)
    execution_manifest = repro.build_execution_manifest(root=d.ROOT,
        source_root=args.source_root, data_root=args.data_root, contract_path=args.lock,
        recommendation_path=args.recommendations, code_names=list(lock["code_sha256"]),
        run_id=args.run_id, invocation=invocation,
        support_artifacts={"training_frame_csv": args.training_frame,
                           "recommendation_input": args.recommendation_input})
    write_new(args.execution_manifest, execution_manifest)
    execution_manifest_sha = d.file_sha256(args.execution_manifest)
    if repro.repository_identity(d.ROOT) != repo_identity:
        raise RuntimeError("repository changed after lock and before evaluator execution")
    # The evaluator is a new process with only the locked file, source and fitted
    # generator recipe. It has no recommendation engine or policy module loaded.
    env = os.environ.copy()
    env["R_LIBS_USER"] = str(args.r_library.resolve())
    command = [sys.executable, "-m", "research.external_validation.semisynthetic_evaluation.evaluate_worker",
        "--source-root", str(args.source_root.resolve()), "--data-root", str(args.data_root.resolve()),
        "--lock", str(args.recommendations.resolve()), "--contract", str(args.lock.resolve()),
        "--output", str(args.evaluation.resolve()), "--fit-seed", "91420261",
        "--fit-check-seed", str(check_seed), "--fit-check-sha256", fit_check["same_seed_refit_sample_sha256"],
        "--evaluation-seed-root", str(lock["evaluation"]["seed_root"]), "--rows", str(lock["evaluation"]["rows_per_action"]),
        "--run-id", args.run_id, "--execution-manifest", str(args.execution_manifest.resolve()),
        "--execution-manifest-sha256", execution_manifest_sha,
        "--bootstrap-replicates", str(lock["evaluation"]["bootstrap_replicates"]),
        "--bootstrap-seed", str(lock["evaluation"]["bootstrap_seed"])]
    command += ["--response-vectors", str(args.response_vectors.resolve())]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=d.ROOT, env=env, text=True, capture_output=True,
                               timeout=args.timeout_seconds)
    if completed.returncode != 0:
        raise RuntimeError(f"evaluator subprocess failed ({completed.returncode}): {completed.stderr[-2000:]}")
    evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
    if evaluation["recommendation_lock_sha256"] != json.loads(args.recommendations.read_text(encoding="utf-8"))["content_sha256"]:
        raise RuntimeError("evaluator result is not bound to recommendation lock")
    if evaluation["total_intervention_rows"] > 1280 or evaluation["rows_per_action"] != 256:
        raise RuntimeError("pilot exceeded locked evaluator limit")
    summary = summarize_pilot(evaluation)
    repro.verify_execution_manifest(root=d.ROOT, source_root=args.source_root, data_root=args.data_root,
        contract_path=args.lock, recommendation_path=args.recommendations,
        execution_manifest_path=args.execution_manifest, expected_manifest_sha256=execution_manifest_sha,
        code_names=list(lock["code_sha256"]), invocation=invocation,
        support_artifacts={"training_frame_csv": args.training_frame,
                           "recommendation_input": args.recommendation_input})
    summary.update({"run_lock_sha256": contract_hash,
        "run_id": args.run_id, "execution_manifest_sha256": execution_manifest_sha,
        "recommendation_lock_sha256": evaluation["recommendation_lock_sha256"],
        "training_sha256": train_hash, "fit_reproducibility": fit_check,
        "source": source_info, "wall_seconds_after_lock": time.perf_counter() - started,
        "evaluator_stdout": completed.stdout.strip(), "evaluator_stderr_tail": completed.stderr[-1200:],
        "recommendation_rows": json.loads(args.recommendations.read_text(encoding="utf-8"))["row_count"],
        "recommendation_worker_stdout": rec_result.stdout.strip(),
        "recommendation_worker_seconds": time.perf_counter() - rec_started,
        "recommendations_locked_before_evaluation": True,
        "intervention_samples_persisted": True})
    summary["response_vectors_artifact"] = evaluation.get("response_vectors_artifact")
    write_new(args.summary, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("structural", "dry-run", "pilot"), required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--structural", type=Path)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--recommendations", type=Path)
    parser.add_argument("--evaluation", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--r-library", type=Path)
    parser.add_argument("--original-lock", type=Path)
    parser.add_argument("--original-audit", type=Path)
    parser.add_argument("--preflight-report", type=Path)
    parser.add_argument("--historical-artifact-dir", type=Path)
    parser.add_argument("--execution-manifest", type=Path)
    parser.add_argument("--training-frame", type=Path)
    parser.add_argument("--recommendation-input", type=Path)
    parser.add_argument("--response-vectors", type=Path)
    parser.add_argument("--recovery-manifest", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--attempt-id")
    parser.add_argument("--timeout-seconds", type=int, default=21600)
    args = parser.parse_args(argv)
    if args.mode == "structural":
        result = structural_mode(args)
    elif args.mode == "dry-run":
        for name in ("structural", "lock", "recommendations", "evaluation", "summary", "r_library",
                     "original_lock", "original_audit", "historical_artifact_dir", "execution_manifest", "training_frame", "recommendation_input", "response_vectors", "attempt_id", "recovery_manifest"):
            if getattr(args, name) is None: parser.error(f"--{name.replace('_','-')} is required in dry-run mode")
        os.environ["R_LIBS_USER"] = str(args.r_library.resolve())
        result = dry_run_mode(args)
    else:
        for name in ("structural", "lock", "recommendations", "evaluation", "summary", "r_library",
                     "original_lock", "original_audit", "preflight_report", "historical_artifact_dir", "execution_manifest", "training_frame", "recommendation_input", "response_vectors", "recovery_manifest"):
            if getattr(args, name) is None: parser.error(f"--{name.replace('_','-')} is required in pilot mode")
        result = pilot_mode(args)
    print(json.dumps({"status": result["status"], "output": args.output.name}, sort_keys=True))


if __name__ == "__main__":
    main()
