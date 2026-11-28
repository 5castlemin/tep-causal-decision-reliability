"""Outcome-blind inspection of the archived random_loads_intake assignment blocks.

Only metadata/assignment columns are loaded. No response column is selected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

MEMBER = "wt_bernoulli_v1/random_loads_intake.csv"
USECOLS = ["timestamp", "config", "counter", "flag", "intervention", "load_in", "load_out", "hatch"]
EXPECTED_SHA256 = "e5d58a67f6307b9099177425e91c449b9e62e7c712f8c6f34d1dc80ce4db01e3"


def inspect_frame(frame: pd.DataFrame) -> dict:
    missing = set(USECOLS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing allowlisted columns: {sorted(missing)}")
    if len(frame) == 0:
        raise ValueError("Empty assignment archive")
    if not frame["timestamp"].is_monotonic_increasing or frame["timestamp"].duplicated().any():
        raise ValueError("Timestamp must be unique and increasing")
    grouped = frame.groupby("flag", sort=False, dropna=False)
    sizes = grouped.size()
    levels = grouped["load_in"].nunique(dropna=False)
    if (sizes != 100).any() or (levels != 1).any():
        raise ValueError("Every flag block must contain 100 rows with one assignment")
    block_loads = grouped["load_in"].first().astype(float).to_numpy()
    block_flags = grouped.size().index.to_numpy(dtype=float)
    flag_sequence_matches = bool(
        len(block_flags) == 2000 and np.array_equal(block_flags, np.arange(2000, dtype=float))
    )
    intervention_pattern_matches = True
    for _, rows in grouped:
        marker = rows["intervention"].to_numpy()
        if len(marker) != 100 or marker[0] != 1 or not np.all(marker[1:] == 0):
            intervention_pattern_matches = False
            break
    if len(block_loads) == 2000:
        rng = np.random.default_rng(42)
        expected = np.array([round(rng.uniform(0, 1), 2) for _ in block_loads])
        # The CSV stores numeric values with float32-style decimal expansion;
        # compare the protocol's recorded two-decimal assignments.
        rng_match_count = int((np.round(block_loads, 2) == expected).sum())
    else:
        rng_match_count = None
    gaps = frame["timestamp"].diff().dropna()
    boundaries = frame["flag"].ne(frame["flag"].shift()).to_numpy()[1:]
    boundary_gaps = gaps.to_numpy()[boundaries]
    arm_counts = {
        f"{arm:.2f}": int((np.round(block_loads, 2) == arm).sum())
        for arm in (0.10, 0.30, 0.50, 0.70, 0.90)
    }
    return {
        "rows": int(len(frame)), "columns_loaded": list(USECOLS),
        "blocks": int(len(sizes)), "block_size_min": int(sizes.min()),
        "block_size_max": int(sizes.max()), "inconsistent_assignment_blocks": int((levels != 1).sum()),
        "flag_sequence_matches_0_to_1999": flag_sequence_matches,
        "intervention_first_row_only_each_block": intervention_pattern_matches,
        "rng_seed_42_matching_blocks": rng_match_count,
        "candidate_arm_block_counts": arm_counts,
        "config_counts": {str(k): int(v) for k, v in frame["config"].value_counts(dropna=False).items()},
        "load_out_unique": sorted(float(x) for x in frame["load_out"].dropna().unique()),
        "hatch_unique": sorted(float(x) for x in frame["hatch"].dropna().unique()),
        "intervention_counts": {str(k): int(v) for k, v in frame["intervention"].value_counts(dropna=False).items()},
        "counter_unique": int(frame["counter"].nunique(dropna=False)),
        "timestamp_gap_seconds": {
            "median": float(gaps.median()), "p99": float(gaps.quantile(.99)), "max": float(gaps.max()),
            "block_boundary_min": float(boundary_gaps.min()), "block_boundary_max": float(boundary_gaps.max()),
        },
        "response_values_read": False,
    }


def inspect_archive(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Archive hash does not match the Step 0 manifest")
    with zipfile.ZipFile(path) as archive, archive.open(MEMBER) as source:
        frame = pd.read_csv(source, usecols=USECOLS)
    summary = inspect_frame(frame)
    summary.update({"archive_bytes": path.stat().st_size, "archive_sha256": digest, "manifest_match": True})
    if (summary["rows"] != 200000 or summary["blocks"] != 2000
            or summary["rng_seed_42_matching_blocks"] != 2000
            or not summary["flag_sequence_matches_0_to_1999"]
            or not summary["intervention_first_row_only_each_block"]):
        raise ValueError("Archive does not match the pinned assignment protocol")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path, help="Existing wt_bernoulli_v1.zip")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    result = inspect_archive(args.archive)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
