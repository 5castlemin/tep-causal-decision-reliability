"""Research D-specific Station1 pipeline. Never called from the Research C runner."""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = Path(__file__).with_name("development_contract.json")
EXPECTED_COMMIT = "8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9"
DATA_HASHES = {
    "assembly_reference--ground_truth.json": "86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8",
    "assembly_sample--assembly_line_500.csv": "afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e",
}
TASK_X, TASK_Y = "Station1_mp_0", "Station1_mp_4"
POLICY_IDS = ("S0", "M1", "M2", "M3", "M4", "M1+M2", "M1+M3", "M1+M4",
    "M2+M3", "M2+M4", "M3+M4", "M1+M2+M3", "M1+M2+M4", "M1+M3+M4",
    "M2+M3+M4", "M1+M2+M3+M4", "CANONICAL_ORACLE")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_sources(source_root: Path, data_root: Path) -> dict:
    source_root, data_root = source_root.resolve(), data_root.resolve()
    commit = subprocess.check_output(["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True).strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"pinned causalAssembly commit mismatch: {commit}")
    hashes = {name: file_sha256(data_root / name) for name in DATA_HASHES}
    if hashes != DATA_HASHES:
        raise ValueError("pinned causalAssembly data SHA-256 mismatch")
    return {"source_commit": commit, "package_version": "1.2.1", "data_sha256": hashes}


def load_fit_station1(source_root: Path, data_root: Path, fit_seed: int):
    """Load pinned official graph/data and fit one official causalAssembly DRF."""
    verify_sources(source_root, data_root)
    from rpy2.robjects import r
    from rpy2.robjects.packages import isinstalled
    if not isinstalled("drf"):
        raise RuntimeError("isolated R library does not contain package drf")
    sys.path.insert(0, str(source_root.resolve()))
    from causalAssembly import models_dag
    from causalAssembly.drf_fitting import fit_drf

    class LocalResponse:
        def __init__(self, text: str): self.text = text

    gt_path = data_root.resolve() / "assembly_reference--ground_truth.json"
    data_path = data_root.resolve() / "assembly_sample--assembly_line_500.csv"
    old_get, old_url = models_dag.requests.get, models_dag.DATA_DATASET
    models_dag.requests.get = lambda _url, timeout=5: LocalResponse(gt_path.read_text(encoding="utf-8"))
    models_dag.DATA_DATASET = str(data_path)
    try:
        full = models_dag.ProductionLineGraph.get_ground_truth()
        data = models_dag.ProductionLineGraph.get_data()
    finally:
        models_dag.requests.get, models_dag.DATA_DATASET = old_get, old_url
    if not nx.is_directed_acyclic_graph(full.graph) or set(full.nodes) != set(data.columns):
        raise ValueError("official graph/data mismatch or non-DAG")
    station = full.Station1
    names = list(station.nodes)
    if any(parent not in names for node in names for parent in full.graph.predecessors(node)):
        raise ValueError("Station1 has external parents; standalone station fit is invalid")
    station_graph = nx.relabel_nodes(station.graph,
        {node: node.removeprefix("Station1_") for node in station.graph.nodes}, copy=True)
    model = models_dag.ProductionLineGraph.from_nx(station_graph,
        cell_mapper={"Station1": list(station_graph.nodes)})
    if set(model.nodes) != set(names) or set(model.graph.edges) != set(station.graph.edges):
        raise ValueError("Station1 official graph changed during loader mapping")
    if model.graph.has_edge(TASK_X, TASK_Y) or not nx.has_path(model.graph, TASK_X, TASK_Y):
        raise ValueError("locked strict indirect task is absent")
    source = data.loc[:, names].copy()
    if list(source.columns) != names or source.isna().any().any():
        raise ValueError("invalid Station1 fit source schema or missing values")
    r(f"set.seed({int(fit_seed)})")
    started = time.perf_counter()
    model.drf = fit_drf(model, data=source)
    fit_seconds = time.perf_counter() - started
    if set(model.drf) != set(model.nodes):
        raise ValueError("fit_drf omitted Station1 mechanism(s)")
    fitted_parent_orders = {}
    for node in model.nodes:
        parents = list(model.parents(of_node=node))
        mechanism = model.drf[node]
        if parents:
            x_train = getattr(mechanism, "X_train", None)
            columns = list(getattr(x_train, "columns", ()))
            if columns != parents:
                raise ValueError(f"fitted X_train columns do not match sampler parent order for {node}")
            fitted_parent_orders[node] = columns
        else:
            if not (hasattr(mechanism, "resample") and hasattr(mechanism, "dataset")):
                raise ValueError(f"root node {node} has no compatible fitted root mechanism")
            fitted_parent_orders[node] = []
    return model, source, {"fit_seconds": fit_seconds, "nodes": names,
                           "edges": sorted(map(list, model.graph.edges)),
                           "graph_sha256": sha256_bytes(canonical_json(sorted(map(list, model.graph.edges)))),
                           "fitted_parent_column_orders": fitted_parent_orders}


def _validate_frame(frame, names, expected_rows):
    import pandas as pd
    if not isinstance(frame, pd.DataFrame) or list(frame.columns) != list(names):
        raise ValueError("sample schema/order mismatch")
    if frame.shape != (expected_rows, len(names)):
        raise ValueError("sample shape mismatch")
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("sample contains nonfinite values")
    return values


def action_grid(source, train, model):
    values = np.quantile(source[TASK_X].to_numpy(dtype=float), [0.1, 0.3, 0.5, 0.7, 0.9], method="linear")
    train_values = train[TASK_X].to_numpy(dtype=float)
    if (not np.isfinite(values).all() or len(np.unique(values)) != 5
            or not np.all(np.diff(values) > 0)
            or values.min() < train_values.min() or values.max() > train_values.max()):
        raise ValueError("action grid is duplicate, nonfinite, or outside learner/source marginal support")
    # Check the fitted mechanism's direct action-parent input support where the
    # node exists. This does not establish multivariate/joint conditional support.
    checked = []
    for node in nx.descendants(model.graph, TASK_X):
        mechanism = model.drf[node]
        xtrain = getattr(mechanism, "X_train", None)
        if xtrain is not None and TASK_X in list(xtrain.columns):
            lo, hi = float(xtrain[TASK_X].min()), float(xtrain[TASK_X].max())
            if values.min() < lo or values.max() > hi:
                raise ValueError(f"action grid outside fitted conditional input support for {node}")
            checked.append({"mechanism_node": node, "parent_column_order": list(xtrain.columns),
                            "action_parent_range": [lo, hi]})
    return values.astype(float).tolist(), checked


def derive_seed(label: str, value: int) -> int:
    digest = hashlib.sha256(f"research-d-external-semisynthetic-development-v1|{label}|{value}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def make_g0(truth, nodes, seed_id):
    # Reuse the frozen C corruption algorithm while deriving independent D-only
    # seed material. The generator receives no response, learner, or evaluator.
    from research.original_objective import policy_engine as pe
    from research.original_objective.g0_candidate import corrupt_graph_candidate
    master = derive_seed("g0", int(seed_id))
    result = corrupt_graph_candidate(truth, nodes=nodes, action=TASK_X, target=TASK_Y,
        master_seed=master, task_id=f"research-d-development-{seed_id}",
        true_corruption_rate=0.15, false_adjacency_rate=0.05)
    result["research_d_seed_id"] = int(seed_id)
    result["research_d_master_seed"] = master
    result["contract_status"] = "RESEARCH_D_DEVELOPMENT_V1"
    result["test_or_cohort_use"] = "bounded_development_only"
    return result


def reconstruct_g0(record, truth):
    from research.original_objective import policy_engine as pe
    current = dict(truth)
    for event in sorted(record["attempted_events"], key=lambda item: item["acceptance_order"]):
        if event["acceptance_status"] != "accepted": continue
        p = tuple(event["pair"])
        state = event["proposed_state"]
        if state == "ABSENT": current.pop(p, None)
        elif state == pe.UNRES: current[p] = pe.UNRES
        else: current[p] = tuple(state)
    if not pe.dag(current): raise ValueError("G0 reconstruction emitted cycle")
    realized = pe.metrics(truth, current, TASK_X, TASK_Y, pe.Config(fp_rule="A"))["counts"]
    if realized != record["realized_error_counts_by_metric"]:
        raise ValueError("reconstructed G0 does not match corruption record event counts")
    return current


def structural_rows(truth, nodes, seed_ids):
    rows = []
    for seed_id in seed_ids:
        record = make_g0(truth, nodes, seed_id)
        g0 = reconstruct_g0(record, truth)
        rows.append({"seed_id": seed_id, "record": record, "g0": g0})
    return rows


def structural_summary(rows, truth):
    from research.original_objective import policy_engine as pe
    from collections import Counter
    policy_ids = []
    activated = Counter()
    task_error = task_zone_error = 0
    task_any = 0
    no_error = 0
    dag_rejected = proposed = edits = 0
    for row in rows:
        record, g0 = row["record"], row["g0"]
        stats = pe.metrics(truth, g0, TASK_X, TASK_Y, pe.Config(fp_rule="A"))
        has = any(sum(stats["counts"][m].values()) for m in pe.METRICS)
        no_error += not has
        task_counts = stats["counts"]["M4"]
        has_task = any(task_counts.values())
        task_any += has_task
        task_zone_error += has_task
        task_error += sum(task_counts.values())
        for m in pe.METRICS:
            if sum(stats["counts"][m].values()): activated[m] += 1
        dag_rejected += record["summary"]["rejected_dag"]
        proposed += record["summary"]["proposed"]
        for budget in (0, 1, 2, 3, 4):
            result = pe.run_catalog(truth, g0, TASK_X, TASK_Y, budget, pe.Config(fp_rule="A"))
            for policy in result["strategies"] + [result["canonical_oracle"]]:
                edits += len(policy["edits"])
                policy_ids.append((row["seed_id"], budget, policy["policy_id"], policy["final_hash"], policy["total_cost"]))
    ids = [(s, b, p) for s, b, p, _, _ in policy_ids]
    duplicate_counts = Counter()
    by = {}
    for seed_id, budget, policy_id, graph_hash, cost in policy_ids:
        by.setdefault((seed_id, budget), []).append((policy_id, graph_hash, cost))
    for key, values in by.items():
        duplicate_counts[str(key)] = len(values) - len({x[1] for x in values})
    return {"n_g0": len(rows), "no_initial_error_count": int(no_error),
        "no_initial_error_fraction": no_error / len(rows), "task_zone_error_count": int(task_any),
        "task_zone_error_fraction": task_any / len(rows), "task_zone_error_events": task_error,
        "metric_activation_counts": dict(activated), "dag_rejected_proposals": dag_rejected,
        "proposed_events": proposed, "policy_budget_rows": len(policy_ids),
        "duplicate_final_graph_excess_count": sum(duplicate_counts.values()),
        "duplicate_final_graph_fraction_over_policy_budget_rows": sum(duplicate_counts.values()) / len(policy_ids),
        "total_structural_edits_over_policy_budget_rows": edits,
        "all_g0_rows_retained": True, "response_values_read": False}


def learner_recommendation(train, nodes, edges, actions, target, scale):
    sys.path.insert(0, str(ROOT / "src"))
    from integrated_pilot import fit_model
    from decision_mvp import static_mean_response
    train_array = train.loc[:, nodes].to_numpy(dtype=float)
    model = fit_model(train_array, list(nodes), set(edges), 1.0)
    mean_x = float(np.median(actions))
    candidates = []
    for action in actions:
        pred = float(static_mean_response(model, TASK_X, float(action))[TASK_Y])
        loss = ((pred - target) / scale) ** 2
        if not math.isfinite(pred) or not math.isfinite(loss): raise ValueError("nonfinite learner prediction")
        candidates.append({"action": float(action), "predicted_target": pred, "predicted_loss": float(loss)})
    chosen = min(candidates, key=lambda x: (x["predicted_loss"], abs(x["action"] - mean_x), x["action"]))
    return chosen["action"], candidates


def graph_free_recommendation(train, actions, target, scale):
    sys.path.insert(0, str(ROOT / "src"))
    from pilot_fit import fit_ridge
    x = train[TASK_X].to_numpy(dtype=float); y = train[TASK_Y].to_numpy(dtype=float)
    mx, sx, my, sy = map(float, (x.mean(), x.std(ddof=0), y.mean(), y.std(ddof=0)))
    if min(sx, sy) <= 0: raise ValueError("association baseline cannot fit constant variable")
    beta, intercept = fit_ridge(((x - mx) / sx)[:, None], (y - my) / sy, 1.0)
    candidates = []
    for value in actions:
        pred = float((intercept + beta[0] * ((value - mx) / sx)) * sy + my)
        loss = ((pred - target) / scale) ** 2
        candidates.append({"action": value, "predicted_target": pred, "predicted_loss": loss})
    chosen = min(candidates, key=lambda x: (x["predicted_loss"], abs(x["action"] - float(np.median(actions))), x["action"]))
    return chosen["action"], candidates


def lock_recommendations(train, train_hash, truth, nodes, actions, g0_rows, lock_path,
                         contract_path: Path = CONTRACT_PATH,
                         contract_sha256: str | None = None):
    from research.original_objective import policy_engine as pe
    if lock_path.exists(): raise FileExistsError("recommendation lock artifact already exists")
    y = train[TASK_Y].to_numpy(dtype=float)
    target = float(y.mean() + y.std(ddof=1))
    scale = float(y.std(ddof=1))
    if not math.isfinite(target) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("invalid training-only target/scale")
    baseline_action, baseline_candidates = graph_free_recommendation(train, actions, target, scale)
    rows, learner_cache = [], {}
    config = pe.Config(fp_rule="A", normalization="fixed_opportunity")
    for row in g0_rows:
        seed_id, g0 = row["seed_id"], row["g0"]
        for budget in (0, 1, 2, 3, 4):
            result = pe.run_catalog(truth, g0, TASK_X, TASK_Y, budget, config)
            policies = result["strategies"] + [result["canonical_oracle"]]
            if len(policies) != 17: raise ValueError("policy catalog must contain exactly 17 policies")
            for policy in policies:
                final = {tuple(edge) for edge in policy["final_edges"]}
                learner_state = {pe.pair(a, b): (a, b) for a, b in final}
                learner_state.update({tuple(p): pe.UNRES for p in policy["final_unresolved"]})
                graph_digest = pe.graph_hash(learner_state)
                if graph_digest not in learner_cache:
                    action_choice, predictions = learner_recommendation(train, nodes, final, actions, target, scale)
                    learner_cache[graph_digest] = {"action": action_choice, "candidates": predictions}
                recommendation = learner_cache[graph_digest]
                rows.append({"g0_seed_id": seed_id, "initial_graph_sha256": pe.graph_hash(g0),
                    "g0_graph_sha256": pe.graph_hash(g0), "budget": budget, "policy_id": policy["policy_id"],
                    "repaired_graph_sha256": policy["final_hash"], "learner_input_sha256": graph_digest,
                    "repair_cost": policy["total_cost"],
                    "unused_budget": policy["unused_budget"], "recommended_action": recommendation["action"],
                    "candidate_predictions_train_only": recommendation["candidates"],
                    "initial_metrics": policy["initial_metrics"], "final_metrics": policy["final_metrics"],
                    "edit_count": len(policy["edits"]), "stop_reason": policy["stop_reason"]})
    # Duplicate seed IDs, missing policy-budget rows, and support overflow fail closed.
    expected = len(g0_rows) * 5 * 17
    keys = [(r["g0_seed_id"], r["budget"], r["policy_id"]) for r in rows]
    if len(rows) != expected or len(set(keys)) != expected:
        raise ValueError("recommendation manifest has missing or duplicate rows")
    bound_contract_sha = contract_sha256 or file_sha256(contract_path)
    if len(bound_contract_sha) != 64 or any(c not in "0123456789abcdef" for c in bound_contract_sha):
        raise ValueError("invalid bound scientific contract digest")
    manifest = {"schema": "RESEARCH_D_RECOMMENDATION_LOCK_V1", "locked": True,
        "contract_sha256": bound_contract_sha, "training_sha256": train_hash,
        "task": {"action": TASK_X, "target": TASK_Y}, "actions": actions,
        "target_training_only": target, "scale_training_only": scale,
        "training_rows": int(len(train)), "g0_seed_ids": [r["seed_id"] for r in g0_rows],
        "row_count": len(rows), "policies_per_graph_budget": 17,
        "learner_cache_unique_graphs": len(learner_cache), "graph_free_baseline": {
            "action": baseline_action, "candidate_predictions_train_only": baseline_candidates,
            "interpretation": "associational only; not a causal effect estimate"},
        "recommendations": rows}
    content_hash = sha256_bytes(canonical_json(manifest))
    manifest["content_sha256"] = content_hash
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(canonical_json(manifest) + b"\n")
    return manifest, content_hash


def validate_recommendation_lock(path: Path, expected_contract_hash: str):
    if not path.exists(): raise ValueError("recommendation manifest missing")
    obj = json.loads(path.read_text(encoding="utf-8"))
    recorded = obj.pop("content_sha256", None)
    actual = sha256_bytes(canonical_json(obj))
    if not obj.get("locked") or not recorded or recorded != actual:
        raise ValueError("recommendation lock missing or content hash invalid")
    if obj.get("contract_sha256") != expected_contract_hash:
        raise ValueError("recommendation contract hash mismatch")
    return obj, recorded


def evaluate_locked(*, model, lock_path: Path, contract_path: Path, output_path: Path,
                    evaluation_seed_root: int, rows_per_action: int,
                    bootstrap_replicates: int = 2000, bootstrap_seed: int = 91420263,
                    response_vectors_path: Path | None = None):
    from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import sample_hard_do
    if output_path.exists(): raise FileExistsError("evaluator output already exists")
    if response_vectors_path is not None and response_vectors_path.exists():
        raise FileExistsError("evaluator response-vector artifact already exists")
    contract_hash = file_sha256(contract_path)
    manifest, lock_hash = validate_recommendation_lock(lock_path, contract_hash)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    actions = [float(v) for v in manifest["actions"]]
    if not actions or len(actions) > 5 or len(set(actions)) != len(actions):
        raise ValueError("invalid common action set")
    if rows_per_action > 256 or len(actions) * rows_per_action > 1280:
        raise ValueError("pilot evaluation sample cap exceeded")
    if (contract.get("mode") != "development_reproduction_only"
            or actions != contract.get("action_grid", {}).get("values")
            or evaluation_seed_root != contract.get("evaluation", {}).get("seed_root")
            or rows_per_action != contract.get("evaluation", {}).get("rows_per_action")
            or bootstrap_replicates != contract.get("evaluation", {}).get("bootstrap_replicates")
            or bootstrap_seed != contract.get("evaluation", {}).get("bootstrap_seed")
            or manifest.get("task") != {"action": contract["task"]["action"], "target": contract["task"]["target"]}
            or manifest.get("g0_seed_ids") != contract.get("g0", {}).get("seed_ids")
            or manifest.get("target_training_only") != contract.get("target_scale", {}).get("target")
            or manifest.get("scale_training_only") != contract.get("target_scale", {}).get("scale")
            or manifest.get("training_rows") != contract.get("training", {}).get("n")
            or manifest.get("training_sha256") != contract.get("training", {}).get("sha256")):
        raise ValueError("evaluator inputs differ from the exact scientific reproduction lock")
    if bootstrap_replicates <= 0:
        raise ValueError("bootstrap replicate count must be positive")
    names = list(model.nodes)
    targets = {row["recommended_action"] for row in manifest["recommendations"]}
    if not targets.issubset(set(actions)): raise ValueError("recommendation outside locked action support")
    seeds = manifest.get("g0_seed_ids", [])
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("missing or duplicate development G0 seed IDs")
    expected_keys = {(seed, budget, policy) for seed in seeds for budget in (0, 1, 2, 3, 4)
                     for policy in POLICY_IDS}
    observed_keys = {(row.get("g0_seed_id"), row.get("budget"), row.get("policy_id"))
                     for row in manifest["recommendations"]}
    if observed_keys != expected_keys or len(manifest["recommendations"]) != len(expected_keys):
        raise ValueError("recommendation manifest is incomplete or has duplicate policy-budget keys")
    streams = [derive_seed("evaluator-action", evaluation_seed_root + i) for i in range(len(actions))]
    if len(set(streams)) != len(streams): raise ValueError("duplicate action RNG streams")
    action_summaries, response_vectors, action_seeds = {}, {}, {}
    started = time.perf_counter()
    for index, (action, seed) in enumerate(zip(actions, streams)):
        frame = sample_hard_do(model, TASK_X, action, size=rows_per_action,
                               rng=np.random.default_rng(seed), smoothed=True)
        values = _validate_frame(frame, names, rows_per_action)
        action_col = names.index(TASK_X)
        if not np.all(values[:, action_col] == action): raise ValueError("hard-do value not exact")
        y = values[:, names.index(TASK_Y)].copy()
        if not np.isfinite(y).all(): raise ValueError("nonfinite evaluator target")
        action_summaries[str(action)] = {"n": rows_per_action, "mean": float(y.mean()),
            "sample_variance": float(y.var(ddof=1)), "response_sha256": sha256_bytes(y.tobytes()),
            "sampling_seconds": None}
        response_vectors[action] = y
        action_seeds[str(action)] = seed
        # Only the target vector remains in evaluator memory for its bootstrap.
        del values, frame
    total_seconds = time.perf_counter() - started
    per_call = total_seconds / len(actions)
    for summary in action_summaries.values(): summary["sampling_seconds"] = per_call
    target, scale = manifest["target_training_only"], manifest["scale_training_only"]
    loss_table = {}
    for action_key, summary in action_summaries.items():
        plug = ((summary["mean"] - target) ** 2) / scale**2
        corrected = (summary["mean"] - target) ** 2 - summary["sample_variance"] / summary["n"]
        loss_table[action_key] = {"plug_in_loss": float(plug),
            "bias_corrected_loss": float(corrected / scale**2), "mc_correction_can_be_negative": bool(corrected < 0)}
    action_lookup = {float(k): k for k in action_summaries}
    evaluated = []
    for rec in manifest["recommendations"]:
        l = loss_table[action_lookup[float(rec["recommended_action"])]]["bias_corrected_loss"]
        pi = loss_table[action_lookup[float(rec["recommended_action"])]]["plug_in_loss"]
        evaluated.append({"g0_seed_id": rec["g0_seed_id"], "budget": rec["budget"],
            "policy_id": rec["policy_id"], "action": rec["recommended_action"],
            "loss_bc": l, "loss_plugin": pi, "repair_cost": rec["repair_cost"],
            "repaired_graph_sha256": rec["repaired_graph_sha256"]})

    # Two-source bootstrap: resample G0s as paired units and independently
    # resample rows within each common action draw. The action resample is shared
    # across all graph seeds because the observed action loss table is shared.
    b_reps, rng = bootstrap_replicates, np.random.default_rng(bootstrap_seed)
    paired = {}
    for row in evaluated:
        if row["budget"] == 2 and row["policy_id"] in ("S0", "M1+M2+M3+M4"):
            paired.setdefault(row["g0_seed_id"], {})[row["policy_id"]] = float(row["action"])
    seed_ids = sorted(k for k, v in paired.items() if set(v) == {"S0", "M1+M2+M3+M4"})
    if not seed_ids: raise ValueError("no paired B=2 primary rows")
    actions_matrix = np.empty((b_reps, len(actions)), dtype=float)
    for j, action in enumerate(actions):
        values = response_vectors[action]
        draw_index = rng.integers(0, len(values), size=(b_reps, len(values)))
        boot = values[draw_index]
        boot_mean = boot.mean(axis=1)
        boot_var = boot.var(axis=1, ddof=1)
        actions_matrix[:, j] = ((boot_mean - target) ** 2 - boot_var / len(values)) / scale**2
    action_index = {a: i for i, a in enumerate(actions)}
    seed_deltas = np.empty((len(seed_ids), b_reps), dtype=float)
    for i, seed_id in enumerate(seed_ids):
        s0 = action_index[paired[seed_id]["S0"]]
        fg = action_index[paired[seed_id]["M1+M2+M3+M4"]]
        seed_deltas[i, :] = actions_matrix[:, s0] - actions_matrix[:, fg]
    g0_draws = rng.integers(0, len(seed_ids), size=(b_reps, len(seed_ids)))
    two_source = seed_deltas[g0_draws, np.arange(b_reps)[:, None]].mean(axis=1)
    mc_only = seed_deltas.mean(axis=0)
    fixed_action_losses = {float(k): float(v["bias_corrected_loss"]) for k, v in loss_table.items()}
    fixed_deltas = []
    for seed_id in seed_ids:
        pair = paired[seed_id]
        fixed_deltas.append(fixed_action_losses[pair["S0"]] - fixed_action_losses[pair["M1+M2+M3+M4"]])
    g0_only_draws = np.empty(b_reps, dtype=float)
    for j in range(b_reps): g0_only_draws[j] = np.mean(rng.choice(fixed_deltas, size=len(fixed_deltas), replace=True))
    baseline_action = float(manifest["graph_free_baseline"]["action"])
    baseline_loss = loss_table[action_lookup[baseline_action]]
    primary_uncertainty = {"bootstrap_replicates": b_reps, "bootstrap_seed": bootstrap_seed,
        "g0_only_percentile_95": [float(x) for x in np.quantile(g0_only_draws, [0.025, 0.975])],
        "action_mc_only_percentile_95": [float(x) for x in np.quantile(mc_only, [0.025, 0.975])],
        "two_source_percentile_95": [float(x) for x in np.quantile(two_source, [0.025, 0.975])],
        "two_source_bootstrap_mean": float(np.mean(two_source)),
        "bootstrap_unit": "paired G0 seed plus within-action independent response-row resampling; shared action loss table preserved"}
    result = {"schema": "RESEARCH_D_DEVELOPMENT_EVALUATION_V1", "recommendation_lock_sha256": lock_hash,
        "contract_sha256": contract_hash, "evaluation_seed_root": evaluation_seed_root,
        "action_rng_seeds": action_seeds,
        "rows_per_action": rows_per_action, "total_intervention_rows": len(actions) * rows_per_action,
        "action_order": actions, "action_summary": action_summaries, "loss_table": loss_table,
        "evaluation_rows": evaluated, "sampling_seconds": total_seconds,
        "primary_two_source_uncertainty": primary_uncertainty,
        "graph_free_association_baseline": {"action": baseline_action, "loss_bc": baseline_loss["bias_corrected_loss"],
            "loss_plugin": baseline_loss["plug_in_loss"], "interpretation": "observational association only"},
        "raw_response_rows_saved": False, "policy_recommendation_changed_after_lock": False}
    if response_vectors_path is not None:
        response_buffer = io.BytesIO()
        response_payload = {f"response_{index:02d}": response_vectors[action]
            for index, action in enumerate(actions)}
        response_payload["action_order"] = np.asarray(actions, dtype=np.float64)
        np.savez(response_buffer, **response_payload)
        response_raw = response_buffer.getvalue()
        response_vectors_path.parent.mkdir(parents=True, exist_ok=True)
        with response_vectors_path.open("xb") as stream:
            stream.write(response_raw)
        result["response_vectors_artifact"] = {"filename": response_vectors_path.name,
            "sha256": sha256_bytes(response_raw), "bytes": len(response_raw),
            "rows_per_action": rows_per_action, "actions": actions,
            "format": "NPZ float64 arrays; evaluator-only; outside repository"}
        result["raw_response_rows_saved"] = True
    response_vectors.clear()
    output_path.write_bytes(canonical_json(result) + b"\n")
    return result


def paired_primary(result):
    rows = result["evaluation_rows"]
    paired = {}
    for row in rows:
        if row["budget"] == 2 and row["policy_id"] in ("S0", "M1+M2+M3+M4"):
            paired.setdefault(row["g0_seed_id"], {})[row["policy_id"]] = row["loss_bc"]
    deltas = [v["S0"] - v["M1+M2+M3+M4"] for v in paired.values()
              if set(v) == {"S0", "M1+M2+M3+M4"}]
    if not deltas: raise ValueError("primary comparison missing paired G0 rows")
    return {"n_g0": len(deltas), "mean_delta_loss_bc": float(np.mean(deltas)),
        "sd_across_g0_conditional_on_fixed_eval": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
        "min": float(np.min(deltas)), "max": float(np.max(deltas)),
        "positive_fraction": float(np.mean(np.asarray(deltas) > 0)),
        "interpretation": "development-only, conditional on one fitted DRF, one train sample and shared evaluation draws"}

