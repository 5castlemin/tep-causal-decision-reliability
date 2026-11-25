"""Evaluator-only child process; does not import recommendation or policy code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from research.external_validation.semisynthetic_evaluation.pipeline import (
    ROOT, evaluate_locked, load_fit_station1, verify_sources,
)
from research.external_validation.semisynthetic_evaluation import reproducibility as repro


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fit-seed", type=int, required=True)
    parser.add_argument("--fit-check-seed", type=int, required=True)
    parser.add_argument("--fit-check-sha256", required=True)
    parser.add_argument("--evaluation-seed-root", type=int, required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--execution-manifest", type=Path, required=True)
    parser.add_argument("--execution-manifest-sha256", required=True)
    parser.add_argument("--bootstrap-replicates", type=int, required=True)
    parser.add_argument("--bootstrap-seed", type=int, required=True)
    args = parser.parse_args(argv)
    repro.require_external_outputs(ROOT, [args.lock, args.contract, args.output,
        args.execution_manifest])
    if args.output.exists(): raise FileExistsError("refusing to overwrite evaluator output")
    verify_sources(args.source_root, args.data_root)
    # No policy engine, learner, G0 generator, or recommendation module is
    # imported in this process. It reads a hash-verified locked manifest only.
    if any(name.startswith("research.original_objective") for name in sys.modules):
        raise RuntimeError("recommendation/policy module unexpectedly loaded in evaluator")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    invocation = {"mode": "development_reproduction_only", "run_id": args.run_id,
        "fit_seed": args.fit_seed, "fit_check_seed": args.fit_check_seed,
        "fit_check_sha256": args.fit_check_sha256,
        "evaluation_seed_root": args.evaluation_seed_root, "rows_per_action": args.rows,
        "actions": contract["action_grid"]["values"],
        "target": contract["target_scale"]["target"], "scale": contract["target_scale"]["scale"],
        "g0_seed_ids": contract["g0"]["seed_ids"], "budgets": contract["g0"]["budgets"],
        "policy_ids": contract["policy_ids"],
        "bootstrap_replicates": args.bootstrap_replicates, "bootstrap_seed": args.bootstrap_seed}
    if contract.get("run_id") != args.run_id or contract.get("fit_seed") != args.fit_seed:
        raise ValueError("evaluator run/fit seed differs from the scientific lock")
    if args.fit_check_seed != contract["fit_reproducibility"]["check_seed"] or \
            args.fit_check_sha256 != contract["fit_reproducibility"]["same_seed_refit_sample_sha256"]:
        raise ValueError("evaluator DRF check seed/digest differs from the scientific lock")
    repro.verify_execution_manifest(root=ROOT,
        source_root=args.source_root, data_root=args.data_root, contract_path=args.contract,
        recommendation_path=args.lock, execution_manifest_path=args.execution_manifest,
        expected_manifest_sha256=args.execution_manifest_sha256,
        code_names=list(contract["code_sha256"]), invocation=invocation, output_path=args.output)
    model, _source, fit_info = load_fit_station1(args.source_root, args.data_root, args.fit_seed)
    import numpy as np
    model.random_state = np.random.default_rng(args.fit_check_seed)
    check = model.sample_from_drf(size=16)
    raw = check.to_numpy(dtype=float).tobytes(order="C")
    if hashlib.sha256(raw).hexdigest() != args.fit_check_sha256:
        raise RuntimeError("evaluator DRF deterministic refit check failed")
    del check
    result = evaluate_locked(model=model, lock_path=args.lock, contract_path=args.contract,
        output_path=args.output, evaluation_seed_root=args.evaluation_seed_root,
        rows_per_action=args.rows, bootstrap_replicates=args.bootstrap_replicates,
        bootstrap_seed=args.bootstrap_seed)
    result["evaluator_process"] = {"isolated_subprocess": True,
        "policy_modules_loaded": False, "fit_seconds": fit_info["fit_seconds"],
        "generator_refit_sample_check": "exact 16-row observational frame SHA-256 match"}
    # Rewrite only the just-created evaluator artifact with process metadata.
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
                           encoding="utf-8")
    try:
        repro.verify_execution_manifest(root=ROOT,
            source_root=args.source_root, data_root=args.data_root, contract_path=args.contract,
            recommendation_path=args.lock, execution_manifest_path=args.execution_manifest,
            expected_manifest_sha256=args.execution_manifest_sha256,
            code_names=list(contract["code_sha256"]), invocation=invocation)
    except Exception:
        quarantine = args.output.with_name(args.output.name + f".quarantine-{int(time.time())}")
        if args.output.exists() and not quarantine.exists(): os.replace(args.output, quarantine)
        raise
    print(json.dumps({"status": "PASS", "total_intervention_rows": result["total_intervention_rows"],
                      "sampling_seconds": result["sampling_seconds"],
                      "recommendation_lock_sha256": result["recommendation_lock_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
