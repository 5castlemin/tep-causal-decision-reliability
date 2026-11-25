"""Evaluator-only child process; does not import recommendation or policy code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from research.external_validation.semisynthetic_evaluation.pipeline import (
    evaluate_locked, load_fit_station1, verify_sources,
)


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
    args = parser.parse_args(argv)
    verify_sources(args.source_root, args.data_root)
    # No policy engine, learner, G0 generator, or recommendation module is
    # imported in this process. It reads a hash-verified locked manifest only.
    if any(name.startswith("research.original_objective") for name in sys.modules):
        raise RuntimeError("recommendation/policy module unexpectedly loaded in evaluator")
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
        rows_per_action=args.rows)
    result["evaluator_process"] = {"isolated_subprocess": True,
        "policy_modules_loaded": False, "fit_seconds": fit_info["fit_seconds"],
        "generator_refit_sample_check": "exact 16-row observational frame SHA-256 match"}
    # Rewrite only the just-created evaluator artifact with process metadata.
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": "PASS", "total_intervention_rows": result["total_intervention_rows"],
                      "sampling_seconds": result["sampling_seconds"],
                      "recommendation_lock_sha256": result["recommendation_lock_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
