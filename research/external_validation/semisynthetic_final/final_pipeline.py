"""Final-only controls for Research D's conditional semisynthetic evaluation."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.external_validation.semisynthetic_evaluation import reproducibility as repro

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "final_contract.json"
NAMESPACE = "research-d-external-semisynthetic-final-v1"
EXPECTED_TRAIN_RAW = "dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094"
EXPECTED_TRAIN_NUMERIC = "bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39"
CODE_FILES = [
    "research/external_validation/semisynthetic_final/RESEARCH_D_FINAL_CONTRACT.md",
    "research/external_validation/semisynthetic_final/final_contract.json",
    "research/external_validation/semisynthetic_final/final_pipeline.py",
    "research/external_validation/semisynthetic_final/final_runner.py",
    "research/external_validation/semisynthetic_final/final_evaluate_worker.py",
    "research/external_validation/semisynthetic_final/final_analyze.py",
    "research/external_validation/semisynthetic_final/resource_supervisor.py",
    "research/external_validation/semisynthetic_evaluation/pipeline.py",
    "research/external_validation/semisynthetic_evaluation/reproducibility.py",
    "research/external_validation/semisynthetic_evaluation/recommendation_worker.py",
    "research/external_validation/semisynthetic_adapter/float_hard_do_adapter.py",
    "research/original_objective/g0_candidate.py",
    "research/original_objective/policy_engine.py",
    "src/integrated_pilot.py", "src/decision_mvp.py", "src/pilot_fit.py",
    "tests/test_research_d_final_pipeline.py",
]


def contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def contract_hash() -> str:
    return d.file_sha256(CONTRACT)


def derive_final_seed(label: str) -> int:
    raw = f"{NAMESPACE}|{label}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], "big")


def g0_seed_ids() -> list[int]:
    ids = contract()["sample"]["g0_ids"]
    if ids != list(range(703001, 703201)):
        raise ValueError("final G0 IDs do not match the locked seed schedule")
    return ids


def file_sha(path: Path) -> str:
    return d.file_sha256(path)


def expected_env() -> dict:
    from rpy2.robjects import r
    import importlib.metadata
    import networkx as nx
    import pandas as pd
    from rpy2.robjects.packages import isinstalled
    if not isinstalled("drf"):
        raise RuntimeError("pinned isolated R library does not contain drf")
    return {"python": sys.version.split()[0], "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__, "networkx": nx.__version__,
        "R": str(r("as.character(getRversion())")[0]),
        "R_drf": str(r('as.character(packageVersion("drf"))')[0]),
        "rpy2": importlib.metadata.version("rpy2"),
        "causalAssembly": importlib.metadata.version("causalAssembly")}


def validate_paths(*, source_root: Path, data_root: Path, training_csv: Path,
                   output_root: Path | None = None) -> dict:
    source_root, data_root, training_csv = map(Path.resolve,
        (source_root, data_root, training_csv))
    identity = repro.repository_identity(ROOT, require_clean=True)
    source = d.verify_sources(source_root, data_root)
    if file_sha(training_csv) != EXPECTED_TRAIN_RAW:
        raise ValueError("fixed Development training CSV raw digest mismatch")
    if output_root is not None:
        repro.require_external_outputs(ROOT, [output_root])
        if output_root.exists() and any(output_root.iterdir()):
            raise FileExistsError("final run output directory already contains data")
    module_path = Path(subprocess.check_output([sys.executable, "-c",
        "import sys, pathlib; sys.path.insert(0, sys.argv[1]); import causalAssembly; print(pathlib.Path(causalAssembly.__file__).resolve())",
        str(source_root)], text=True).strip())
    try:
        module_path.relative_to(source_root)
    except ValueError as exc:
        raise ValueError(f"imported causalAssembly is outside pinned source worktree: {module_path}") from exc
    return {"repository": identity, "source": source, "training_csv_sha256": file_sha(training_csv),
        "runtime": expected_env(), "imported_causalAssembly": str(module_path)}


def make_final_g0(truth: dict, nodes: list[str], seed_id: int) -> dict:
    from research.original_objective.g0_candidate import corrupt_graph_candidate
    from research.original_objective import policy_engine as pe
    master_seed = derive_final_seed(f"g0|{seed_id}")
    record = corrupt_graph_candidate(truth, nodes=nodes, action=d.TASK_X, target=d.TASK_Y,
        master_seed=master_seed, task_id=f"research-d-final-{seed_id}",
        true_corruption_rate=0.15, false_adjacency_rate=0.05)
    record["research_d_seed_id"] = int(seed_id)
    record["research_d_master_seed"] = master_seed
    record["contract_status"] = "RESEARCH_D_FINAL_V1"
    record["test_or_cohort_use"] = "locked_final_only"
    g0 = d.reconstruct_g0(record, truth)
    return {"seed_id": int(seed_id), "record": record, "graph_sha256": pe.graph_hash(g0)}


def build_seed_collision_audit(*, source_root: Path, data_root: Path,
                               prior_g0_manifest: Path, reproduction_lock: Path,
                               adapter_summary: Path, prior_records: list[Path]) -> dict:
    """Check final IDs and derived streams against every recorded prior stream."""
    c = contract()
    ids = g0_seed_ids()
    ids_seen = set(ids)
    prior_ids = set(range(701001, 701065)) | set(range(702001, 702033))
    if ids_seen & prior_ids or len(ids_seen) != 200:
        raise ValueError("final G0 IDs overlap or are duplicated")
    lock = json.loads(reproduction_lock.read_text(encoding="utf-8"))
    old_streams = {int(lock["fit_seed"]), int(lock["fit_reproducibility"]["check_seed"]),
        int(lock["training"]["seed"]), int(lock["evaluation"]["seed_root"]),
        int(lock["evaluation"]["bootstrap_seed"])}
    old_streams.update(map(int, lock["evaluation"].get("action_rng_seeds", {}).values()))
    # Include master seeds used by the previous G0 cohorts even where only the seed IDs were persisted.
    from research.external_validation.semisynthetic_evaluation.pipeline import derive_seed
    old_streams.update(derive_seed("g0", sid) for sid in list(range(701001,701065))+list(range(702001,702033)))
    g0_manifest = json.loads(prior_g0_manifest.read_text(encoding="utf-8"))
    old_streams.update(int(row.get("master_seed")) for row in g0_manifest.get("g0", [])
                       if row.get("master_seed") is not None)
    smoke = json.loads(adapter_summary.read_text(encoding="utf-8"))
    # Adapter records the fixed smoke seed and any generated integration seeds.
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if "seed" in key.lower() and isinstance(child, int):
                    old_streams.add(child)
                elif "seed" in key.lower() and isinstance(child, list):
                    old_streams.update(x for x in child if isinstance(x, int))
                walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(smoke)
    prior_ids = set(prior_ids)
    for record_path in prior_records:
        if not record_path.is_file():
            raise FileNotFoundError(f"required prior RNG/provenance record missing: {record_path.name}")
        prior = json.loads(record_path.read_text(encoding="utf-8"))
        walk(prior)
        # The G0 ID ranges count as prior seed identifiers even when a manifest omits master-seed values.
        for key in ("seed_ids", "g0_seed_ids"):
            val = prior.get(key)
            if isinstance(val, list): prior_ids.update(int(x) for x in val if isinstance(x, int))
    if ids_seen & prior_ids:
        raise ValueError("final G0 seed IDs overlap a recorded prior seed ID")
    g0_seeds = [derive_final_seed(f"g0|{seed_id}") for seed_id in ids]
    action_values = c["task"]["actions"]
    eval_seeds = [derive_final_seed(f"action|{i}|{repr(float(action))}")
                  for i, action in enumerate(action_values)]
    bootstrap_seed = derive_final_seed("bootstrap|primary-two-source")
    secondary_seed = derive_final_seed("bootstrap|m4-vs-fullgreedy")
    cost_seed = derive_final_seed("bootstrap|paired-cost")
    resource_seed = derive_final_seed("resource-benchmark")
    all_new = g0_seeds + eval_seeds + [bootstrap_seed, secondary_seed, cost_seed, resource_seed]
    if len(all_new) != len(set(all_new)) or set(all_new) & old_streams:
        raise ValueError("final RNG stream collides with another final stream or recorded prior stream")
    return {"namespace": NAMESPACE, "g0_ids": ids, "g0_master_seed_sha256": hashlib.sha256(
        np.asarray(g0_seeds, dtype=np.uint32).tobytes()).hexdigest(),
        "action_seeds": eval_seeds, "bootstrap_seed": bootstrap_seed,
        "secondary_bootstrap_seed": secondary_seed,"paired_cost_seed":cost_seed,
        "resource_benchmark_seed":resource_seed,
        "new_seed_values_unique": True, "prior_stream_collision_count": 0,
        "prior_g0_ids_disjoint": True}


def runtime_manifest(source_root: Path, data_root: Path, training_csv: Path) -> dict:
    validation = validate_paths(source_root=source_root, data_root=data_root,
                                training_csv=training_csv)
    return {**validation, "code_sha256": repro.research_code_hashes(ROOT, CODE_FILES),
        "code_commit": validation["repository"]["commit"],
        "code_tree": validation["repository"]["tree"],
        "contract_sha256": contract_hash()}


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fit_diagnostic(source_root: Path, data_root: Path) -> tuple[object, object, dict]:
    model, source, fit_info = d.load_fit_station1(source_root, data_root, 91420261)
    check_seed = 3124221787
    model.random_state = np.random.default_rng(check_seed)
    frame = model.sample_from_drf(size=16)
    digest = hashlib.sha256(frame.to_numpy(dtype=float).tobytes(order="C")).hexdigest()
    if digest != "11f3a13511bfcf405c8ab167aced154a01fd068711a1fee06fca89e6362856f1":
        raise ValueError("same-seed DRF diagnostic differs from the reproduced Development DGP")
    del frame
    return model, source, {**fit_info, "diagnostic_rows": 16, "diagnostic_seed": check_seed,
        "diagnostic_sha256": digest}


def create_request_and_runlock(*, model, source, train_path: Path, source_root: Path,
                               data_root: Path, paths: dict[str, Path],
                               fit_info: dict, seed_audit: dict) -> dict:
    from research.external_validation.semisynthetic_evaluation.reproducibility import read_training_frame
    from research.original_objective import policy_engine as pe
    c = contract()
    if file_sha(train_path) != EXPECTED_TRAIN_RAW:
        raise ValueError("training frame raw hash mismatch")
    nodes = list(model.nodes)
    train = read_training_frame(train_path, node_order=nodes, rows=512,
                                expected_numeric_sha256=EXPECTED_TRAIN_NUMERIC)
    if hashlib.sha256(train.to_numpy(dtype=float).tobytes(order="C")).hexdigest() != EXPECTED_TRAIN_NUMERIC:
        raise ValueError("training frame numeric hash mismatch")
    y = train[d.TASK_Y].to_numpy(dtype=float)
    target, scale = float(y.mean() + y.std(ddof=1)), float(y.std(ddof=1))
    if target != c["task"]["target"] or scale != c["task"]["scale"]:
        raise ValueError("fixed frame target or scale differs from locked contract")
    actions, support = d.action_grid(source, train, model)
    if actions != c["task"]["actions"]:
        raise ValueError("action grid derived from pinned fit source differs")
    truth = {pe.pair(a, b): (a, b) for a, b in model.graph.edges}
    g0 = [make_final_g0(truth, nodes, seed_id) for seed_id in g0_seed_ids()]
    if len(g0) != 200 or [row["seed_id"] for row in g0] != g0_seed_ids():
        raise ValueError("final G0 generation was incomplete or unordered")
    request = {"schema": "RESEARCH_D_FINAL_RECOMMENDATION_INPUT_V1",
        "nodes": nodes, "reference_edges": sorted(map(list, model.graph.edges)),
        "actions": actions, "training_numeric_sha256": EXPECTED_TRAIN_NUMERIC,
        "g0": g0}
    atomic_json(paths["request"], request)
    runlock = {"schema": "RESEARCH_D_FINAL_RUN_LOCK_V1", "status": "LOCKED_BEFORE_RECOMMENDATION_AND_EVALUATION",
        "run_id": c["run_id"], "mode": "external_final_evaluation_only",
        "contract_sha256": contract_hash(), "repository": repro.repository_identity(ROOT),
        "code_sha256": repro.research_code_hashes(ROOT, CODE_FILES),
        "external_source": repro.external_source_manifest(source_root),
        "source": d.verify_sources(source_root, data_root), "runtime": expected_env(),
        "training": {"raw_csv_sha256": file_sha(train_path), "numeric_sha256": EXPECTED_TRAIN_NUMERIC,
            "rows": 512, "new_rows": 0},
        "graph": {"nodes": nodes, "edges": sorted(map(list, model.graph.edges)),
            "sha256": fit_info["graph_sha256"]},
        "fit_diagnostic": fit_info,
        "fit": {"seed": c["generator"]["fit_seed"], "diagnostic": {
            "seed": c["generator"]["diagnostic_seed"], "rows": c["generator"]["diagnostic_rows"],
            "sha256": c["generator"]["diagnostic_sha256"]}},
        "task": c["task"], "learner_and_repair": c["learner_and_repair"],
        "sampling": {**c["sample"], "action_seeds": seed_audit["action_seeds"],
            "bootstrap_seed": seed_audit["bootstrap_seed"],
            "secondary_bootstrap_seed": seed_audit["secondary_bootstrap_seed"],
            "paired_cost_seed":seed_audit["paired_cost_seed"],
            "resource_benchmark_seed":seed_audit["resource_benchmark_seed"]},
        "loss_and_uncertainty": c["loss_and_uncertainty"],
        "resource_limits": c["resource_limits"], "action_support_checks": support,
        "g0_records": g0, "g0_initial_graph_hashes": {str(x["seed_id"]): x["graph_sha256"] for x in g0},
        "training_path_external_only": str(train_path), "output_names": sorted(paths),
        "final_evaluation_seeds_or_samples_created": False, "seed_collision_audit": seed_audit}
    # Keep raw G0 error records in the external lock; the public summary uses only aggregate/hash evidence.
    atomic_json(paths["run_lock"], runlock)
    return runlock


def enrich_recommendations_with_edit_zones(request_path: Path, recommendation_path: Path) -> dict:
    """Attach exact task/off-task edit counts from the unchanged policy engine."""
    from collections import Counter
    from research.original_objective import policy_engine as pe
    request=json.loads(request_path.read_text(encoding="utf-8"))
    manifest=json.loads(recommendation_path.read_text(encoding="utf-8"))
    old_content=manifest.pop("content_sha256",None)
    if hashlib.sha256(d.canonical_json(manifest)).hexdigest()!=old_content:
        raise ValueError("base recommendation manifest is not integrity-valid")
    truth={pe.pair(a,b):(a,b) for a,b in request["reference_edges"]}
    g0_by_seed={int(x["seed_id"]):x for x in request["g0"]}
    rec_by_key={(x["g0_seed_id"],x["budget"],x["policy_id"]):x for x in manifest["recommendations"]}
    if len(rec_by_key)!=17000:
        raise ValueError("cannot enrich incomplete final recommendation manifest")
    config=pe.Config(fp_rule="A",normalization="fixed_opportunity")
    n_checked=0
    for seed_id in manifest["g0_seed_ids"]:
        initial=d.reconstruct_g0(g0_by_seed[int(seed_id)]["record"],truth)
        for budget in (0,1,2,3,4):
            catalog=pe.run_catalog(truth,initial,d.TASK_X,d.TASK_Y,budget,config)
            for policy in catalog["strategies"]+[catalog["canonical_oracle"]]:
                row=rec_by_key[(seed_id,budget,policy["policy_id"])]
                if (row["repaired_graph_sha256"]!=policy["final_hash"]
                        or row["repair_cost"]!=policy["total_cost"]
                        or row["edit_count"]!=len(policy["edits"])):
                    raise ValueError("final recommendation disagrees with deterministic policy-engine replay")
                task_count=sum(bool(e["task_zone"]) for e in policy["edits"])
                type_counts=Counter(e["error_type"] for e in policy["edits"])
                operation_counts=Counter(e["operation"] for e in policy["edits"])
                row["task_zone_edit_count"]=task_count
                row["off_task_edit_count"]=len(policy["edits"])-task_count
                row["edit_error_type_counts"]=dict(sorted(type_counts.items()))
                row["edit_operation_counts"]=dict(sorted(operation_counts.items()))
                n_checked+=1
    manifest["content_sha256"]=hashlib.sha256(d.canonical_json(manifest)).hexdigest()
    tmp=recommendation_path.with_suffix(recommendation_path.suffix+".enriched")
    tmp.write_bytes(d.canonical_json(manifest)+b"\n")
    os.replace(tmp,recommendation_path)
    return {"recommendation_rows":len(manifest["recommendations"]),
        "policy_rows_replayed":n_checked,"task_off_task_edit_fields":True,
        "new_content_sha256":manifest["content_sha256"]}


def verify_lock(*, lock_path: Path, expected_lock_sha256: str,
                source_root: Path, data_root: Path, training_path: Path,
                recommendation_path: Path | None = None,
                execution_manifest_path: Path | None = None) -> dict:
    if file_sha(lock_path) != expected_lock_sha256:
        raise ValueError("final run lock raw digest mismatch")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("schema") != "RESEARCH_D_FINAL_RUN_LOCK_V1" \
            or lock.get("status") != "LOCKED_BEFORE_RECOMMENDATION_AND_EVALUATION":
        raise ValueError("unapproved final run lock")
    if contract_hash() != lock.get("contract_sha256"):
        raise ValueError("final scientific contract changed")
    identity = repro.repository_identity(ROOT)
    if identity != lock.get("repository"):
        raise ValueError("final source commit/tree/worktree changed")
    if repro.research_code_hashes(ROOT, CODE_FILES) != lock.get("code_sha256"):
        raise ValueError("final research code byte hash changed")
    if expected_env() != lock.get("runtime"):
        raise ValueError("final Python/R/numerical environment changed")
    if d.verify_sources(source_root, data_root) != lock.get("source") \
            or repro.external_source_manifest(source_root) != lock.get("external_source"):
        raise ValueError("pinned causalAssembly source/data changed")
    if file_sha(training_path) != lock["training"]["raw_csv_sha256"]:
        raise ValueError("fixed Development frame bytes changed")
    if recommendation_path is not None:
        rec, rec_hash = d.validate_recommendation_lock(recommendation_path, lock["contract_sha256"])
        if rec.get("row_count") != 17000 or rec.get("g0_seed_ids") != g0_seed_ids():
            raise ValueError("final recommendation support is incomplete")
        if execution_manifest_path is None:
            raise ValueError("final execution manifest required after recommendation lock")
        manifest = json.loads(execution_manifest_path.read_text(encoding="utf-8"))
        if manifest.get("recommendation_raw_sha256") != file_sha(recommendation_path) \
                or manifest.get("recommendation_content_sha256") != rec_hash \
                or manifest.get("run_lock_sha256") != expected_lock_sha256:
            raise ValueError("recommendation/execution manifest binding failed")
    return lock


def build_execution_manifest(*, lock_path: Path, recommendation_path: Path,
                             paths: dict[str, Path]) -> dict:
    c = contract()
    lock_sha = file_sha(lock_path)
    rec = json.loads(recommendation_path.read_text(encoding="utf-8"))
    rec_body = dict(rec); rec_hash = rec_body.pop("content_sha256", None)
    actual = hashlib.sha256(d.canonical_json(rec_body)).hexdigest()
    if actual != rec_hash or rec.get("row_count") != 17000:
        raise ValueError("final recommendation manifest hash/count failed")
    manifest = {"schema": "RESEARCH_D_FINAL_EXECUTION_MANIFEST_V1", "run_id": c["run_id"],
        "mode": "external_final_evaluation_only", "run_lock_sha256": lock_sha,
        "contract_sha256": contract_hash(), "recommendation_raw_sha256": file_sha(recommendation_path),
        "recommendation_content_sha256": rec_hash, "recommendation_rows": rec["row_count"],
        "code_sha256": repro.research_code_hashes(ROOT, CODE_FILES),
        "repository": repro.repository_identity(ROOT),
        "external_source_sha256": repro.external_source_manifest(Path(paths["source_root"])),
        "training_sha256": EXPECTED_TRAIN_NUMERIC,
        "evaluation_seeds": c["sample"], "locked_before_intervention_sampling": True}
    atomic_json(paths["execution_manifest"], manifest)
    return manifest


def verify_final_artifacts(lock_path: Path, execution_path: Path,
                           recommendation_path: Path) -> tuple[dict, dict, dict]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    rec = json.loads(recommendation_path.read_text(encoding="utf-8"))
    manifest = json.loads(execution_path.read_text(encoding="utf-8"))
    if file_sha(lock_path) != manifest.get("run_lock_sha256"):
        raise ValueError("final lock hash differs from execution manifest")
    if file_sha(recommendation_path) != manifest.get("recommendation_raw_sha256"):
        raise ValueError("recommendation raw file hash differs from execution manifest")
    if (manifest.get("code_sha256") != lock.get("code_sha256")
            or manifest.get("repository") != lock.get("repository")
            or manifest.get("contract_sha256") != lock.get("contract_sha256")
            or manifest.get("run_id") != lock.get("run_id")
            or manifest.get("mode") != lock.get("mode")):
        raise ValueError("execution manifest code/repository/contract binding failed")
    body = dict(rec); content = body.pop("content_sha256", None)
    if hashlib.sha256(d.canonical_json(body)).hexdigest() != content \
            or content != manifest.get("recommendation_content_sha256"):
        raise ValueError("recommendation content hash differs from execution manifest")
    if rec.get("row_count") != 17000 or manifest.get("recommendation_rows") != 17000:
        raise ValueError("final recommendation row count is not exactly 17,000")
    expected = {(s, b, p) for s in g0_seed_ids() for b in range(5) for p in d.POLICY_IDS}
    keys = {(r["g0_seed_id"], r["budget"], r["policy_id"]) for r in rec["recommendations"]}
    if keys != expected or len(keys) != 17000:
        raise ValueError("final recommendation key grid incomplete or duplicated")
    if rec.get("actions") != lock["task"]["actions"] \
            or rec.get("task") != {"action": d.TASK_X, "target": d.TASK_Y} \
            or rec.get("training_sha256") != EXPECTED_TRAIN_NUMERIC \
            or rec.get("target_training_only") != lock["task"]["target"] \
            or rec.get("scale_training_only") != lock["task"]["scale"]:
        raise ValueError("final recommendation scientific input binding mismatch")
    return lock, rec, manifest
