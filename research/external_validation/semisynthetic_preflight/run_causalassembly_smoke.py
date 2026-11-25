"""Bounded API smoke test for a pinned causalAssembly checkout.

This script deliberately emits metadata and pass/fail checks only. The small
generated response samples are exploratory exposure and must not be reused as
evaluation data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_COMMIT = "8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9"
EXPECTED_HASHES = {
    "assembly_reference--ground_truth.json": "86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8",
    "assembly_sample--assembly_line_500.csv": "afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(source_root: Path, data_root: Path, smoke_rows: int = 4, seed: int = 2031) -> dict:
    source_root = source_root.resolve()
    data_root = data_root.resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"Expected pinned causalAssembly commit {EXPECTED_COMMIT}, got {commit}")

    for relative, expected_hash in EXPECTED_HASHES.items():
        actual = sha256(data_root / relative)
        if actual != expected_hash:
            raise ValueError(f"Hash mismatch for pinned source file: {relative}")

    # Keep CRAN additions inside the separate Python preflight environment.
    os.environ.setdefault("R_LIBS_USER", str(Path(sys.prefix) / "R-library"))
    import numpy as np
    import networkx as nx
    import pandas as pd
    from rpy2.robjects import r
    from rpy2.robjects.packages import isinstalled

    if not isinstalled("drf"):
        raise RuntimeError("R package 'drf' must be installed in the isolated R_LIBS_USER")

    sys.path.insert(0, str(source_root))
    from causalAssembly import models_dag
    from causalAssembly.drf_fitting import fit_drf

    class LocalResponse:
        def __init__(self, text: str):
            self.text = text

    # The upstream methods default to mutable main-branch URLs. Point those
    # calls at the already-pinned local checkout instead of downloading main.
    gt_path = data_root / "assembly_reference--ground_truth.json"
    data_path = data_root / "assembly_sample--assembly_line_500.csv"
    original_get = models_dag.requests.get
    original_dataset_url = models_dag.DATA_DATASET
    models_dag.requests.get = lambda _url, timeout=5: LocalResponse(gt_path.read_text(encoding="utf-8"))
    models_dag.DATA_DATASET = str(data_path)
    try:
        graph = models_dag.ProductionLineGraph.get_ground_truth()
        data = models_dag.ProductionLineGraph.get_data()
    finally:
        models_dag.requests.get = original_get
        models_dag.DATA_DATASET = original_dataset_url

    if not nx.is_directed_acyclic_graph(graph.graph):
        raise ValueError("Official graph loader returned a cyclic graph")
    if set(graph.nodes) != set(data.columns):
        raise ValueError("Pinned graph and data columns differ")

    station = graph.Station1
    station_graph = station.graph.copy()
    station_node_names = list(station.nodes)
    if any(
        parent not in station_node_names
        for node in station_node_names
        for parent in graph.graph.predecessors(node)
    ):
        raise ValueError("Station1 has external parents; station-only model would omit causes")

    # Build the official Station1 component as a ProductionLineGraph so the
    # package's intervention API is available. This is a named official cell,
    # not an arbitrary induced projection.
    stripped = nx.relabel_nodes(
        station_graph,
        {node: node.removeprefix("Station1_") for node in station_graph.nodes},
        copy=True,
    )
    model = models_dag.ProductionLineGraph.from_nx(
        stripped, cell_mapper={"Station1": list(stripped.nodes)}
    )
    if set(model.nodes) != set(station_node_names) or set(model.graph.edges) != set(station_graph.edges):
        raise ValueError("Station1 adapter changed the official node or edge set")

    action = "Station1_mp_0"
    target = "Station1_mp_4"
    if model.graph.has_edge(action, target) or not nx.has_path(model.graph, action, target):
        raise ValueError("Predeclared strict indirect task is not present in Station1")
    task_path = nx.shortest_path(model.graph, action, target)

    training = data[station_node_names]
    if training.isna().any().any():
        raise ValueError("Station1 training input contains missing values")

    r("set.seed(" + str(seed) + ")")
    fit_started = time.perf_counter()
    model.drf = fit_drf(model, data=training)
    fit_seconds = round(time.perf_counter() - fit_started, 3)
    if set(model.drf) != set(model.nodes):
        raise ValueError("fit_drf did not return one model per Station1 node")

    model.random_state = np.random.default_rng(seed)
    obs_first = model.sample_from_drf(size=smoke_rows)
    model.random_state = np.random.default_rng(seed)
    obs_repeat = model.sample_from_drf(size=smoke_rows)
    sampling_reproducible = bool(obs_first.equals(obs_repeat))

    # Use a training-only in-support floating value. The API accepts it in
    # intervene_on(), but the pinned sampler currently rejects numeric floats.
    action_value = float(training[action].median())
    model.intervene_on(nodes_values={action: action_value})
    intervention_stored = len(model.interventional_drf) == 1
    float_do_status = "supported"
    try:
        interventional = model.sample_from_interventional_drf(size=smoke_rows)
        applied = bool(np.all(interventional[action].to_numpy() == action_value))
        if not applied:
            raise AssertionError("Intervention value was not set on every generated row")
        interventional_rows = int(len(interventional))
    except NotImplementedError as exc:
        float_do_status = "unsupported"
        interventional_rows = 0
        intervention_error = str(exc)
    else:
        intervention_error = None

    fresh = models_dag.ProductionLineGraph.from_nx(
        stripped, cell_mapper={"Station1": list(stripped.nodes)}
    )
    fresh_state_empty = not fresh.mutilated_dags and not fresh.interventional_drf

    return {
        "pinned_commit": commit,
        "source_hashes_verified": True,
        "python": sys.version.split()[0],
        "package_version": "1.2.1",
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "networkx": nx.__version__,
        "scipy": __import__("scipy").__version__,
        "R_version": str(r("as.character(getRversion())")[0]),
        "R_drf_version": str(r('as.character(packageVersion("drf"))')[0]),
        "fit_seed": seed,
        "sampling_seed": seed,
        "fit_seconds_station1": fit_seconds,
        "full_graph": {
            "nodes": len(graph.nodes),
            "edges": graph.graph.number_of_edges(),
            "dag": nx.is_directed_acyclic_graph(graph.graph),
            "data_rows": int(len(data)),
            "data_columns": int(len(data.columns)),
            "missing_values": int(data.isna().sum().sum()),
        },
        "station1": {
            "nodes": len(model.nodes),
            "edges": model.graph.number_of_edges(),
            "external_parents": False,
            "task_candidate": {"action": action, "target": target, "path": task_path},
            "action_support": {
                "unique": int(training[action].nunique()),
                "minimum": float(training[action].min()),
                "maximum": float(training[action].max()),
                "training_quantiles_10_30_50_70_90": [
                    float(value) for value in training[action].quantile([.1, .3, .5, .7, .9])
                ],
            },
            "fit_drf_models": len(model.drf),
        },
        "observational_sample": {
            "rows_per_repeat": smoke_rows,
            "finite": bool(np.isfinite(obs_first.to_numpy()).all()),
            "same_model_same_seed_reproducible": sampling_reproducible,
            "target_response_values_generated": True,
            "target_response_summary_calculated": False,
        },
        "float_hard_intervention": {
            "intervene_on_accepts_value": intervention_stored,
            "sample_generation_status": float_do_status,
            "rows_returned": interventional_rows,
            "error": intervention_error,
        },
        "fresh_object_resets_intervention_state": fresh_state_empty,
        "evaluation_or_policy_performance_run": False,
        "loss_or_regret_calculated": False,
        "physical_machine_controlled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--smoke-rows", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2031)
    args = parser.parse_args()
    if args.smoke_rows < 1:
        parser.error("--smoke-rows must be positive")
    print(json.dumps(run(args.source_root, args.data_root, args.smoke_rows, args.seed), indent=2))


if __name__ == "__main__":
    main()
