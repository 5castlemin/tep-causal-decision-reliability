"""Bounded causalAssembly adapter qualification; never computes outcomes summaries."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_COMMIT = "8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9"
EXPECTED_HASHES = {
    "assembly_reference--ground_truth.json": "86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8",
    "assembly_sample--assembly_line_500.csv": "afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e",
}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DevelopmentConditional:
    """Tiny integer-support development mechanism for upstream parity only."""

    def __init__(self):
        self.seen_parent_columns: list[list[str]] = []

    def produce_sample(self, newdata, random_state, n=1):
        self.seen_parent_columns.append(list(newdata.columns))
        if list(newdata.columns) != ["Dev_X"]:
            raise AssertionError("upstream/adapter parent order mismatch")
        return newdata["Dev_X"].to_numpy() + random_state.normal(0.0, 0.05, len(newdata))


def mechanism_state_snapshot(mechanism, np):
    """Capture fitted training inputs and native fitted-object identity."""
    if hasattr(mechanism, "dataset"):
        return {
            "kind": "kde",
            "dataset": np.array(mechanism.dataset, copy=True),
            "covariance": np.array(mechanism.covariance, copy=True),
        }
    if hasattr(mechanism, "X_train") and hasattr(mechanism, "Y_train"):
        return {
            "kind": "drf",
            "X_train": mechanism.X_train.copy(deep=True),
            "Y_train": mechanism.Y_train.copy(deep=True),
            "fit_params": dict(mechanism.fit_params),
            "r_fit_object_id": id(mechanism.r_fit_object),
        }
    raise TypeError(f"unrecognized pinned fitted mechanism type: {type(mechanism)!r}")


def mechanism_state_unchanged(mechanism, snapshot, np, pd) -> bool:
    if snapshot["kind"] == "kde":
        return np.array_equal(mechanism.dataset, snapshot["dataset"]) and np.array_equal(
            mechanism.covariance, snapshot["covariance"]
        )
    return (
        mechanism.X_train.equals(snapshot["X_train"])
        and mechanism.Y_train.equals(snapshot["Y_train"])
        and mechanism.fit_params == snapshot["fit_params"]
        and id(mechanism.r_fit_object) == snapshot["r_fit_object_id"]
    )


def qualify_upstream_integer_parity(np, nx, models_dag, gaussian_kde, sample_hard_do, seed: int) -> dict:
    """Compare pinned upstream hard-int behavior on an in-support dev fixture."""
    raw = nx.DiGraph()
    raw.add_nodes_from(["X", "Y"])
    raw.add_edge("X", "Y")
    upstream_model = models_dag.ProductionLineGraph.from_nx(
        raw, cell_mapper={"Dev": ["X", "Y"]}
    )
    adapter_model = models_dag.ProductionLineGraph.from_nx(
        raw, cell_mapper={"Dev": ["X", "Y"]}
    )
    x_node, y_node = "Dev_X", "Dev_Y"
    shared_mechanisms = {
        x_node: gaussian_kde(np.array([0.0, 1.0, 2.0, 3.0])),
        y_node: DevelopmentConditional(),
    }
    upstream_model.drf = dict(shared_mechanisms)
    adapter_model.drf = dict(shared_mechanisms)
    upstream_model.random_state = np.random.default_rng(seed)
    upstream_model.intervene_on({x_node: 1})
    upstream_result = upstream_model.sample_from_interventional_drf(size=5, smoothed=True)
    adapter_result = sample_hard_do(
        adapter_model, x_node, 1, size=5, rng=np.random.default_rng(seed), smoothed=True
    )
    pd_equal = upstream_result.equals(adapter_result)
    if not pd_equal:
        raise AssertionError("adapter does not match upstream integer hard-do output")
    if upstream_model.interventional_amat(0).loc[x_node, y_node] != 1:
        raise AssertionError("upstream intervention incorrectly removed outgoing edge")
    if set(upstream_model.interventional_amat(0).loc[:, x_node].to_numpy()) != {0}:
        raise AssertionError("upstream intervention retained incoming edge")
    return {
        "status": "PASS",
        "action": "in-support integer 1 on isolated synthetic development fixture",
        "same_dag_and_fitted_mechanism": True,
        "sample_size": 5,
        "smoothed": True,
        "same_rng_initial_state": True,
        "exact_dataframe_equality": True,
        "parent_order_checked": [x_node],
    }


def run(source_root: Path, data_root: Path, seed: int = 2718, rows: int = 2) -> dict:
    source_root, data_root = source_root.resolve(), data_root.resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"expected pinned causalAssembly commit {EXPECTED_COMMIT}; got {commit}")
    hashes = {name: file_hash(data_root / name) for name in EXPECTED_HASHES}
    if hashes != EXPECTED_HASHES:
        raise ValueError("pinned source data hash mismatch")

    import networkx as nx
    import numpy as np
    import pandas as pd
    from rpy2.robjects import r
    from rpy2.robjects.packages import isinstalled
    from scipy.stats import gaussian_kde

    if not isinstalled("drf"):
        raise RuntimeError("isolated R library must provide package drf")
    sys.path.insert(0, str(source_root))
    repository_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repository_root))
    from causalAssembly import models_dag
    from causalAssembly.drf_fitting import fit_drf

    from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import (
        sample_hard_do,
    )

    integer_parity = qualify_upstream_integer_parity(
        np, nx, models_dag, gaussian_kde, sample_hard_do, seed
    )

    # Route pinned API loaders to previously hash-verified files, never mutable main.
    class LocalResponse:
        def __init__(self, text):
            self.text = text

    original_get = models_dag.requests.get
    original_dataset_url = models_dag.DATA_DATASET
    gt_path = data_root / "assembly_reference--ground_truth.json"
    data_path = data_root / "assembly_sample--assembly_line_500.csv"
    models_dag.requests.get = lambda _url, timeout=5: LocalResponse(
        gt_path.read_text(encoding="utf-8")
    )
    models_dag.DATA_DATASET = str(data_path)
    try:
        full_graph = models_dag.ProductionLineGraph.get_ground_truth()
        data = models_dag.ProductionLineGraph.get_data()
    finally:
        models_dag.requests.get = original_get
        models_dag.DATA_DATASET = original_dataset_url

    station = full_graph.Station1
    station_nodes = list(station.nodes)
    stripped = nx.relabel_nodes(
        station.graph, {name: name.removeprefix("Station1_") for name in station_nodes}, copy=True
    )
    model = models_dag.ProductionLineGraph.from_nx(
        stripped, cell_mapper={"Station1": list(stripped.nodes)}
    )
    if set(model.nodes) != set(station_nodes) or set(model.graph.edges) != set(station.graph.edges):
        raise ValueError("station wrapper changed official graph")
    train = data[station_nodes]
    r(f"set.seed({seed})")
    fit_started = time.perf_counter()
    model.drf = fit_drf(model, train)
    fit_seconds = round(time.perf_counter() - fit_started, 3)
    mechanism_ids = {name: id(mechanism) for name, mechanism in model.drf.items()}
    mechanism_snapshots = {
        name: mechanism_state_snapshot(mechanism, np) for name, mechanism in model.drf.items()
    }
    original_edges = set(model.graph.edges)
    original_nodes = list(model.nodes)

    # Development-only node avoids the predeclared task's action and target.
    intervention_node = "Station1_mp_2"
    intervention_value = float(train[intervention_node].median())
    maximum_rows = 4  # two rows, repeated once from the same fixed seed
    if rows != 2:
        raise ValueError("qualification is fixed at two rows per draw")
    started = time.perf_counter()
    first = sample_hard_do(
        model, intervention_node, intervention_value, size=rows,
        rng=np.random.default_rng(seed), smoothed=True,
    )
    second = sample_hard_do(
        model, intervention_node, intervention_value, size=rows,
        rng=np.random.default_rng(seed), smoothed=True,
    )
    sampling_seconds = round(time.perf_counter() - started, 3)
    if len(first) + len(second) > maximum_rows:
        raise RuntimeError("smoke sample cap exceeded")
    if list(first.columns) != original_nodes or not first.equals(second):
        raise AssertionError("schema/order or same-seed reproducibility failed")
    if not np.all(first[intervention_node].to_numpy() == intervention_value):
        raise AssertionError("intervention value not fixed exactly")
    if not np.isfinite(first.to_numpy(dtype=float)).all():
        raise AssertionError("interventional sample contains nonfinite values")
    if set(model.graph.edges) != original_edges or list(model.nodes) != original_nodes:
        raise AssertionError("adapter mutated the original graph")
    if {name: id(mechanism) for name, mechanism in model.drf.items()} != mechanism_ids:
        raise AssertionError("adapter replaced or mutated fitted mechanism mapping")
    if not all(
        mechanism_state_unchanged(model.drf[name], mechanism_snapshots[name], np, pd)
        for name in model.drf
    ):
        raise AssertionError("adapter changed fitted training inputs or native fitted object")
    if model.mutilated_dags or model.interventional_drf:
        raise AssertionError("adapter leaked intervention state into upstream model")

    return {
        "pinned_commit": commit,
        "package_version": "1.2.1",
        "data_sha256": hashes,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "networkx": nx.__version__,
        "R": str(r("as.character(getRversion())")[0]),
        "R_drf": str(r('as.character(packageVersion("drf"))')[0]),
        "seed": seed,
        "integer_upstream_compatibility": integer_parity,
        "station1_float_smoke": {
            "node": intervention_node,
            "value_source": "predeclared training-only median; value not emitted",
            "rows_per_draw": rows,
            "total_generated_rows": len(first) + len(second),
            "maximum_generated_rows": maximum_rows,
            "fit_seconds": fit_seconds,
            "two_draw_sampling_seconds": sampling_seconds,
            "adapter_execution": "PASS",
            "exact_constant_applied": True,
            "all_values_finite": True,
            "node_and_column_order_preserved": True,
            "same_seed_reproducible": True,
            "original_graph_preserved": True,
            "fitted_mechanism_identities_preserved": True,
            "fitted_training_data_and_native_fit_state_preserved": True,
            "intervention_state_leaked": False,
            "response_values_or_summaries_emitted": False,
        },
        "exposure": {
            "station1_smoke_rows_generated": len(first) + len(second),
            "exploratory_and_discarded": True,
            "reuse_as_development_or_evaluation_data": False,
            "policy_or_regret_computed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=2718)
    parser.add_argument("--rows", type=int, default=2)
    args = parser.parse_args()
    result = run(args.source_root, args.data_root, args.seed, args.rows)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
