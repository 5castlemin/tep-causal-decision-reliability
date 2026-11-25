"""Small, disposable R/DRF timing probe; emits no response summaries."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_evaluation.pipeline import (
    _validate_frame, load_fit_station1, verify_sources,
)
from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import sample_hard_do


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--seed", type=int, default=91420901)
    args = parser.parse_args()
    if not 1 <= args.rows <= 16:
        parser.error("disposable performance smoke is capped at 16 rows")
    verify_sources(args.source_root, args.data_root)
    model, source, info = load_fit_station1(args.source_root, args.data_root, 91420261)
    action = float(np.quantile(source["Station1_mp_0"].to_numpy(), 0.5, method="linear"))
    started = time.perf_counter()
    sample = sample_hard_do(model, "Station1_mp_0", action, size=args.rows,
                            rng=np.random.default_rng(args.seed), smoothed=True)
    values = _validate_frame(sample, list(model.nodes), args.rows)
    elapsed = time.perf_counter() - started
    del sample, values, model, source
    print(json.dumps({"status": "DISPOSABLE_SMOKE_COMPLETED", "rows": args.rows,
        "finite_schema_pass": True, "exact_action_pass": True,
        "sampling_seconds": round(elapsed, 3), "fit_seconds": round(info["fit_seconds"], 3),
        "response_values_emitted": False, "samples_reusable": False,
        "action_rule": "pinned source median; numeric value omitted"}, sort_keys=True))


if __name__ == "__main__":
    main()
