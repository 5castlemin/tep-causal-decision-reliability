"""Validate Step 1 qualification metadata without reading response values."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent


def dyad_counts(node_count: int, edge_count: int) -> tuple[int, int, int]:
    """Return total unordered pairs, nonedges, and oriented nonedge proposals."""
    pairs = node_count * (node_count - 1) // 2
    nonedges = pairs - edge_count
    return pairs, nonedges, 2 * nonedges


def validate() -> dict:
    inspection = json.loads((AUDIT / "inspection_results.json").read_text(encoding="utf-8"))
    summary = json.loads((HERE / "qualification_summary.json").read_text(encoding="utf-8"))
    graph = inspection["mk2_figure_transcription"]
    if graph["node_count"] != 90 or graph["edge_count"] != 142 or not graph["dag"]:
        raise ValueError("Unexpected Mk2 graph metadata")
    if len(set(graph["nodes"])) != graph["node_count"] or len(graph["edges"]) != graph["edge_count"]:
        raise ValueError("Graph node/edge count mismatch")

    pair_total, nonedges, oriented = dyad_counts(graph["node_count"], graph["edge_count"])
    if (pair_total, nonedges, oriented) != (4005, 3863, 7726):
        raise ValueError("Unexpected unordered/oriented nonedge counts")
    experiments = inspection["chamber"]["lt_spice_v1"]["experiments"]
    expected_constants = (67, 59, 31, 8)
    for experiment_name in ("exp_1_low_noise", "exp_2_noisy"):
        experiment = experiments[experiment_name]
        constants = set(experiment["constant_columns"])
        nodes = set(graph["nodes"])
        observed = (len(constants), len(constants & nodes), len(nodes - constants), len(constants - nodes))
        if observed != expected_constants:
            raise ValueError(f"Constant-column/node counts mismatch for {experiment_name}: {observed}")

    recorded = summary["primary_csvs"]
    if (recorded["constant_columns_each"], recorded["constant_reference_nodes_each"],
            recorded["variable_reference_nodes_each"], recorded["constant_non_graph_columns_each"]) != expected_constants:
        raise ValueError("Qualification summary disagrees with Step 0 inspection")
    return {
        "status": "PASS",
        "graph_nodes": graph["node_count"],
        "graph_edges": graph["edge_count"],
        "unordered_pairs": pair_total,
        "unordered_nonedges": nonedges,
        "oriented_fp_candidates": oriented,
        "constant_column_graph_overlap": expected_constants,
        "response_values_read": False,
    }


def verify_dataset(path: Path) -> dict:
    manifest = json.loads((AUDIT / "dataset_manifest.json").read_text(encoding="utf-8"))
    entry = manifest["datasets"]["lt_spice_v1"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    if digest != entry["sha256"] or path.stat().st_size != entry["bytes"]:
        raise ValueError("lt_spice_v1 bytes/hash disagree with Step 0 manifest")
    return {"sha256": digest, "bytes": path.stat().st_size, "zip_members": len(names), "manifest_match": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-zip", type=Path, help="Optional existing local lt_spice_v1.zip")
    args = parser.parse_args()
    result = {"metadata_validation": validate()}
    if args.dataset_zip:
        result["dataset_integrity"] = verify_dataset(args.dataset_zip)
    print(json.dumps(result, indent=2))
