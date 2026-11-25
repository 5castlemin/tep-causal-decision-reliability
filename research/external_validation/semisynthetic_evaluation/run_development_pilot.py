"""Run outcome-blind structural preflight, then the bounded D development pilot."""
from __future__ import annotations

import argparse
import hashlib
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
        "research/external_validation/semisynthetic_evaluation/recommendation_worker.py",
        "research/external_validation/semisynthetic_evaluation/evaluate_worker.py",
        "research/external_validation/semisynthetic_evaluation/development_contract.json",
        "research/external_validation/semisynthetic_adapter/float_hard_do_adapter.py",
        "research/original_objective/policy_engine.py", "research/original_objective/g0_candidate.py",
        "src/integrated_pilot.py", "src/decision_mvp.py", "src/pilot_fit.py"]
    return {name: d.file_sha256(d.ROOT / name) for name in names}


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
              recommendation_input_sha256, training_csv_sha256):
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
        args.summary, args.execution_manifest, args.training_frame, args.recommendation_input])
    approved_id = "rd-development-reproduction-20261125-01"
    if args.run_id != approved_id:
        raise ValueError(f"this authorization permits only run id {approved_id}")
    for path in (args.lock, args.recommendations, args.evaluation, args.summary,
                 args.execution_manifest, args.training_frame, args.recommendation_input,
                 args.output):
        if path.exists(): raise FileExistsError(f"reproduction output already exists: {path.name}")
    original_lock_sha = d.file_sha256(args.original_lock)
    if original_lock_sha != "9f3c63c5aa33123a0619511bfc5cc129b887200700227c5fec4d2f4c2b88a404":
        raise ValueError("historical Development lock differs from its independently recorded SHA-256")
    original_audit = json.loads(args.original_audit.read_text(encoding="utf-8"))
    if (original_audit.get("status") != "PASS_SAVED_ARTIFACTS_AUDITED_RAW_RESPONSE_ROWS_NOT_AVAILABLE"
            or not original_audit.get("pipeline_exact_hash_recovered")
            or original_audit.get("historical_gate_promoted_retroactively") is not False):
        raise ValueError("historical source/artifact audit is incomplete or inconsistent")
    original_lock = json.loads(args.original_lock.read_text(encoding="utf-8"))
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
    if args.training_frame.exists() or args.recommendation_input.exists():
        raise FileExistsError("reproduction training/recommendation inputs already exist")
    args.training_frame.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = train.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8")
    args.training_frame.write_bytes(csv_bytes)
    recommendation_request = {"schema": "RESEARCH_D_RECOMMENDATION_INPUT_V1",
        "nodes": list(model.nodes), "reference_edges": [list(edge) for edge in model.graph.edges],
        "actions": actions, "training_numeric_sha256": train_hash,
        "g0": [{"seed_id": row["seed_id"], "record": row["record"],
                "graph_sha256": pe.graph_hash(row["g0"])} for row in g0_rows]}
    write_new(args.recommendation_input, recommendation_request)
    training_csv_sha = d.file_sha256(args.training_frame)
    recommendation_input_sha = d.file_sha256(args.recommendation_input)
    lock = make_lock(args, source_frame, train, model, actions, support_checks, fit_check,
        repo_identity, recommendation_input_sha, training_csv_sha)
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
        "intervention_samples_persisted": False})
    write_new(args.summary, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("structural", "pilot"), required=True)
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
    parser.add_argument("--execution-manifest", type=Path)
    parser.add_argument("--training-frame", type=Path)
    parser.add_argument("--recommendation-input", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--timeout-seconds", type=int, default=21600)
    args = parser.parse_args(argv)
    if args.mode == "structural":
        result = structural_mode(args)
    else:
        for name in ("structural", "lock", "recommendations", "evaluation", "summary", "r_library",
                     "original_lock", "original_audit", "execution_manifest", "training_frame", "recommendation_input"):
            if getattr(args, name) is None: parser.error(f"--{name.replace('_','-')} is required in pilot mode")
        result = pilot_mode(args)
    print(json.dumps({"status": result["status"], "output": args.output.name}, sort_keys=True))


if __name__ == "__main__":
    main()
