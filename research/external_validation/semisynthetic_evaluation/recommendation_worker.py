"""Recommendation-only worker; receives train rows and graphs, never a DRF."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.original_objective import policy_engine as pe


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--training-sha256", required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists(): raise FileExistsError("refusing to overwrite recommendation output")
    if d.file_sha256(args.input) != args.input_sha256:
        raise ValueError("recommendation input raw-byte hash mismatch")
    if d.file_sha256(args.training) != args.training_sha256:
        raise ValueError("learner training CSV raw-byte hash mismatch")
    request = json.loads(args.input.read_text(encoding="utf-8"))
    train = pd.read_csv(args.training)
    nodes = request["nodes"]
    values = d._validate_frame(train, nodes, 512)
    train = pd.DataFrame(values, columns=nodes)
    numeric_hash = hashlib.sha256(train.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    if numeric_hash != request["training_numeric_sha256"]:
        raise ValueError("recommendation training numeric digest mismatch")
    truth = {pe.pair(a, b): (a, b) for a, b in request["reference_edges"]}
    if not pe.dag(truth) or list(request["actions"]) != sorted(set(request["actions"])):
        raise ValueError("recommendation reference/action input invalid")
    rows = []
    for item in request["g0"]:
        graph = d.reconstruct_g0(item["record"], truth)
        if pe.graph_hash(graph) != item["graph_sha256"]:
            raise ValueError("G0 reconstruction mismatch in recommendation worker")
        rows.append({"seed_id": item["seed_id"], "record": item["record"], "g0": graph})
    manifest, digest = d.lock_recommendations(train, numeric_hash, truth, nodes,
        request["actions"], rows, args.output, contract_sha256=args.contract_sha256)
    print(json.dumps({"status": "PASS", "recommendation_rows": manifest["row_count"],
        "content_sha256": digest, "training_numeric_sha256": numeric_hash}, sort_keys=True))


if __name__ == "__main__":
    main()
