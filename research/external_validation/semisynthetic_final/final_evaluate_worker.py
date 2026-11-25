"""Final-only evaluator; imports no Research C policy or recommendation code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import sample_hard_do
from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.external_validation.semisynthetic_evaluation.reproducibility import read_training_frame
from research.external_validation.semisynthetic_final import final_pipeline as fp


def atomic_npy_exclusive(path: Path, values: np.ndarray) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"response vector already exists; overwrite/re-generation denied: {path.name}")
    tmp = path.with_name(path.name + ".partial")
    if tmp.exists():
        raise FileExistsError("partial response vector exists; continuation state is ambiguous")
    with tmp.open("xb") as stream:
        np.save(stream, values, allow_pickle=False)
        stream.flush(); os.fsync(stream.fileno())
    raw = tmp.read_bytes()
    os.replace(tmp, path)
    return hashlib.sha256(raw).hexdigest(), len(raw)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--training", type=Path, required=True)
    p.add_argument("--run-lock", type=Path, required=True)
    p.add_argument("--run-lock-sha256", required=True)
    p.add_argument("--recommendations", type=Path, required=True)
    p.add_argument("--execution-manifest", type=Path, required=True)
    p.add_argument("--evaluation-manifest", type=Path, required=True)
    p.add_argument("--response-dir", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    args = p.parse_args(argv)
    outpaths = [args.evaluation_manifest, args.state, args.response_dir]
    from research.external_validation.semisynthetic_evaluation.reproducibility import require_external_outputs
    require_external_outputs(fp.ROOT, outpaths)
    if args.evaluation_manifest.exists() or args.state.exists():
        raise FileExistsError("final evaluator outputs already exist")
    if args.response_dir.exists() and any(args.response_dir.iterdir()):
        raise FileExistsError("final response directory contains prior material")
    lock = fp.verify_lock(lock_path=args.run_lock, expected_lock_sha256=args.run_lock_sha256,
        source_root=args.source_root, data_root=args.data_root, training_path=args.training,
        recommendation_path=args.recommendations, execution_manifest_path=args.execution_manifest)
    runlock, rec, manifest = fp.verify_final_artifacts(args.run_lock, args.execution_manifest,
                                                        args.recommendations)
    if any(name.startswith("research.original_objective") for name in sys.modules):
        raise RuntimeError("policy/recommendation module unexpectedly imported by evaluator")
    from research.external_validation.semisynthetic_evaluation.reproducibility import runtime_fingerprint
    # Final environment is checked in the parent verifier; the evaluator repeats exact source checks.
    if d.verify_sources(args.source_root, args.data_root) != lock["source"]:
        raise ValueError("pinned source/data mismatch at evaluator entry")
    nodes = runlock["graph"]["nodes"]
    train = read_training_frame(args.training, node_order=nodes, rows=512,
        expected_numeric_sha256=runlock["training"]["numeric_sha256"])
    if hashlib.sha256(train.to_numpy(dtype=float).tobytes(order="C")).hexdigest() != \
            runlock["training"]["numeric_sha256"]:
        raise ValueError("learner training numeric digest changed")
    model, _source, fit_info = fp.fit_diagnostic(args.source_root, args.data_root)
    if fit_info["graph_sha256"] != runlock["graph"]["sha256"]:
        raise ValueError("evaluator graph does not match locked Station1 reference")
    if set(rec["g0_seed_ids"]) != set(runlock["sampling"]["g0_ids"]):
        raise ValueError("recommendation G0 IDs differ from final lock")
    actions = [float(x) for x in runlock["task"]["actions"]]
    seeds = [fp.derive_final_seed(f"action|{i}|{repr(float(action))}")
             for i, action in enumerate(actions)]
    if len(set(seeds)) != len(seeds):
        raise ValueError("duplicate final action RNG streams")
    args.response_dir.mkdir(parents=True, exist_ok=True)
    state = {"schema": "RESEARCH_D_FINAL_EVALUATOR_STATE_V1", "run_id": runlock["run_id"],
        "status": "SAMPLING_STARTED", "completed_action_indices": [], "rows_completed": 0,
        "active_action_index": None, "active_action_seed": None, "active_call_rows": 0,
        "ambiguity_rule": "If a hard-do call fails before its complete vector is atomically saved, generated internal draws are unknown; stop and do not retry this final run."}
    fp.atomic_json(args.state, state)
    action_records = []
    started = time.perf_counter()
    for index, (action, seed) in enumerate(zip(actions, seeds)):
        state["active_action_index"] = index; state["active_action_seed"] = seed
        state["active_call_rows"] = 2500
        fp.atomic_json(args.state, state)
        frame = sample_hard_do(model, "Station1_mp_0", action, size=2500,
            rng=np.random.default_rng(seed), smoothed=True)
        if list(frame.columns) != nodes or frame.shape != (2500, 6):
            raise ValueError("final hard-do sample schema or shape mismatch")
        values = frame.to_numpy(dtype=np.float64)
        if not np.isfinite(values).all():
            raise ValueError("final hard-do draw includes NaN or infinity")
        if not np.all(values[:, nodes.index("Station1_mp_0")] == action):
            raise ValueError("hard-do action was not applied exactly")
        y = values[:, nodes.index("Station1_mp_4")].copy()
        path = args.response_dir / f"action_{index:02d}.npy"
        vector_sha, vector_bytes = atomic_npy_exclusive(path, y)
        action_records.append({"index": index, "action": action, "seed": seed,
            "rows": len(y), "response_sha256": vector_sha, "bytes": vector_bytes,
            "filename": path.name})
        state["completed_action_indices"].append(index)
        state["rows_completed"] += len(y)
        state["active_action_index"] = None; state["active_action_seed"] = None
        state["active_call_rows"] = 0
        fp.atomic_json(args.state, state)
        del frame, values, y
    total_seconds = time.perf_counter() - started
    evaluation = {"schema": "RESEARCH_D_FINAL_RESPONSE_MANIFEST_V1", "run_id": runlock["run_id"],
        "run_lock_sha256": args.run_lock_sha256,
        "execution_manifest_sha256": d.file_sha256(args.execution_manifest),
        "recommendation_raw_sha256": d.file_sha256(args.recommendations),
        "action_records": action_records, "rows_per_action": 2500,
        "total_rows": sum(x["rows"] for x in action_records),
        "sampling_seconds": total_seconds, "fit_seconds": fit_info["fit_seconds"],
        "diagnostic_sha256": fit_info["diagnostic_sha256"],
        "rows_reused_from_prior_evaluation": 0,
        "outcomes_used_to_change_recommendations_or_contract": False}
    fp.atomic_json(args.evaluation_manifest, evaluation)
    state["status"] = "ALL_ACTION_VECTORS_SAVED"; state["completed_at_epoch"] = time.time()
    fp.atomic_json(args.state, state)
    if d.verify_sources(args.source_root, args.data_root) != lock["source"]:
        raise ValueError("source/data changed during final intervention sampling")
    if fp.contract_hash() != lock["contract_sha256"] or fp.file_sha(args.run_lock) != args.run_lock_sha256:
        raise ValueError("contract or run lock changed during final intervention sampling")
    print(json.dumps({"status": "PASS_RESPONSE_GENERATION", "total_rows": evaluation["total_rows"],
        "sampling_seconds": total_seconds, "response_hashes": [r["response_sha256"] for r in action_records]},
        sort_keys=True))


if __name__ == "__main__":
    main()
