"""Regenerate locked Development G0 audit rows from fixed seeds only (outcome-blind)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.external_validation.semisynthetic_evaluation.pipeline import (
    file_sha256, make_g0, reconstruct_g0, sha256_bytes, canonical_json, TASK_X, TASK_Y,
)
from research.original_objective import policy_engine as pe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--structural", type=Path, required=True)
    parser.add_argument("--run-lock", type=Path, required=True)
    parser.add_argument("--recommendations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError("refusing to overwrite G0 manifest")
    structural = json.loads(args.structural.read_text(encoding="utf-8"))
    run_lock = json.loads(args.run_lock.read_text(encoding="utf-8"))
    recs = json.loads(args.recommendations.read_text(encoding="utf-8"))
    nodes = structural["official_graph"]["nodes"]
    truth = {pe.pair(a, b): (a, b) for a, b in structural["official_graph"]["edges"]}
    if pe.graph_hash(truth) != run_lock["graph_sha256"]:
        raise ValueError("reference graph differs from locked run")
    locked_seed_ids = run_lock["g0"]["seed_ids"]
    expected_hashes = {}
    for row in recs["recommendations"]:
        expected_hashes[row["g0_seed_id"]] = row["g0_graph_sha256"]
    entries = []
    for seed_id in locked_seed_ids:
        record = make_g0(truth, nodes, seed_id)
        g0 = reconstruct_g0(record, truth)
        graph_hash = pe.graph_hash(g0)
        if graph_hash != expected_hashes.get(seed_id):
            raise ValueError(f"fixed-seed G0 mismatch for {seed_id}")
        stats = pe.metrics(truth, g0, TASK_X, TASK_Y, pe.Config(fp_rule="A"))
        entries.append({"seed_id": seed_id, "master_seed": record["research_d_master_seed"],
            "initial_graph_sha256": graph_hash, "initial_graph": record["initial_graph"],
            "task_zone_pairs": record["task_zone_pairs"], "task_zone_nodes": record["task_zone_nodes"],
            "proposal_summary": record["summary"], "attempted_events": record["attempted_events"],
            "event_opportunities_by_metric_kind_and_zone": record["event_opportunities_by_metric_kind_and_zone"],
            "realized_error_counts_by_metric": stats["counts"], "support": stats["support"],
            "task_off_task_error_counts": record["realized_error_counts_by_kind_and_zone"]})
    body = {"schema": "RESEARCH_D_DEVELOPMENT_G0_MANIFEST_V1", "outcome_blind_regeneration": True,
        "run_lock_sha256": file_sha256(args.run_lock), "recommendation_lock_sha256": recs["content_sha256"],
        "reference_graph_sha256": pe.graph_hash(truth), "g0_count": len(entries), "g0": entries,
        "response_values_used": False, "seed_replacement": False}
    body["content_sha256"] = sha256_bytes(canonical_json(body))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "g0_count": len(entries), "content_sha256": body["content_sha256"]}))


if __name__ == "__main__":
    main()
