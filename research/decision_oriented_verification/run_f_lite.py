"""Run F-Lite against restored Research C inputs; never writes to C ledgers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import csv
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from research.budget_aware_refinement.step3_adapter import prepare, evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.budget_aware_refinement.step4c1_scm import generate_scm_parameters, generate_observations
from research.original_objective import policy_engine as pe
from integrated_pilot import fit_model
from decision_mvp import static_mean_response
from research.decision_oriented_verification.policy import (
    NO_EDGE, UNRESOLVED, U_TO_V, V_TO_U, VerificationState, query_once,
)

DATA_ROOT = Path(os.environ.get("DAT_RESEARCH_ROOT", "C:/DAT_RESEARCH"))
PRIVATE_ROOT = Path(os.environ.get("DAT_RESEARCH_F_LITE_ROOT", str(DATA_ROOT / "research-f-lite/v1")))
EXPECTED = {
    "C_DEVELOPMENT:cohort": "dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716",
    "C_DEVELOPMENT:proposal": "1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584",
    "C_HELDOUT:cohort": "37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba",
    "C_HELDOUT:proposal": "59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6",
}
SOURCES = [
    ("C_DEVELOPMENT", "development",
     DATA_ROOT / "research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite",
     DATA_ROOT / "research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite"),
    ("C_HELDOUT", "confirmation",
     DATA_ROOT / "research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite",
     DATA_ROOT / "research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite"),
]
DETERMINISTIC = ("FIT_BASED_VERIFICATION", "SUSPICION_ONLY", "DECISION_IMPACT_ONLY", "DECISION_WEIGHTED_VERIFICATION")
RANDOM_REPEATS = 32
EXECUTION_LOCK = ROOT / "research/decision_oriented_verification/execution_lock.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_execution_lock() -> dict:
    lock = json.loads(EXECUTION_LOCK.read_text(encoding="utf-8"))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", f"{lock['code_commit']}^{{tree}}"], cwd=ROOT, text=True).strip()
    if tree != lock["code_tree"]:
        raise ValueError("execution lock's code tree is inconsistent")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", lock["code_commit"], head], cwd=ROOT)
    if ancestor.returncode != 0:
        raise ValueError("locked code commit is not an ancestor of current HEAD")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != "research/research-f-lite-verification":
        raise ValueError("unexpected execution branch")
    for path, expected in lock["runtime_files"].items():
        local = ROOT / path
        if sha256_file(local) != expected["raw_sha256"]:
            raise ValueError(f"runtime bytes changed after lock: {path}")
        blob = subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip()
        if blob != expected["git_blob"]:
            raise ValueError(f"Git blob changed after lock: {path}")
    return lock


def stable_seed(*parts) -> int:
    raw = "research-f-lite-v1|" + "|".join(str(x) for x in parts)
    return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")


def read_only(path: Path):
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError(f"SQLite integrity check failed: {path.name}")
    return con


def _config(payload):
    cfg = dict(payload["config"]["repair_config"])
    for k in ("costs", "beta", "weights", "route_relevant_fp"):
        if k in cfg:
            cfg[k] = tuple(tuple(x) for x in cfg[k]) if k in ("costs", "route_relevant_fp") else tuple(cfg[k])
    return pe.Config(**cfg)


def restore_cohort(source):
    cohort, proposal_cohort, cohort_path, proposal_path = source
    got = {f"{cohort}:cohort": sha256_file(cohort_path), f"{cohort}:proposal": sha256_file(proposal_path)}
    if any(got[k] != EXPECTED[k] for k in got):
        raise ValueError(f"input DB hash mismatch: {got}")
    con, pcon = read_only(cohort_path), read_only(proposal_path)
    prop_by_scm = {}
    for (raw,) in pcon.execute("SELECT proposal_json FROM proposal_attempts WHERE status='ELIGIBLE'"):
        prop = json.loads(raw)
        prop_by_scm[prop["scm_id"]] = prop
    records = []
    rows = list(con.execute("SELECT scm_id,status,result_json FROM scms ORDER BY ordinal"))
    for scm_id, status, raw in rows:
        if status != "COMPLETED" or scm_id not in prop_by_scm:
            raise ValueError(f"incomplete or unmatched source unit: {cohort} {scm_id} {status}")
        payload = json.loads(raw)["payload"]
        prop = prop_by_scm[scm_id]
        scm = generate_scm_parameters(prop)
        obs = generate_observations(prop, scm)
        binding = payload["input_binding"]
        if scm["equation_signature_sha256"] != binding["truth_spec_sha256"]:
            raise ValueError(f"truth specification mismatch: {scm_id}")
        if obs["data_sha256"] != binding["observations_sha256"]:
            raise ValueError(f"observation digest mismatch: {scm_id}")
        if (prop["action"], prop["target"], list(prop["nodes"])) != (binding["action"], binding["target"], binding["nodes"]):
            raise ValueError(f"task/schema mismatch: {scm_id}")
        truth = pe.state([tuple(e) for e in scm["truth_spec"]["edges"]])
        gj = payload["g0_generation"]["initial_graph"]
        initial = pe.state([tuple(e) for e in gj["edges"]], unresolved=[tuple(e) for e in gj["unresolved"]])
        g0_hash = pe.graph_hash(initial)
        if g0_hash != binding["initial_structural_graph_sha256"]:
            raise ValueError(f"G0 hash mismatch: {scm_id}")
        b0 = next(x for x in payload["e2e_result"]["budgets"][0]["policies"] if x["policy_id"] == "S0")
        if b0["final_graph_sha256"] != g0_hash or b0["evaluation_status"] != "RESEARCH_OK":
            raise ValueError(f"historical B0 binding mismatch: {scm_id}")
        data = np.asarray(obs["rows"], dtype=np.float64)
        # Historical S0 B0 replay is source validation; no historical response is passed to a policy.
        request = {"node_ids": prop["nodes"], "action": prop["action"], "target": prop["target"]}
        delta = int(binding["delta"])
        rr = {"final_graph": [list(e) for e in initial.values() if isinstance(e, tuple)]}
        _, selection = prepare(request, data, prop["nodes"], prop["nodes"], delta,
                               fit_model, static_mean_response, graph_result=rr)
        old_action = float(b0["evaluation"]["selected_action"])
        new_action = float(next(x["action"] for x in selection["candidates"] if x["k"] == selection["selected_k"]))
        if new_action != old_action:
            raise ValueError(f"historical B0 S0 action mismatch: {scm_id}")
        y_index = prop["nodes"].index(prop["target"])
        expected_target = float(data[:, y_index].mean() + delta * data[:, y_index].std(ddof=1))
        if abs(float(selection["target"]) - expected_target) > 1e-12 or list(binding["action_candidates"]) != [-1.0, -0.5, 0.0, 0.5, 1.0]:
            raise ValueError(f"target/action-grid binding mismatch: {scm_id}")
        old_losses = b0["evaluation"]["predicted_losses"]
        for candidate in selection["candidates"]:
            if abs(float(old_losses[str(candidate["k"])]) - float(candidate["predicted_loss"])) > 1e-12:
                raise ValueError(f"historical B0 S0 predicted loss mismatch: {scm_id}")
        if abs(float(selection["sd_y"]) - float(data[:, y_index].std(ddof=1))) > 1e-12:
            raise ValueError(f"training scale binding mismatch: {scm_id}")
        check = evaluate(selection, scm["truth_spec"], analytic_response)
        if abs(float(check["regret"]) - float(b0["evaluation"]["regret"])) >= 1e-12:
            raise ValueError(f"historical B0 S0 regret mismatch: {scm_id}")
        means = data.mean(axis=0); sd = data.std(axis=0, ddof=1)
        actions = [float(means[prop["nodes"].index(prop["action"])] + k * sd[prop["nodes"].index(prop["action"])])
                   for k in (-1., -.5, 0., .5, 1.)]
        target_value = float(means[prop["nodes"].index(prop["target"])] + delta * sd[prop["nodes"].index(prop["target"])])
        records.append({"cohort": cohort, "scm_id": scm_id, "nodes": tuple(prop["nodes"]), "data": data,
                        "initial": {p: (UNRESOLVED if r == pe.UNRES else r) for p, r in initial.items()},
                        "truth": truth, "truth_spec": scm["truth_spec"], "action": prop["action"], "target": prop["target"],
                        "actions": tuple(actions), "target_value": target_value, "scale": float(sd[prop["nodes"].index(prop["target"])]),
                        "delta": delta, "config": _config(payload), "g0_hash": g0_hash,
                        "truth_digest": binding["truth_spec_sha256"], "observations_digest": binding["observations_sha256"],
                        "historical_b0_action": old_action, "historical_b0_regret": float(b0["evaluation"]["regret"]),
                        "payload": payload})
    con.close(); pcon.close()
    expected_n = 64 if cohort == "C_DEVELOPMENT" else 200
    if len(records) != expected_n or len({r["scm_id"] for r in records}) != expected_n:
        raise ValueError(f"cohort completeness failure: {cohort} {len(records)}")
    return records, got


def _relation_from_truth(truth, p):
    value = truth.get(p)
    if value is None:
        return NO_EDGE
    return U_TO_V if value == p else V_TO_U


def _selection(record, relations):
    rr = {"final_graph": [list(e) for e in relations.values() if isinstance(e, tuple)]}
    req = {"node_ids": list(record["nodes"]), "action": record["action"], "target": record["target"]}
    return prepare(req, record["data"], list(record["nodes"]), list(record["nodes"]), record["delta"],
                   fit_model, static_mean_response, graph_result=rr)[1]


def make_policy_view(record):
    """Explicit allow-list; never copy an experiment payload into a policy call."""
    allowed = ("cohort", "scm_id", "nodes", "data", "initial", "action", "target",
               "actions", "target_value", "scale", "delta")
    view = {k: record[k] for k in allowed}
    if set(view) != set(allowed):
        raise ValueError("policy input allow-list mismatch")
    return view


def _recommend(record, policy, expert):
    rng_repeats = range(RANDOM_REPEATS) if policy == "RANDOM_VERIFICATION" else range(1)
    out = []
    score_cache = {}
    for repeat in rng_repeats:
        st = VerificationState(record["nodes"], dict(record["initial"]))
        rng = np.random.default_rng(stable_seed(record["cohort"], record["scm_id"], policy, repeat)) if policy == "RANDOM_VERIFICATION" else None
        context = {"data": record["data"], "nodes": record["nodes"], "action": record["action"],
                   "target": record["target"], "action_values": record["actions"], "target_value": record["target_value"],
                   "scale": record["scale"], "fit_model": fit_model, "response": static_mean_response,
                   "model_cache": score_cache}
        recs = []
        initial_errors = None
        for b in range(5):
            if b:
                query_once(st, policy, b, expert, score_context=context, rng=rng)
            selection = _selection(record, st.relations)
            recs.append({"cohort": record["cohort"], "scm_id": record["scm_id"], "policy": policy,
                         "repeat": repeat, "budget": b, "query_count": st.query_count, "edit_count": st.edits,
                         "relations": dict(st.relations), "pending": dict(st.pending), "query_history": list(st.history),
                         "selection": selection})
        out.extend(recs)
    return out


def run_recommendations(records, cohort_name, outpath):
    # F policies get sanitized fields through _recommend; evaluator fields remain in source records.
    policies = ["S0", *DETERMINISTIC, "RANDOM_VERIFICATION"]
    all_recs = []
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("psutil is required for the approved process RSS resource guard") from exc
    process = psutil.Process()
    started = time.perf_counter(); peak_rss = process.memory_info().rss
    for i, rec in enumerate(records, 1):
        view = make_policy_view(rec)
        for policy in policies:
            if policy == "S0":
                selection = _selection(view, view["initial"])
                all_recs.extend({"cohort": rec["cohort"], "scm_id": rec["scm_id"], "policy": policy,
                                 "repeat": 0, "budget": b, "query_count": 0, "edit_count": 0,
                                 "relations": dict(rec["initial"]), "pending": {}, "query_history": [], "selection": selection}
                                for b in range(5))
            else:
                # The coordinator owns the private reference and exposes a single-pair response function.
                expert = lambda p, _truth=rec["truth"]: _relation_from_truth(_truth, p)
                all_recs.extend(_recommend(view, policy, expert))
        peak_rss = max(peak_rss, process.memory_info().rss)
        if i % 8 == 0:
            print(f"recommendations {cohort_name}: {i}/{len(records)} SCM; {time.perf_counter()-started:.1f}s", flush=True)
        if time.perf_counter() - started > (7200 if cohort_name == "C_DEVELOPMENT" else 10800):
            raise TimeoutError(f"recommendation resource wall limit exceeded for {cohort_name}")
        if peak_rss > 4 * 1024**3:
            raise MemoryError(f"recommendation RSS cap exceeded for {cohort_name}")
    # Oracle-assisted M4 is copied from the already completed, frozen C ledger; it is not a query policy.
    for rec in records:
        for b in range(5):
            old = next(x for x in rec["payload"]["e2e_result"]["budgets"][b]["policies"] if x["policy_id"] == "M4")
            selection = {"action": rec["action"], "target_node": rec["target"], "target": rec["target_value"],
                         "sd_y": rec["scale"], "selected_k": float(old["evaluation"]["selected_k"]),
                         "candidates": [{"k": float(k), "action": float(a), "predicted_loss": float(v)}
                                        for k, a, v in zip((-1., -.5, 0., .5, 1.), rec["actions"],
                                                           [float(old["evaluation"]["predicted_losses"][str(k)]) for k in (-1., -.5, 0., .5, 1.)])]}
            all_recs.append({"cohort": rec["cohort"], "scm_id": rec["scm_id"], "policy": "ORACLE_ASSISTED_M4_DIAGNOSTIC",
                             "repeat": 0, "budget": b, "query_count": None, "edit_count": int(old["total_edit_cost"]),
                             "relations": None, "pending": {}, "query_history": [], "selection": selection})
        # New graph-free association diagnostic: one directed X->Y modeling edge.
        gfree = {(rec["action"], rec["target"]): (rec["action"], rec["target"])}
        selection = _selection(view, gfree)
        for b in range(5):
            all_recs.append({"cohort": rec["cohort"], "scm_id": rec["scm_id"], "policy": "GRAPH_FREE_ASSOCIATION_DIAGNOSTIC",
                             "repeat": 0, "budget": b, "query_count": 0, "edit_count": 0,
                             "relations": gfree, "pending": {}, "query_history": [], "selection": selection})
    by_scm = {r["scm_id"]: r for r in records}
    expected_n = len(records) * 195
    if len(all_recs) != expected_n:
        raise ValueError(f"recommendation key count mismatch: {len(all_recs)} != {expected_n}")
    keys = [(r["scm_id"], r["policy"], r["repeat"], r["budget"]) for r in all_recs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate recommendation key")
    for row in all_recs:
        if len(row["selection"]["candidates"]) != 5:
            raise ValueError("action candidate grid is incomplete")
        if row["query_count"] is not None and (row["query_count"] > row["budget"] or row["query_count"] != len(row["query_history"])):
            raise ValueError("query budget/history mismatch")
        seen = [tuple(q["pair"]) for q in row["query_history"]]
        if len(seen) != len(set(seen)):
            raise ValueError("duplicate queried pair")
        if row["relations"] is not None and not __import__("research.decision_oriented_verification.policy", fromlist=["graph_dag"]).graph_dag(by_scm[row["scm_id"]]["nodes"], row["relations"]):
            raise ValueError("recommendation graph is cyclic")
    # Public-facing lock contains recommendation content digest; raw records stay external.
    serial = [{k: v for k, v in r.items() if k not in ("relations", "pending", "query_history", "selection")} |
              {"action": float(next(x["action"] for x in r["selection"]["candidates"] if x["k"] == r["selection"]["selected_k"])),
               "selected_k": float(r["selection"]["selected_k"]),
               "predicted_losses": [float(x["predicted_loss"]) for x in r["selection"]["candidates"]]}
              for r in all_recs]
    canonical = json.dumps(serial, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    lock = {"cohort": cohort_name, "recommendation_count_including_repeats_and_diagnostics": len(serial),
            "recommendation_sha256": hashlib.sha256(canonical).hexdigest(), "raw_detail_sha256": hashlib.sha256(
                json.dumps([{**x, "relations": repr(x["relations"]), "pending": repr(x["pending"]), "query_history": repr(x["query_history"]), "selection": x["selection"]}
                            for x in all_recs], sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest(),
            "wall_seconds": time.perf_counter()-started, "peak_process_rss_bytes_observed": peak_rss}
    outpath.parent.mkdir(parents=True, exist_ok=True)
    if outpath.exists():
        raise FileExistsError(f"refusing to overwrite existing recommendation artifact: {outpath.name}")
    tmp = outpath.with_suffix(outpath.suffix + ".tmp")
    tmp.write_text(json.dumps({"lock": lock, "records": serial}, separators=(",", ":")), encoding="utf-8")
    tmp.replace(outpath)
    return all_recs, lock


def evaluate_locked(records, recommendations, recommendation_lock, recommendation_path, output_path):
    # Binding check occurs before any new analytic evaluator call.
    saved = json.loads(recommendation_path.read_text(encoding="utf-8"))
    if saved.get("lock") != recommendation_lock:
        raise ValueError("recommendation lock file differs; evaluator is not entered")
    saved_records = saved.get("records")
    saved_digest = hashlib.sha256(json.dumps(saved_records, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if saved_digest != recommendation_lock["recommendation_sha256"]:
        raise ValueError("recommendation manifest digest mismatch; evaluator is not entered")
    rows_for_hash = [{k: v for k, v in r.items() if k not in ("relations", "pending", "query_history", "selection")} |
                     {"action": float(next(x["action"] for x in r["selection"]["candidates"] if x["k"] == r["selection"]["selected_k"])),
                      "selected_k": float(r["selection"]["selected_k"]),
                      "predicted_losses": [float(x["predicted_loss"]) for x in r["selection"]["candidates"]]}
                     for r in recommendations]
    digest = hashlib.sha256(json.dumps(rows_for_hash, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if digest != recommendation_lock["recommendation_sha256"] or rows_for_hash != saved_records:
        raise ValueError("recommendation lock mismatch; evaluator is not entered")
    by_id = {r["scm_id"]: r for r in records}
    # Audit the one-pair expert API only after the recommendation lock is fixed.
    for row in recommendations:
        if row["policy"] in {"ORACLE_ASSISTED_M4_DIAGNOSTIC", "GRAPH_FREE_ASSOCIATION_DIAGNOSTIC", "S0"}:
            continue
        truth = by_id[row["scm_id"]]["truth"]
        for q in row["query_history"]:
            if _relation_from_truth(truth, tuple(q["pair"])) != q["answer"]:
                raise ValueError("simulated perfect expert response mismatch")
    evaluated = []
    for row in recommendations:
        rec = by_id[row["scm_id"]]
        if row["policy"] in {"ORACLE_ASSISTED_M4_DIAGNOSTIC"}:
            # Use the historical frozen evaluator result; no re-run needed.
            old = next(x for x in rec["payload"]["e2e_result"]["budgets"][row["budget"]]["policies"] if x["policy_id"] == "M4")
            regret = float(old["evaluation"]["regret"])
            errors = sum(sum(v.values()) for v in old["final_error_counts"].values())
            gt_rows = old["evaluation"]["truth"]
            selected_loss = float(old["evaluation"]["gt_selected_loss"])
            best_loss = float(old["evaluation"]["gt_best_loss"])
        else:
            result = evaluate(row["selection"], rec["truth_spec"], analytic_response)
            regret = float(result["regret"])
            gt_rows = result["truth"]
            selected_loss = float(next(x["loss"] for x in gt_rows if x["k"] == row["selection"]["selected_k"]))
            best_loss = float(min(x["loss"] for x in gt_rows))
            errors = None
            if row["relations"] is not None:
                state = {p: (pe.UNRES if r == UNRESOLVED else r) for p, r in row["relations"].items()}
                errors = sum(sum(v.values()) for v in pe.metrics(rec["truth"], state, rec["action"], rec["target"], rec["config"])["counts"].values())
        evaluated.append({"cohort": row["cohort"], "scm_id": row["scm_id"], "policy": row["policy"],
                          "repeat": row["repeat"], "budget": row["budget"], "query_count": row["query_count"],
                          "edit_count": row["edit_count"], "action": float(next(x["action"] for x in row["selection"]["candidates"] if x["k"] == row["selection"]["selected_k"])),
                          "selected_k": float(row["selection"]["selected_k"]), "regret": regret, "selected_loss": selected_loss,
                          "best_grid_loss": best_loss, "gt_loss_vector": [{"k": float(x["k"]), "loss": float(x["loss"])} for x in gt_rows],
                          "remaining_errors": errors,
                          "pending_count": len(row["pending"]), "query_history": row["query_history"],
                          "final_relations": repr(row["relations"])})
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite evaluator artifact: {output_path.name}")
    output_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in evaluated), encoding="utf-8")
    return evaluated


def aggregate_cohort(evaluated, cohort, out_dir):
    """Summarize repeats within SCM before any cohort-level inference."""
    import statistics
    from collections import defaultdict
    units = defaultdict(list)
    for r in evaluated:
        if r["cohort"] == cohort:
            units[(r["policy"], r["scm_id"], r["budget"])].append(r)
    collapsed = []
    for (policy, scm_id, budget), rows in sorted(units.items()):
        collapsed.append({"cohort": cohort, "policy": policy, "scm_id": scm_id, "budget": budget,
                          "regret": float(np.mean([x["regret"] for x in rows])),
                          "query_count": None if rows[0]["query_count"] is None else float(np.mean([x["query_count"] for x in rows])),
                          "edit_count": float(np.mean([x["edit_count"] for x in rows])),
                          "remaining_errors": None if rows[0]["remaining_errors"] is None else float(np.mean([x["remaining_errors"] for x in rows])),
                          "action_change": None, "random_repeats": len(rows),
                          "discovered_error_pairs": float(np.mean([sum(bool(q["error_discovered_at_query"]) for q in x["query_history"]) for x in rows]))})
    baseline = {(x["scm_id"], x["budget"]): x["regret"] for x in collapsed if x["policy"] == "S0"}
    for x in collapsed:
        x["action_change"] = None if x["policy"] == "S0" else float(any(
            r["scm_id"] == x["scm_id"] and r["budget"] == x["budget"] and r["policy"] == x["policy"] and r["action"] !=
            next(s["action"] for s in evaluated if s["cohort"] == cohort and s["scm_id"] == x["scm_id"] and s["policy"] == "S0" and s["budget"] == x["budget"])
            for r in evaluated if r["cohort"] == cohort and r["scm_id"] == x["scm_id"] and r["policy"] == x["policy"] and r["budget"] == x["budget"]))
    groups = defaultdict(list)
    for x in collapsed:
        groups[(x["policy"], x["budget"])].append(x)
    aggregates = []
    for (policy, budget), rows in sorted(groups.items()):
        vals = np.asarray([x["regret"] for x in rows], dtype=float)
        for metric in ("query_count", "edit_count", "remaining_errors", "discovered_error_pairs", "action_change"):
            mv = [x[metric] for x in rows if x[metric] is not None]
            value = float(np.mean(mv)) if mv else None
            if metric == "query_count": qmean = value
            elif metric == "edit_count": emean = value
            elif metric == "remaining_errors": remmean = value
            elif metric == "discovered_error_pairs": dmean = value
            elif metric == "action_change": chmean = value
        aggregates.append({"cohort": cohort, "policy": policy, "budget": budget, "n_scm": len(rows),
                           "mean_regret": float(vals.mean()), "median_regret": float(np.median(vals)),
                           "sd_regret": float(vals.std(ddof=1)) if len(vals)>1 else 0.0,
                           "q25_regret": float(np.quantile(vals,.25)), "q75_regret": float(np.quantile(vals,.75)),
                           "mean_query_count": qmean, "mean_edit_count": emean,
                           "mean_remaining_errors": remmean, "mean_discovered_error_pairs": dmean,
                           "action_change_rate": chmean})
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / f"{cohort.lower()}_aggregate.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(aggregates[0]));w.writeheader();w.writerows(aggregates)
    contrasts = []
    policy_by_key = {(x["policy"],x["scm_id"],x["budget"]):x for x in collapsed}
    rng = np.random.default_rng(stable_seed(cohort,"paired-bootstrap"))
    for comp in ("RANDOM_VERIFICATION", *DETERMINISTIC):
        diffs = np.asarray([policy_by_key[(comp,s,4)]["regret"] - policy_by_key[("DECISION_WEIGHTED_VERIFICATION",s,4)]["regret"]
                            for s in sorted({x["scm_id"] for x in collapsed if x["policy"]==comp and x["budget"]==4})], dtype=float)
        boots=np.empty(10000,dtype=float)
        for j in range(10000):
            boots[j]=float(np.mean(diffs[rng.integers(0,len(diffs),size=len(diffs))]))
        contrasts.append({"cohort":cohort,"comparator":comp,"proposed":"DECISION_WEIGHTED_VERIFICATION","budget":4,
                          "n_scm":len(diffs),"mean_comparator_minus_proposed":float(diffs.mean()),
                          "median_difference":float(np.median(diffs)),"ci95_low":float(np.quantile(boots,.025)),
                          "ci95_high":float(np.quantile(boots,.975)),"better":int((diffs<0).sum()),
                          "worse":int((diffs>0).sum()),"tie":int((diffs==0).sum()),
                          "bootstrap_replicates":10000,"seed":stable_seed(cohort,"paired-bootstrap")})
    (out_dir / f"{cohort.lower()}_paired_contrasts.json").write_text(json.dumps(contrasts,indent=2),encoding="utf-8")
    return aggregates, contrasts


def main():
    lock = verify_execution_lock()
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True)
    all_public = {"status": "RUNNING", "inputs": {}, "cohorts": {}}
    for source in SOURCES:
        cohort, _, cp, pp = source
        records, hashes = restore_cohort(source)
        all_public["inputs"].update(hashes)
        rec_path = PRIVATE_ROOT / f"{cohort.lower()}_recommendations.json"
        eval_path = PRIVATE_ROOT / f"{cohort.lower()}_evaluator_results.jsonl"
        if rec_path.exists() or eval_path.exists():
            raise FileExistsError(f"F-Lite output exists; refusing overwrite for {cohort}")
        reco, lock = run_recommendations(records, cohort, rec_path)
        evaluated = evaluate_locked(records, reco, lock, rec_path, eval_path)
        agg, contrasts = aggregate_cohort(evaluated, cohort, ROOT / "research/decision_oriented_verification/outputs")
        all_public["cohorts"][cohort] = {"n_scm": len(records), "recommendation_lock": lock,
                                         "evaluator_results_sha256": sha256_file(eval_path),
                                         "evaluator_rows": len(evaluated), "recommendation_path_external": True,
                                         "aggregate_rows": len(agg), "paired_contrasts": contrasts}
    all_public["status"] = "COMPLETED"
    verify_execution_lock()
    all_public["execution_lock_sha256"] = sha256_file(EXECUTION_LOCK)
    all_public["code_commit"] = lock["code_commit"]
    all_public["code_tree"] = lock["code_tree"]
    (ROOT / "research/decision_oriented_verification/run_summary_private_redacted.json").write_text(json.dumps(all_public, indent=2), encoding="utf-8")
    print(json.dumps(all_public, indent=2))


if __name__ == "__main__":
    main()
