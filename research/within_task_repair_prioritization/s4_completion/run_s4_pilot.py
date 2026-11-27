"""One-shot, lock-bound S4 development pilot; private unit outputs only."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from research.budget_aware_refinement.step3_adapter import prepare, evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
from research.budget_aware_refinement.step4c1_scm import generate_scm_parameters, generate_observations
from research.original_objective import policy_engine as pe
from research.original_objective.g0_candidate import corrupt_graph_candidate
from research.within_task_repair_prioritization import s3_analysis as s3
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

LOCK_PATH = HERE / "s4_pilot_lock.json"
OUT = Path(os.environ.get("S4_PILOT_OUTPUT", r"C:\DAT_RESEARCH\research-s4\pilot-20261127-v1"))
BOOT = 2_000
TOL = 1e-12
MAX_WALL_SECONDS = 7_200
MAX_RSS_BYTES = 4 * 1024**3
PEAK_RSS_BYTES = 0


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def current_commit() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def process_rss_bytes() -> int:
    """Get this single-process runner's working set on Windows without dependencies."""
    if os.name != "nt":
        raise RuntimeError("pilot resource guard requires Windows GetProcessMemoryInfo")
    import ctypes
    from ctypes import wintypes

    class CountersEx(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PrivateUsage", ctypes.c_size_t)]
    counters = CountersEx()
    counters.cb = ctypes.sizeof(counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    get_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(CountersEx), wintypes.DWORD]
    get_info.restype = wintypes.BOOL
    if not get_info(handle, ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.WorkingSetSize)


def guard(started: float) -> int:
    global PEAK_RSS_BYTES
    if time.perf_counter() - started > MAX_WALL_SECONDS:
        raise TimeoutError("S4 pilot wall-time cap exceeded")
    rss = process_rss_bytes()
    PEAK_RSS_BYTES = max(PEAK_RSS_BYTES, rss)
    if rss > MAX_RSS_BYTES:
        raise MemoryError(f"S4 pilot RSS cap exceeded: {rss}")
    return rss


def write_json(path: Path, value) -> None:
    path.write_bytes(json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def verify_lock(lock: dict) -> dict:
    if lock.get("contract_status") != "LOCKED_BEFORE_GENERATION":
        raise ValueError("pilot contract is not locked")
    if lock.get("classification") != "exploratory_development_pilot":
        raise ValueError("unapproved pilot mode")
    commit = current_commit()
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain=v1"], text=True).strip():
        raise ValueError("execution checkout must be clean")
    source_commit = lock.get("execution_commit")
    if not source_commit or subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", source_commit, "HEAD"]).returncode:
        raise ValueError("locked execution source commit is not an ancestor of HEAD")
    source_tree = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", f"{source_commit}^{{tree}}"], text=True).strip()
    if source_tree != lock.get("execution_tree"):
        raise ValueError("execution source tree does not match the lock")
    code = HERE / "run_s4_pilot.py"
    if sha_file(code) != lock.get("runner_sha256"):
        raise ValueError("runner bytes do not match locked digest")
    for relative, expected in lock.get("source_hashes", {}).items():
        path = ROOT / relative
        if not path.is_file() or sha_file(path) != expected:
            raise ValueError(f"locked source mismatch: {relative}")
    if not sha_file(HERE / "S4_PILOT_SCIENTIFIC_CONTRACT.md") == lock.get("contract_sha256"):
        raise ValueError("scientific contract digest mismatch")
    from importlib.metadata import version
    env = {"python": platform.python_version(), "numpy": np.__version__, "pandas": version("pandas")}
    if env != lock.get("environment"):
        raise ValueError(f"environment fingerprint mismatch: {env}")
    return {"git_commit": commit, "execution_source_commit": source_commit,
            "execution_source_tree": source_tree,
            "git_tree": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"], text=True).strip(),
            "runner_sha256": sha_file(code), "lock_sha256": sha_file(LOCK_PATH), "environment": env,
            "contract_sha256": sha_file(HERE / "S4_PILOT_SCIENTIFIC_CONTRACT.md"),
            "source_hashes": {rel: sha_file(ROOT / rel) for rel in lock["source_hashes"]}}


def make_config() -> pe.Config:
    return pe.Config(fp_rule="A", normalization="fixed_opportunity",
                     costs=(("add", 1), ("delete", 1), ("orient", 1),
                            ("resolve", 1), ("delete_unresolved", 1)),
                     beta=(1, 1, 1, 1), weights=(1, 1, 1, 1),
                     task_multiplier=1.0, route_relevant_fp=())


def derive_seed(namespace: str, *parts) -> int:
    raw = "|".join((namespace, *(str(x) for x in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def delta_for(cohort: str, scm_id: str) -> int:
    digest = hashlib.sha256(f"research-s4-pilot-v1|delta|{cohort}|{scm_id}".encode()).digest()
    return 1 if digest[0] & 1 else -1


def feasible_m4(truth, g0, action, target, config):
    result = []
    for edit in pe.candidates(truth, g0, action, target, config):
        if edit.metric != "M4" or not s3.direct_task_edit(edit, truth, g0, action, target, config):
            continue
        graph = pe.apply(g0, edit)
        if pe.dag(graph):
            result.append((edit, graph))
    return result


def make_units(lock: dict, started: float, journal: Path) -> tuple[list[dict], list[dict], dict]:
    cfg = make_config()
    units: list[dict] = []
    attempt_rows: list[dict] = []
    cohort_meta = {}
    def append_event(event):
        with journal.open("ab") as stream:
            stream.write(canonical(event) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    for name in ("general", "opportunity_rich_diagnostic"):
        cohort_attempt_start = len(attempt_rows)
        spec = lock["cohorts"][name]
        master = int(spec["master_seed"])
        prefix = lock["proposal_id_prefixes"][name]
        selected = []
        admitted = 0
        for ix in range(int(lock["max_proposal_g0_screening_attempts_per_cohort"])):
            guard(started)
            proposal_id = f"{prefix}-{ix:05d}"
            proposal = build_structural_proposal(cohort="development", master_seed=master,
                                                 proposal_id=proposal_id, attempt=0)
            item = {"cohort": name, "proposal_id": proposal_id,
                    "event": "proposal_screen",
                    "proposal_accepted": bool(proposal.get("accepted")),
                    "proposal_reason": proposal.get("reason")}
            if proposal.get("accepted"):
                admitted += 1
                truth = pe.state([tuple(edge) for edge in proposal["topology_edges"]])
                g0_seed = derive_seed("research-s4-pilot-v1", name, proposal_id, "g0")
                corruption = corrupt_graph_candidate(truth, nodes=proposal["nodes"],
                    action=proposal["action"], target=proposal["target"], master_seed=g0_seed,
                    task_id=f"research-s4-pilot-v1:{name}:{proposal_id}")
                initial = pe.state(corruption["initial_graph"]["edges"],
                                   unresolved=corruption["initial_graph"]["unresolved"])
                candidates = feasible_m4(truth, initial, proposal["action"], proposal["target"], cfg)
                item.update({"g0_generated": True, "g0_seed": g0_seed,
                             "truth_graph_sha256": pe.graph_hash(truth),
                             "initial_graph_sha256": pe.graph_hash(initial),
                             "initial_m4_feasible_count": len(candidates),
                             "selected_for_analysis": False})
                eligible = name == "general" or len(candidates) >= 2
                if eligible and len(selected) < int(spec["target_scm"]):
                    scm_id = f"s4-{name}-{len(selected):03d}"
                    delta = delta_for(name, scm_id)
                    item["event"] = "generation_started"
                    item["selected_for_analysis"] = True
                    item["scm_id"] = scm_id
                    append_event(item)
                    # Coefficients and observations are drawn only after structural admission.
                    generator_proposal = dict(proposal)
                    generator_proposal["scm_id"] = f"dev-scm-{scm_id}"
                    generator_proposal["master_seed"] = master
                    scm = generate_scm_parameters(generator_proposal)
                    observations = generate_observations(generator_proposal, scm)
                    unit = {"cohort": name, "scm_id": scm_id, "proposal_id": proposal_id,
                            "proposal": proposal, "truth_spec": scm["truth_spec"],
                            "truth_equation_sha256": scm["equation_signature_sha256"],
                            "observations": observations["rows"],
                            "observation_sha256": observations["data_sha256"],
                            "observation_rows": observations["n_rows"],
                            "initial_graph": initial, "initial_graph_sha256": pe.graph_hash(initial),
                            "corruption": corruption, "g0_seed": g0_seed,
                            "initial_m4_feasible_count": len(candidates), "delta": delta,
                            "config": cfg}
                    selected.append(unit)
                    item["selected_for_analysis"] = True
                    item["scm_id"] = scm_id
                    append_event({"event": "unit_generated", "cohort": name, "scm_id": scm_id,
                                  "truth_equation_sha256": scm["equation_signature_sha256"],
                                  "observation_sha256": observations["data_sha256"],
                                  "observation_rows": observations["n_rows"]})
                    units.append(unit)
                item["event"] = "g0_screen_complete"
            attempt_rows.append(item)
            append_event(item)
            if len(selected) >= int(spec["target_scm"]):
                break
        cohort_attempts = attempt_rows[cohort_attempt_start:]
        cohort_meta[name] = {"target": int(spec["target_scm"]), "retained": len(selected),
                             "screening_attempts": len(cohort_attempts), "proposal_admitted": admitted,
                             "g0_screening_draws": sum(bool(row.get("g0_generated")) for row in cohort_attempts),
                             "structural_eligibility": spec["eligibility"],
                             "shortfall": max(0, int(spec["target_scm"]) - len(selected))}
    return units, attempt_rows, cohort_meta


def state_record(graph, edit_sequence=(), policy="diagnostic", budget=0):
    return {"graph": dict(graph), "graph_hash": pe.graph_hash(graph),
            "edit_sequence": list(edit_sequence), "policy": policy, "budget": budget}


def build_states(unit: dict, cohort: str) -> tuple[dict[str, dict], list[dict], list[dict]]:
    truth, g0 = pe.state(unit["proposal"]["topology_edges"]), unit["initial_graph"]
    action, target, cfg = unit["proposal"]["action"], unit["proposal"]["target"], unit["config"]
    states: dict[str, dict] = {}
    policy_rows = []

    def add(record):
        key = record["graph_hash"]
        states.setdefault(key, record)
        return key

    for budget in range(5):
        for policy, subset, canonical in (("S0", (), False), ("M4", ("M4",), False),
                                          ("FULL_GREEDY", pe.METRICS, False)):
            result = pe.run(truth, g0, action, target, budget, subset, cfg, canonical=canonical)
            graph = pe.state(result["final_edges"], unresolved=result["final_unresolved"])
            key = add(state_record(graph, result["edits"], policy, budget))
            policy_rows.append({"cohort": cohort, "scm_id": unit["scm_id"], "policy": policy,
                                "budget": budget, "graph_hash": key, "cost": result["total_cost"]})

    for combo in s3.SETS:
        graph, log = s3.greedy(truth, g0, action, target, cfg, combo, 2)
        key = add(state_record(graph, log, "T_GREEDY", 2))
        policy_rows.append({"cohort": cohort, "scm_id": unit["scm_id"], "policy": "T_GREEDY:"+"+".join(combo),
                            "budget": 2, "graph_hash": key, "cost": len(log)})

    # Privileged benchmark universe is fixed before any truth response is queried.
    pool = [edit for edit in pe.candidates(truth, g0, action, target, cfg) if edit.metric == "M4"]
    feasible0 = feasible_m4(truth, g0, action, target, cfg)
    add(state_record(g0, (), "EXPOST_NO_EDIT", 0))
    for edit, graph in feasible0:
        add(state_record(graph, (edit.key,), "EXPOST_SINGLE", 1))
    sequences = []
    for e1, g1 in feasible0:
        for e2 in pool:
            if e2.key == e1.key or not s3.direct_task_edit(e2, truth, g1, action, target, cfg):
                continue
            g2 = pe.apply(g1, e2)
            if not pe.dag(g2):
                continue
            sequence = (e1.key, e2.key)
            add(state_record(g2, sequence, "EXPOST_TWO_EDIT", 2))
            sequences.append({"scm_id": unit["scm_id"], "e1": e1, "e2": e2, "g1": g1, "g2": g2})
    return states, policy_rows, [{"feasible0": feasible0, "pool": pool, "sequences": sequences}]


def recommendation_stage(units: list[dict], started: float, out: Path) -> tuple[list[dict], dict, list[dict]]:
    manifest = []
    unit_states = []
    state_manifest = []
    for unit in units:
        guard(started)
        cohort = unit["cohort"]
        states, policies, diagnostics = build_states(unit, cohort)
        proposal = unit["proposal"]
        data = np.asarray(unit["observations"], dtype=np.float64)
        schema = list(proposal["nodes"])
        request = {"node_ids": schema, "action": proposal["action"], "target": proposal["target"]}
        rec_by_hash = {}
        for graph_hash, state in sorted(states.items()):
            guard(started)
            graph_result = {"final_graph": [list(edge) for edge in sorted(e for e in state["graph"].values() if e != pe.UNRES)]}
            _, selection = prepare(request, data, schema, schema, unit["delta"], fit_model,
                                   static_mean_response, graph_result=graph_result)
            rec_by_hash[graph_hash] = {"selected_k": float(selection["selected_k"]),
                                       "selected_action": float(next(x["action"] for x in selection["candidates"] if x["k"] == selection["selected_k"])),
                                       "target": float(selection["target"]), "scale": float(selection["sd_y"])}
            state_manifest.append({"cohort": cohort, "scm_id": unit["scm_id"], "graph_hash": graph_hash,
                                   "selected_k": rec_by_hash[graph_hash]["selected_k"],
                                   "selected_action": rec_by_hash[graph_hash]["selected_action"],
                                   "target": rec_by_hash[graph_hash]["target"], "scale": rec_by_hash[graph_hash]["scale"]})
        unit_states.append({"unit": unit, "states": states, "policies": policies,
                            "diagnostics": diagnostics[0], "recommendations": rec_by_hash})
    manifest = sorted(state_manifest, key=lambda r:(r["cohort"], r["scm_id"], r["graph_hash"]))
    path = out / "recommendation_manifest_private.json"
    write_json(path, manifest)
    digest = sha_file(path)
    binding = {"recommendation_manifest_sha256": digest, "rows": len(manifest),
               "recommendation_locked_before_truth_evaluation": True,
               "truth_response_accessed": False}
    write_json(out / "recommendation_lock.json", binding)
    return unit_states, binding, manifest


def evaluator_stage(unit_states: list[dict], binding: dict, out: Path, started: float):
    if sha_file(out / "recommendation_manifest_private.json") != binding["recommendation_manifest_sha256"]:
        raise ValueError("recommendation lock mismatch")
    unit_rows, candidate_rows, interaction_rows, policy_rows = [], [], [], []
    for entry in unit_states:
        guard(started)
        unit, states = entry["unit"], entry["states"]
        truth = unit["truth_spec"]
        proposal = unit["proposal"]
        outcomes = {}
        for graph_hash, state in states.items():
            graph_result = {"final_graph": [list(edge) for edge in sorted(e for e in state["graph"].values() if e != pe.UNRES)]}
            request = {"node_ids": proposal["nodes"], "action": proposal["action"], "target": proposal["target"]}
            selection = {"action": proposal["action"], "target_node": proposal["target"],
                         "target": entry["recommendations"][graph_hash]["target"],
                         "sd_y": entry["recommendations"][graph_hash]["scale"],
                         "selected_k": entry["recommendations"][graph_hash]["selected_k"],
                         "candidates": [{"k": k, "action": a} for k, a in zip((-1.,-.5,0.,.5,1.),
                             [float(np.mean(np.asarray(unit["observations"], dtype=np.float64)[:, proposal["nodes"].index(proposal["action"])])) + k * float(np.std(np.asarray(unit["observations"], dtype=np.float64)[:, proposal["nodes"].index(proposal["action"] )], ddof=1)) for k in (-1.,-.5,0.,.5,1.)])]}
            evaluated = evaluate(selection, truth, analytic_response)
            selected = next(row for row in evaluated["truth"] if row["k"] == selection["selected_k"])
            outcomes[graph_hash] = {"regret": float(evaluated["regret"]), "selected_k": selection["selected_k"],
                                    "selected_loss": float(selected["loss"]), "optimum_k": float(evaluated["optimum_k"]),
                                    "truth_rows": evaluated["truth"]}
        # Every policy maps to the same locked common graph-level evaluator table.
        for policy in entry["policies"]:
            result = outcomes[policy["graph_hash"]]
            policy_rows.append({**policy, "regret": result["regret"], "selected_k": result["selected_k"],
                                "optimum_k": result["optimum_k"], "action_changed_from_s0": None})
        policy_map = {(r["policy"], r["budget"]): r for r in policy_rows if r["scm_id"] == unit["scm_id"] and r["cohort"] == unit["cohort"]}
        s0 = next(r for r in policy_map.values() if r["policy"] == "S0" and r["budget"] == 0)
        for row in policy_map.values(): row["action_changed_from_s0"] = row["selected_k"] != s0["selected_k"]

        candidate_info = entry["diagnostics"]["feasible0"]
        g0_hash = pe.graph_hash(unit["initial_graph"])
        base = outcomes[g0_hash]
        context = (pe.state(proposal["topology_edges"]), proposal["action"], proposal["target"],
                   *s3.structural_sets(pe.state(proposal["topology_edges"]), proposal["action"], proposal["target"], unit["config"]))
        q0 = s3.q_metrics(unit["initial_graph"], context)
        initial_metrics = pe.metrics(pe.state(proposal["topology_edges"]), unit["initial_graph"], proposal["action"], proposal["target"], unit["config"])
        for edit, graph in candidate_info:
            key = pe.graph_hash(graph)
            q1 = s3.q_metrics(graph, context)
            row = {"cohort": unit["cohort"], "scm_id": unit["scm_id"], "kind": edit.kind,
                   "operation": edit.operation, "metric": edit.metric, "pair": json.dumps(edit.pair),
                   "graph_hash": key, "regret_gain": base["regret"] - outcomes[key]["regret"],
                   "action_changed": base["selected_k"] != outcomes[key]["selected_k"],
                   "M4_gain": s3.m4_gain(edit, pe.state(proposal["topology_edges"]), unit["initial_graph"],
                                           initial_metrics, proposal["action"], proposal["target"], unit["config"])}
            row.update({f"{metric}_gain": q1[metric] - q0[metric] for metric in s3.T})
            candidate_rows.append(row)
        # Distinct initially feasible edit pair interactions; outcomes are revealed only here.
        single_by_key = {json.loads(r["pair"]): r for r in candidate_rows if r["scm_id"] == unit["scm_id"] and r["cohort"] == unit["cohort"]}
        feasible_by_key = {edit.key: graph for edit, graph in candidate_info}
        for e1, e2 in itertools.combinations([x[0] for x in candidate_info], 2):
            pair_order = []
            for first, second in ((e1, e2), (e2, e1)):
                g1 = pe.apply(unit["initial_graph"], first)
                if not s3.direct_task_edit(second, pe.state(proposal["topology_edges"]), g1, proposal["action"], proposal["target"], unit["config"]):
                    continue
                g2 = pe.apply(g1, second)
                if pe.dag(g2): pair_order.append((first, second, pe.graph_hash(g2)))
            for first, second, joint_hash in pair_order:
                v1 = base["regret"] - outcomes[pe.graph_hash(feasible_by_key[first.key])]["regret"]
                v2 = base["regret"] - outcomes[pe.graph_hash(feasible_by_key[second.key])]["regret"]
                v12 = base["regret"] - outcomes[joint_hash]["regret"]
                interaction_rows.append({"cohort": unit["cohort"], "scm_id": unit["scm_id"],
                    "first": repr(first.key), "second": repr(second.key), "interaction": v12-v1-v2,
                    "v_first": v1, "v_second": v2, "v_joint": v12, "joint_graph_hash": joint_hash})
        seq_rows = []
        seq_rows.append((0, outcomes[g0_hash]["regret"], g0_hash))
        for edit, graph in candidate_info:
            h = pe.graph_hash(graph); seq_rows.append((1, outcomes[h]["regret"], h))
        for sequence in entry["diagnostics"]["sequences"]:
            h = pe.graph_hash(sequence["g2"]); seq_rows.append((2, outcomes[h]["regret"], h))
        optimum = min(seq_rows, key=lambda r:(r[1], r[0], r[2]))
        unit_rows.append({"cohort": unit["cohort"], "scm_id": unit["scm_id"],
                          "initial_m4_candidates": len(candidate_info), "n_feasible_two_edit_orders": len(entry["diagnostics"]["sequences"]),
                          "s0_regret": base["regret"], "m4_b2_regret": next(r["regret"] for r in policy_map.values() if r["policy"]=="M4" and r["budget"]==2),
                          "full_greedy_b2_regret": next(r["regret"] for r in policy_map.values() if r["policy"]=="FULL_GREEDY" and r["budget"]==2),
                          "expost_le2_regret": optimum[1], "expost_cost": optimum[0], "expost_graph_hash": optimum[2]})
    return unit_rows, candidate_rows, interaction_rows, policy_rows


def summarize(units, candidates, interactions, policies, cohorts, binding, provenance, started):
    aggregates = []
    policy_groups = {}
    for row in policies:
        policy_groups.setdefault((row["cohort"], row["policy"], row["budget"]), []).append(row)
    for (cohort, policy, budget), rows in sorted(policy_groups.items()):
        values = np.array([x["regret"] for x in rows], dtype=float)
        costs = np.array([x["cost"] for x in rows], dtype=float)
        aggregates.append({"cohort": cohort, "policy": policy, "budget": budget, "n_scm": len(rows),
                           "mean_regret": float(values.mean()), "median_regret": float(np.median(values)),
                           "sd_regret": float(values.std(ddof=1)) if len(values)>1 else None,
                           "mean_edit_cost": float(costs.mean()),
                           "action_change_rate": float(np.mean([x["action_changed_from_s0"] for x in rows]))})
    rng_results = []
    rng = np.random.default_rng(6419173299)
    for cohort in ("general", "opportunity_rich_diagnostic"):
        rows = [x for x in units if x["cohort"] == cohort]
        if not rows: continue
        ix = rng.integers(0, len(rows), size=(BOOT, len(rows)))
        for name, key in (("S0_minus_M4_B2", "s0_regret"), ("M4_B2_minus_FULL_GREEDY_B2", None),
                          ("M4_B2_minus_EXPOST_LE2", None)):
            if name == "S0_minus_M4_B2": d = np.array([r["s0_regret"]-r["m4_b2_regret"] for r in rows])
            elif name == "M4_B2_minus_FULL_GREEDY_B2": d = np.array([r["m4_b2_regret"]-r["full_greedy_b2_regret"] for r in rows])
            else: d = np.array([r["m4_b2_regret"]-r["expost_le2_regret"] for r in rows])
            boot = d[ix].mean(axis=1)
            rng_results.append({"cohort": cohort, "contrast": name, "n_scm": len(d), "mean_difference": float(d.mean()),
                                "ci95_low": float(np.quantile(boot,.025)), "ci95_high": float(np.quantile(boot,.975)),
                                "better_left_count": int(np.sum(d> TOL)), "worse_left_count": int(np.sum(d< -TOL)),
                                "tie_count": int(np.sum(np.abs(d)<=TOL)), "seed": 6419173299, "replicates": BOOT})
    return {"gate": "PILOT_EXECUTED" if all(x["retained"] == x["target"] for x in cohorts.values()) else "PILOT_EXECUTED_WITH_SHORTFALL",
            "classification": "exploratory_development_pilot", "new_scm": len(units),
            "new_g0_screening_draws": sum(x["g0_screening_draws"] for x in cohorts.values()),
            "new_g0_analysis_draws": len(units), "new_observation_rows": sum(x["observation_rows"] for x in units),
            "new_intervention_rows": 0, "cohorts": cohorts, "recommendation_binding": binding,
            "paired_bootstrap": rng_results, "policy_aggregates": aggregates,
            "candidate_rows_private": len(candidates), "interaction_rows_private": len(interactions),
            "source_provenance": provenance, "runtime_seconds": time.perf_counter()-started,
            "peak_process_rss_bytes_observed": provenance.get("max_rss_bytes"),
            "limitations": ["pilot is not confirmatory", "opportunity-rich cohort is structurally selected",
                            "one linear-Gaussian SCM family only", "no matched corruption variants",
                            "analytic intervention means; zero sampled intervention rows",
                            "post-hoc candidate and policy contrasts are pointwise/descriptive",
                            "Research D/S5 replay blocked because private unit-level artifacts are unavailable"]}


def main():
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    provenance = verify_lock(lock)
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite pilot output: {OUT}")
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    journal = OUT / "generation_journal_private.jsonl"
    units, attempts, cohort_meta = make_units(lock, started, journal)
    if not units:
        raise RuntimeError("no eligible pilot SCMs generated; no replacement permitted")
    write_json(OUT / "cohort_generation_summary.json", cohort_meta)
    # Keep private input bytes outside the public repository.
    private_inputs = []
    for u in units:
        row = {k: v for k, v in u.items() if k not in ("config", "initial_graph")}
        row["initial_graph"] = {"directed_edges": [list(e) for e in sorted(e for e in u["initial_graph"].values() if e != pe.UNRES)],
                                 "unresolved_pairs": [list(p) for p, e in sorted(u["initial_graph"].items()) if e == pe.UNRES]}
        private_inputs.append(row)
    write_json(OUT / "pilot_inputs_private.json", private_inputs)
    unit_states, binding, _ = recommendation_stage(units, started, OUT)
    # Recommendation manifest is immutable and verified immediately before evaluator access.
    unit_rows, candidate_rows, interaction_rows, policy_rows = evaluator_stage(unit_states, binding, OUT, started)
    write_json(OUT / "unit_results_private.json", unit_rows)
    write_json(OUT / "candidate_values_private.json", candidate_rows)
    write_json(OUT / "interaction_values_private.json", interaction_rows)
    write_json(OUT / "policy_results_private.json", policy_rows)
    write_csv(OUT / "public_policy_aggregates.csv", summarize(unit_rows, candidate_rows, interaction_rows, policy_rows,
             cohort_meta, binding, provenance, started)["policy_aggregates"])
    result = summarize(unit_rows, candidate_rows, interaction_rows, policy_rows, cohort_meta, binding, provenance, started)
    max_rss = process_rss_bytes()
    result["peak_process_rss_bytes_observed"] = max(max_rss, PEAK_RSS_BYTES)
    result["source_provenance"].update({"max_rss_bytes": result["peak_process_rss_bytes_observed"],
                                        "runtime_seconds": time.perf_counter()-started})
    final_provenance = verify_lock(lock)
    if final_provenance != provenance:
        raise ValueError("source, environment or Git identity changed during pilot")
    result["private_artifact_sha256"] = {
        path.name: sha_file(path) for path in sorted(OUT.iterdir()) if path.is_file()
    }
    write_json(OUT / "pilot_summary_private.json", result)
    write_json(OUT / "attempts_summary.json", {"rows": len(attempts), "cohorts": cohort_meta,
                                               "proposal_attempts": sum(x["screening_attempts"] for x in cohort_meta.values())})
    write_json(OUT / "pilot_artifact_manifest.json", {
        "run_id": lock["run_id"], "git_commit": provenance["git_commit"],
        "git_tree": provenance["git_tree"], "execution_source_commit": provenance["execution_source_commit"],
        "execution_source_tree": provenance["execution_source_tree"],
        "files_sha256": {path.name: sha_file(path) for path in sorted(OUT.iterdir()) if path.is_file()
                         and path.name != "pilot_artifact_manifest.json"},
        "recommendation_manifest_sha256": binding["recommendation_manifest_sha256"],
        "new_scm": len(units), "new_g0_screening_draws": result["new_g0_screening_draws"],
        "new_observation_rows": result["new_observation_rows"], "new_intervention_rows": 0})
    print(json.dumps({k:v for k,v in result.items() if k not in ("policy_aggregates", "paired_bootstrap")}, indent=2))


if __name__ == "__main__":
    main()
